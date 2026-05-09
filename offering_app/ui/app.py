from datetime import datetime
from decimal import Decimal
import hashlib
import hmac
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
    "workflow_cash_view": {"treasurer", "admin", "auditor"},
    "workflow_outputs_view": {"treasurer", "admin", "auditor"},
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
    app.config["APP_AUTH_PROXY_TOKEN"] = os.getenv("APP_AUTH_PROXY_TOKEN", "")
    app.config["APP_AUTH_PROXY_SIGNING_SECRET"] = os.getenv("APP_AUTH_PROXY_SIGNING_SECRET", "")
    app.config["APP_AUTH_PROXY_MAX_AGE_SECONDS"] = int(os.getenv("APP_AUTH_PROXY_MAX_AGE_SECONDS", "300"))
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

        if auth_mode == "proxy-signed":
            signing_secret = str(app.config.get("APP_AUTH_PROXY_SIGNING_SECRET") or "").strip()
            incoming_signature = (request.headers.get("X-Auth-Signature") or "").strip().lower()
            incoming_ts = (request.headers.get("X-Auth-Timestamp") or "").strip()
            proxy_role = (request.headers.get("X-Auth-Role") or header_role).strip().lower()
            proxy_user_id = (request.headers.get("X-Auth-User-Id") or header_user_id).strip()

            g.auth_role = proxy_role
            g.auth_user_id = proxy_user_id

            if not signing_secret:
                g.auth_error = "proxy_signature_not_configured"
            elif not incoming_signature or not incoming_ts:
                g.auth_error = "missing_signature"
            elif not proxy_role or not proxy_user_id:
                g.auth_error = "missing_identity"
            elif proxy_role not in KNOWN_ROLES:
                g.auth_error = "invalid_role"
            else:
                try:
                    ts_value = int(incoming_ts)
                except ValueError:
                    g.auth_error = "invalid_signature_timestamp"
                else:
                    now_ts = int(time.time())
                    max_age = int(app.config.get("APP_AUTH_PROXY_MAX_AGE_SECONDS", 300))
                    if abs(now_ts - ts_value) > max_age:
                        g.auth_error = "stale_signature"
                    else:
                        payload = f"{proxy_role}:{proxy_user_id}:{incoming_ts}".encode("utf-8")
                        expected_signature = hmac.new(
                            signing_secret.encode("utf-8"),
                            payload,
                            hashlib.sha256,
                        ).hexdigest()
                        if not hmac.compare_digest(expected_signature, incoming_signature):
                            g.auth_error = "invalid_signature"
        elif auth_mode == "proxy-token":
            expected_token = str(app.config.get("APP_AUTH_PROXY_TOKEN") or "").strip()
            incoming_token = (request.headers.get("X-Auth-Proxy-Token") or "").strip()
            proxy_role = (request.headers.get("X-Auth-Role") or header_role).strip().lower()
            proxy_user_id = (request.headers.get("X-Auth-User-Id") or header_user_id).strip()

            g.auth_role = proxy_role
            g.auth_user_id = proxy_user_id

            if not expected_token:
                g.auth_error = "proxy_token_not_configured"
            elif not incoming_token:
                g.auth_error = "missing_proxy_token"
            elif incoming_token != expected_token:
                g.auth_error = "invalid_proxy_token"
            elif not proxy_role or not proxy_user_id:
                g.auth_error = "missing_identity"
            elif proxy_role not in KNOWN_ROLES:
                g.auth_error = "invalid_role"
        elif auth_mode == "header-strict":
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
            return jsonify({"status": "error", "error": "not_found", "message": "Not found"}), 404
        if "invalid_transition" in message or "closed" in message:
            return jsonify({"status": "error", "error": "invalid_transition", "message": "Conflict"}), 409
        if "invalid_" in message:
            return jsonify({"status": "error", "error": "invalid_payload", "message": "Invalid payload"}), 400
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
        return jsonify({"status": "error", "error": "internal_error", "message": "Internal error"}), 500

    def _ok_response(data, message: str, status_code: int = 200):
        return jsonify({"status": "ok", "message": message, "data": _json_safe(data)}), status_code

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
                        <style>
                            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 16px; }
                            .card { border: 1px solid #d9d9d9; border-radius: 12px; padding: 12px; margin-bottom: 12px; }
                            .actions a { display: inline-block; margin-right: 8px; margin-top: 8px; }
                            input, button { font-size: 16px; padding: 10px; }
                        </style>
            <h1>Ofrendas</h1>
                        <div class="card">
                            <p>Sobres hoy: {{ summary.envelopes }}</p>
                            <p>Total hoy: {{ summary.total }}</p>
                        </div>
                        <div class="card">
                            <form action="/process" method="post" enctype="multipart/form-data">
                                <input type="file" name="image" required>
                                <button type="submit">Nuevo Sobre</button>
                            </form>
                        </div>
                        <div class="actions">
                            <a href="/day-log">Day Log</a>
                            <a href="/summary">Resumen</a>
                            <a href="/workflow/cash">Caja (mobile)</a>
                            <a href="/workflow/outputs">Salidas (mobile)</a>
                        </div>
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

    @app.get("/workflow/cash")
    def workflow_cash_view():
        denied = _require_policy("workflow_cash_view")
        if denied:
            return denied
        service_date = _current_service_date()
        return render_template_string(
            """
            <style>
              body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 14px; }
              form { border: 1px solid #d9d9d9; border-radius: 10px; padding: 10px; margin-bottom: 10px; }
              input, button { width: 100%; box-sizing: border-box; margin: 6px 0; font-size: 16px; padding: 10px; }
            </style>
            <h1>Cash Workflow</h1>
            <p>Fecha de servicio: {{ service_date }}</p>
            <form method="post" action="/cash-window/open">
              <input type="hidden" name="service_date" value="{{ service_date }}">
              <input name="notes" placeholder="Notas apertura">
              <button type="submit">Abrir sesion</button>
            </form>
            <form method="post" action="/cash-window/line">
              <input type="hidden" name="service_date" value="{{ service_date }}">
              <input name="denomination_value" value="20">
              <input name="denomination_type" value="bill">
              <input name="quantity" value="1">
              <button type="submit">Actualizar linea</button>
            </form>
            <form method="post" action="/cash-window/close">
              <input type="hidden" name="service_date" value="{{ service_date }}">
              <input name="notes" placeholder="Notas cierre">
              <button type="submit">Cerrar sesion</button>
            </form>
            <form method="post" action="/cash-window/reopen">
              <input type="hidden" name="service_date" value="{{ service_date }}">
              <input name="reason" placeholder="Motivo reapertura">
              <button type="submit">Reabrir sesion (admin)</button>
            </form>
            <a href="/">Volver</a>
            """,
            service_date=service_date,
        )

    @app.get("/workflow/outputs")
    def workflow_outputs_view():
        denied = _require_policy("workflow_outputs_view")
        if denied:
            return denied
        output_date = _current_service_date()
        return render_template_string(
            """
            <style>
              body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 14px; }
              form { border: 1px solid #d9d9d9; border-radius: 10px; padding: 10px; margin-bottom: 10px; }
              input, button { width: 100%; box-sizing: border-box; margin: 6px 0; font-size: 16px; padding: 10px; }
            </style>
            <h1>Outputs Workflow</h1>
            <p>Fecha de salida: {{ output_date }}</p>
            <form method="post" action="/outputs/draft">
              <input type="hidden" name="output_date" value="{{ output_date }}">
              <input name="category" value="other">
              <input name="description" value="Pago servicio">
              <input name="amount" value="10">
              <input name="fund_source_code" value="other">
              <button type="submit">Crear draft</button>
            </form>
            <p>Transiciones submit/approve/pay usan rutas API con id del draft.</p>
            <a href="/">Volver</a>
            """,
            output_date=output_date,
        )

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
        transition = {
            "entity": "cash_session",
            "action": "open",
            "from_status": "none" if session.get("created") else "open",
            "to_status": session.get("session_status", "open"),
        }
        return _ok_response({"session": session, "transition": transition}, "Cash session opened", status_code)

    @app.get("/cash-window")
    def cash_window_get():
        denied = _require_policy("cash_window_get")
        if denied:
            return denied
        service_date = request.args.get("service_date", _current_service_date())
        session = cash_window_service.get_session(service_date)
        if not session:
            return jsonify({"status": "not-found", "service_date": service_date}), 404
        return _ok_response({"session": session}, "Cash session fetched")

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
            transition = {
                "entity": "cash_session",
                "action": "line_update",
                "from_status": session.get("session_status", "open"),
                "to_status": session.get("session_status", "open"),
            }
            return _ok_response({"session": session, "transition": transition}, "Cash line updated")
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
            transition = {
                "entity": "cash_session",
                "action": "close",
                "from_status": "open",
                "to_status": session.get("session_status", "closed"),
            }
            return _ok_response({"session": session, "transition": transition}, "Cash session closed")
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
            transition = {
                "entity": "cash_session",
                "action": "reopen",
                "from_status": "closed",
                "to_status": session.get("session_status", "open"),
            }
            return _ok_response({"session": session, "transition": transition}, "Cash session reopened")
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
            return jsonify({"status": "error", "error": "invalid_payload", "message": "Description is required"}), 400
        if not amount_raw:
            return jsonify({"status": "error", "error": "invalid_payload", "message": "Amount is required"}), 400
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
            return jsonify({"status": "error", "error": "invalid_payload", "message": "Invalid draft payload"}), 400
        transition = {
            "entity": "disbursement",
            "action": "create_draft",
            "from_status": "none",
            "to_status": row.get("status", "draft"),
        }
        return _ok_response({"disbursement": row, "transition": transition}, "Disbursement draft created", 201)

    @app.get("/outputs/drafts")
    def outputs_list_drafts():
        denied = _require_policy("outputs_list_drafts")
        if denied:
            return denied
        rows = outputs_service.list_drafts(request.args.get("output_date"))
        return _ok_response({"items": rows}, "Disbursement drafts fetched")

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
            transition = {
                "entity": "disbursement",
                "action": "update_draft",
                "from_status": "draft",
                "to_status": row.get("status", "draft"),
            }
            return _ok_response({"disbursement": row, "transition": transition}, "Disbursement draft updated")
        except ValueError as exc:
            return _domain_error_response(exc)

    @app.post("/outputs/<disbursement_id>/submit")
    def outputs_submit(disbursement_id: str):
        denied = _require_policy("outputs_submit")
        if denied:
            return denied
        try:
            row = outputs_service.submit(disbursement_id, getattr(g, "auth_user_id", None))
            transition = {
                "entity": "disbursement",
                "action": "submit",
                "from_status": "draft",
                "to_status": row.get("status", "submitted"),
            }
            return _ok_response({"disbursement": row, "transition": transition}, "Disbursement submitted")
        except ValueError as exc:
            return _domain_error_response(exc)

    @app.post("/outputs/<disbursement_id>/approve")
    def outputs_approve(disbursement_id: str):
        denied = _require_policy("outputs_approve")
        if denied:
            return denied
        try:
            row = outputs_service.approve(disbursement_id, getattr(g, "auth_user_id", None))
            transition = {
                "entity": "disbursement",
                "action": "approve",
                "from_status": "submitted",
                "to_status": row.get("status", "approved"),
            }
            return _ok_response({"disbursement": row, "transition": transition}, "Disbursement approved")
        except ValueError as exc:
            return _domain_error_response(exc)

    @app.post("/outputs/<disbursement_id>/pay")
    def outputs_pay(disbursement_id: str):
        denied = _require_policy("outputs_pay")
        if denied:
            return denied
        try:
            row = outputs_service.pay(disbursement_id, getattr(g, "auth_user_id", None))
            transition = {
                "entity": "disbursement",
                "action": "pay",
                "from_status": "approved",
                "to_status": row.get("status", "paid"),
            }
            return _ok_response({"disbursement": row, "transition": transition}, "Disbursement paid")
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
