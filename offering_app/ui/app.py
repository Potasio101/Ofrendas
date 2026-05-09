from datetime import datetime
from decimal import Decimal
import json
import logging
import os
from pathlib import Path
import time
from zoneinfo import ZoneInfo

from flask import Flask, jsonify, redirect, render_template_string, request, url_for, g
from werkzeug.utils import secure_filename

from offering_app.repositories.postgresql_repo import PostgreSQLRepo
from offering_app.services.cash_window_service import CashWindowService
from offering_app.services.offering_service import OfferingService
from offering_app.services.outputs_service import OutputsService


ROLE_POLICY = {
    "home": {"treasurer", "admin", "auditor"},
    "process_image": {"treasurer", "admin"},
    "confirm": {"treasurer", "admin"},
    "summary": {"treasurer", "admin", "auditor"},
    "day_log": {"treasurer", "admin", "auditor"},
    "review_existing": {"treasurer", "admin", "auditor"},
    "save_review": {"treasurer", "admin"},
    "admin_config": {"admin"},
    "cash_window_open": {"treasurer", "admin"},
    "cash_window_get": {"treasurer", "admin", "auditor"},
    "cash_window_line": {"treasurer", "admin"},
    "cash_window_close": {"treasurer", "admin"},
    "cash_window_reopen": {"admin"},
    "outputs_create_draft": {"treasurer", "admin"},
    "outputs_list_drafts": {"treasurer", "admin", "auditor"},
    "outputs_update_draft": {"treasurer", "admin"},
    "outputs_submit": {"treasurer", "admin"},
    "outputs_approve": {"admin"},
    "outputs_pay": {"admin"},
}

KNOWN_ROLES = {"treasurer", "admin", "auditor"}


def create_app(
    service: OfferingService,
    storage: PostgreSQLRepo,
    upload_path: str,
    cash_window_service: CashWindowService | None = None,
    outputs_service: OutputsService | None = None,
) -> Flask:
    app = Flask(__name__)
    app.config["UPLOAD_PATH"] = upload_path
    app.config["APP_TIMEZONE"] = os.getenv("APP_TIMEZONE", "UTC")
    app.config["APP_DEFAULT_ROLE"] = os.getenv("APP_DEFAULT_ROLE", "treasurer")
    app.config["APP_DEFAULT_USER_ID"] = os.getenv("APP_DEFAULT_USER_ID", "local-dev-user")
    app.config["APP_AUTH_MODE"] = os.getenv("APP_AUTH_MODE", "local-dev")
    _configure_logging(app)

    cash_window_service = cash_window_service or CashWindowService(storage)
    outputs_service = outputs_service or OutputsService(storage)

    @app.before_request
    def before_request():
        g._request_started_at = time.time()
        g.auth_error = None
        auth_mode = (app.config.get("APP_AUTH_MODE") or "local-dev").strip().lower()
        header_role = (request.headers.get("X-User-Role") or "").strip().lower()
        header_user_id = (request.headers.get("X-User-Id") or "").strip()

        if auth_mode == "header-strict":
            g.auth_role = header_role
            g.auth_user_id = header_user_id
            if not header_role or not header_user_id:
                g.auth_error = "missing_identity"
            elif header_role not in KNOWN_ROLES:
                g.auth_error = "invalid_role"
        else:
            role = header_role or (app.config.get("APP_DEFAULT_ROLE") or "treasurer").strip().lower()
            user_id = header_user_id or request.form.get("actor_user_id") or app.config.get("APP_DEFAULT_USER_ID")
            g.auth_role = role
            g.auth_user_id = user_id

    def _require_authentication():
        auth_error = getattr(g, "auth_error", None)
        if not auth_error:
            return None
        app.logger.info(
            json.dumps(
                {
                    "event": "authn_denied",
                    "reason": auth_error,
                    "auth_mode": app.config.get("APP_AUTH_MODE"),
                    "path": request.path,
                    "method": request.method,
                },
                ensure_ascii=True,
            )
        )
        return "Unauthorized", 401

    def _current_service_date() -> str:
        tz_name = (app.config.get("APP_TIMEZONE") or "UTC").strip() or "UTC"
        if hasattr(storage, "get_current_service_date"):
            try:
                return storage.get_current_service_date(tz_name)
            except Exception:
                app.logger.info(
                    json.dumps(
                        {
                            "event": "service_date_fallback",
                            "source": "python",
                            "timezone": tz_name,
                        },
                        ensure_ascii=True,
                    )
                )
        try:
            tz = ZoneInfo(tz_name)
        except Exception:
            tz = ZoneInfo("UTC")
        return datetime.now(tz).date().isoformat()

    def _require_policy(policy_key: str):
        unauth = _require_authentication()
        if unauth:
            return unauth
        allowed_roles = ROLE_POLICY.get(policy_key, set())
        role = getattr(g, "auth_role", "")
        if role not in allowed_roles:
            app.logger.info(
                json.dumps(
                    {
                        "event": "authz_denied",
                        "policy": policy_key,
                        "allowed_roles": sorted(allowed_roles),
                        "auth_role": role,
                        "auth_user_id": getattr(g, "auth_user_id", None),
                        "path": request.path,
                        "method": request.method,
                    },
                    ensure_ascii=True,
                )
            )
            return "Forbidden", 403
        return None

    def _domain_error_response(exc: Exception):
        message = str(exc)
        if "not_found" in message:
            return "Not found", 404
        if "invalid_transition" in message or "closed" in message:
            return "Conflict", 409
        if "invalid_" in message:
            return "Invalid payload", 400
        app.logger.info(
            json.dumps(
                {
                    "event": "unexpected_domain_error",
                    "message": message,
                    "path": request.path,
                    "method": request.method,
                },
                ensure_ascii=True,
            )
        )
        return "Internal error", 500

    def _json_safe(value):
        if isinstance(value, dict):
            return {k: _json_safe(v) for k, v in value.items()}
        if isinstance(value, list):
            return [_json_safe(v) for v in value]
        if isinstance(value, Decimal):
            return float(value)
        if hasattr(value, "isoformat") and callable(value.isoformat):
            return value.isoformat()
        return value

    @app.after_request
    def after_request(response):
        started = getattr(g, "_request_started_at", time.time())
        latency_ms = round((time.time() - started) * 1000, 2)
        app.logger.info(
            json.dumps(
                {
                    "event": "http_request",
                    "method": request.method,
                    "path": request.path,
                    "status": response.status_code,
                    "latency_ms": latency_ms,
                    "remote_addr": request.remote_addr,
                },
                ensure_ascii=True,
            )
        )
        return response

    @app.get("/healthz")
    def healthz():
        return jsonify({"status": "ok"})

    @app.get("/readyz")
    def readyz():
        try:
            storage.get_daily_totals(_current_service_date())
            return jsonify({"status": "ready"})
        except Exception as exc:
            return jsonify({"status": "not-ready", "error": str(exc)}), 503

    @app.get("/")
    def home():
        denied = _require_policy("home")
        if denied:
            return denied
        summary = service.get_daily_summary(_current_service_date())
        return render_template_string(
            """
            <h1>Ofrendas</h1>
            <p>Sobres hoy: {{ summary.envelopes }}</p>
            <p>Total hoy: {{ summary.total }}</p>
            <form action="/process" method="post" enctype="multipart/form-data">
              <input type="file" name="image" required>
              <button type="submit">Nuevo Sobre</button>
            </form>
            <p><a href="/day-log">Day Log</a> | <a href="/summary">Resumen</a></p>
            """,
            summary=summary,
        )

    @app.post("/process")
    def process_image():
        denied = _require_policy("process_image")
        if denied:
            return denied
        file = request.files.get("image")
        if not file or file.filename == "":
            return "Image is required", 400

        safe_name = secure_filename(file.filename)
        target = Path(app.config["UPLOAD_PATH"]) / safe_name
        target.parent.mkdir(parents=True, exist_ok=True)
        file.save(target)

        data = service.process_image(str(target))
        data["service_date"] = _current_service_date()
        return render_template_string(
            _review_template(),
            data=data,
            action=url_for("confirm"),
            title="Revisar Captura",
            offering_id="",
        )

    @app.post("/confirm")
    def confirm():
        denied = _require_policy("confirm")
        if denied:
            return denied
        actor = getattr(g, "auth_user_id", None)
        offering = service.build_offering_from_form(request.form, actor)
        corrections = service.build_corrections_from_form(request.form)
        offering_id = service.confirm(offering, corrections)
        return redirect(url_for("review_existing", offering_id=offering_id))

    @app.get("/summary")
    def summary():
        denied = _require_policy("summary")
        if denied:
            return denied
        data = service.get_daily_summary(_current_service_date())
        return render_template_string(
            """
            <h1>Resumen del dia</h1>
            <pre>{{ data }}</pre>
            <a href="/">Volver</a>
            """,
            data=data,
        )

    @app.get("/day-log")
    def day_log():
        denied = _require_policy("day_log")
        if denied:
            return denied
        rows = storage.get_by_date(_current_service_date())
        return render_template_string(
            """
            <h1>Day Log</h1>
            <ul>
            {% for row in rows %}
              <li>
                {{ row.member_name }} - {{ row.total }}
                <a href="/review/{{ row.id }}">Revisar</a>
              </li>
            {% endfor %}
            </ul>
            <a href="/">Volver</a>
            """,
            rows=rows,
        )

    @app.get("/review/<offering_id>")
    def review_existing(offering_id: str):
        denied = _require_policy("review_existing")
        if denied:
            return denied
        row = storage.get_offering(offering_id)
        if not row:
            return "Not found", 404
        data = {k: ("" if v is None else str(v)) for k, v in row.items()}
        return render_template_string(
            _review_template(),
            data=data,
            action=url_for("save_review", offering_id=offering_id),
            title="Correccion diferida",
            offering_id=offering_id,
        )

    @app.post("/review/<offering_id>/save")
    def save_review(offering_id: str):
        denied = _require_policy("save_review")
        if denied:
            return denied
        updates = {
            field: request.form.get(field, "")
            for field in [
                "member_name",
                "diezmo",
                "ofrenda",
                "primicias",
                "pro_templo",
                "ofrenda_misionera",
                "ofrenda_pastoral",
                "payment_method",
            ]
        }
        ok = storage.update_offering_fields(
            offering_id=offering_id,
            updates=updates,
            changed_by_user_id=getattr(g, "auth_user_id", None),
            reason=request.form.get("reason"),
        )
        if not ok:
            return "Not found", 404
        return redirect(url_for("day_log"))

    @app.get("/admin/config")
    def admin_config():
        denied = _require_policy("admin_config")
        if denied:
            return denied
        return jsonify({"status": "ok", "scope": "admin"})

    @app.post("/cash-window/open")
    def cash_window_open():
        denied = _require_policy("cash_window_open")
        if denied:
            return denied
        session = cash_window_service.open_session(
            service_date=request.form.get("service_date", _current_service_date()),
            actor_user_id=getattr(g, "auth_user_id", None),
            notes=request.form.get("notes"),
        )
        status_code = 201 if session.get("created") else 200
        return jsonify(_json_safe(session)), status_code

    @app.get("/cash-window")
    def cash_window_get():
        denied = _require_policy("cash_window_get")
        if denied:
            return denied
        service_date = request.args.get("service_date", _current_service_date())
        session = cash_window_service.get_session(service_date)
        if not session:
            return jsonify({"status": "not-found", "service_date": service_date}), 404
        return jsonify(_json_safe(session))

    @app.post("/cash-window/line")
    def cash_window_line():
        denied = _require_policy("cash_window_line")
        if denied:
            return denied
        try:
            session = cash_window_service.upsert_line(
                service_date=request.form.get("service_date", _current_service_date()),
                denomination_value=float(request.form.get("denomination_value", "0") or 0),
                denomination_type=request.form.get("denomination_type", "bill"),
                quantity=int(request.form.get("quantity", "0") or 0),
                actor_user_id=getattr(g, "auth_user_id", None),
            )
            return jsonify(_json_safe(session))
        except ValueError as exc:
            return _domain_error_response(exc)

    @app.post("/cash-window/close")
    def cash_window_close():
        denied = _require_policy("cash_window_close")
        if denied:
            return denied
        try:
            session = cash_window_service.close_session(
                service_date=request.form.get("service_date", _current_service_date()),
                actor_user_id=getattr(g, "auth_user_id", None),
                notes=request.form.get("notes"),
            )
            return jsonify(_json_safe(session))
        except ValueError as exc:
            return _domain_error_response(exc)

    @app.post("/cash-window/reopen")
    def cash_window_reopen():
        denied = _require_policy("cash_window_reopen")
        if denied:
            return denied
        try:
            session = cash_window_service.reopen_session(
                service_date=request.form.get("service_date", _current_service_date()),
                actor_user_id=getattr(g, "auth_user_id", None),
                reason=request.form.get("reason"),
            )
            return jsonify(_json_safe(session))
        except ValueError as exc:
            return _domain_error_response(exc)

    @app.post("/outputs/draft")
    def outputs_create_draft():
        denied = _require_policy("outputs_create_draft")
        if denied:
            return denied
        description = request.form.get("description", "").strip()
        amount_raw = request.form.get("amount", "").strip()
        if not description:
            return "Description is required", 400
        if not amount_raw:
            return "Amount is required", 400
        payload = {
            "output_date": request.form.get("output_date", _current_service_date()),
            "category": request.form.get("category", "other"),
            "description": description,
            "beneficiary_name": request.form.get("beneficiary_name"),
            "amount": amount_raw,
            "fund_source_code": request.form.get("fund_source_code", "other"),
            "justification": request.form.get("justification"),
        }
        try:
            row = outputs_service.create_draft(payload, getattr(g, "auth_user_id", None))
        except ValueError:
            return "Invalid draft payload", 400
        return jsonify(_json_safe(row)), 201

    @app.get("/outputs/drafts")
    def outputs_list_drafts():
        denied = _require_policy("outputs_list_drafts")
        if denied:
            return denied
        rows = outputs_service.list_drafts(request.args.get("output_date"))
        return jsonify({"items": _json_safe(rows)})

    @app.post("/outputs/<disbursement_id>/update")
    def outputs_update_draft(disbursement_id: str):
        denied = _require_policy("outputs_update_draft")
        if denied:
            return denied
        payload = {
            "category": request.form.get("category"),
            "description": request.form.get("description"),
            "beneficiary_name": request.form.get("beneficiary_name"),
            "amount": request.form.get("amount"),
            "fund_source_code": request.form.get("fund_source_code"),
            "justification": request.form.get("justification"),
        }
        try:
            row = outputs_service.update_draft(disbursement_id, payload, getattr(g, "auth_user_id", None))
            return jsonify(_json_safe(row))
        except ValueError as exc:
            return _domain_error_response(exc)

    @app.post("/outputs/<disbursement_id>/submit")
    def outputs_submit(disbursement_id: str):
        denied = _require_policy("outputs_submit")
        if denied:
            return denied
        try:
            row = outputs_service.submit(disbursement_id, getattr(g, "auth_user_id", None))
            return jsonify(_json_safe(row))
        except ValueError as exc:
            return _domain_error_response(exc)

    @app.post("/outputs/<disbursement_id>/approve")
    def outputs_approve(disbursement_id: str):
        denied = _require_policy("outputs_approve")
        if denied:
            return denied
        try:
            row = outputs_service.approve(disbursement_id, getattr(g, "auth_user_id", None))
            return jsonify(_json_safe(row))
        except ValueError as exc:
            return _domain_error_response(exc)

    @app.post("/outputs/<disbursement_id>/pay")
    def outputs_pay(disbursement_id: str):
        denied = _require_policy("outputs_pay")
        if denied:
            return denied
        try:
            row = outputs_service.pay(disbursement_id, getattr(g, "auth_user_id", None))
            return jsonify(_json_safe(row))
        except ValueError as exc:
            return _domain_error_response(exc)

    return app


def _review_template() -> str:
    return """
    <h1>{{ title }}</h1>
    <form method="post" action="{{ action }}">
      <input type="hidden" name="image_path" value="{{ data.image_path or '' }}">
      <input type="hidden" name="ocr_confidence" value="{{ data.ocr_confidence or 0.5 }}">
      <label>Nombre</label><input name="member_name" value="{{ data.member_name or '' }}"><br>
      <label>Diezmo</label><input name="diezmo" value="{{ data.diezmo or 0 }}"><br>
      <label>Ofrenda</label><input name="ofrenda" value="{{ data.ofrenda or 0 }}"><br>
      <label>Primicias</label><input name="primicias" value="{{ data.primicias or 0 }}"><br>
      <label>Pro templo</label><input name="pro_templo" value="{{ data.pro_templo or 0 }}"><br>
      <label>Ofrenda misionera</label><input name="ofrenda_misionera" value="{{ data.ofrenda_misionera or 0 }}"><br>
      <label>Ofrenda pastoral</label><input name="ofrenda_pastoral" value="{{ data.ofrenda_pastoral or 0 }}"><br>
      <label>Fecha</label><input name="service_date" value="{{ data.service_date or '' }}"><br>
      <label>Metodo de pago</label><input name="payment_method" value="{{ data.payment_method or 'cash' }}"><br>
      {% if offering_id %}
      <label>Motivo</label><input name="reason" value=""><br>
      {% endif %}
      <button type="submit">Guardar</button>
    </form>
    <a href="/">Volver</a>
    """


def _configure_logging(app: Flask) -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    app.logger.setLevel(logging.INFO)
