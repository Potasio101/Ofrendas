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
from offering_app.services.kiosk_pos_service import KioskPOSService
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
    "workflow_kiosk_view": {"treasurer", "admin", "auditor"},
    "kiosk_open_order": {"treasurer", "admin"},
    "kiosk_list_items": {"treasurer", "admin", "auditor"},
    "kiosk_add_catalog_line": {"treasurer", "admin"},
    "kiosk_add_custom_line": {"treasurer", "admin"},
    "kiosk_pay_order": {"treasurer", "admin"},
}

KNOWN_ROLES = {"treasurer", "admin", "auditor"}


def create_app(
    service: OfferingService,
    storage: PostgreSQLRepo,
    upload_path: str,
    cash_window_service: CashWindowService | None = None,
    outputs_service: OutputsService | None = None,
    kiosk_pos_service: KioskPOSService | None = None,
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
    kiosk_pos_service = kiosk_pos_service or KioskPOSService(storage)

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

    def _ui_base_css() -> str:
                return """
                <style>
                    @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap');
                    :root {
                        --ink: #1f2a37;
                        --muted: #5c6675;
                        --paper: #fffef8;
                        --card: rgba(255, 255, 255, 0.88);
                        --line: rgba(31, 42, 55, 0.14);
                        --brand: #15616d;
                        --brand-strong: #0f4a53;
                        --accent: #f4a261;
                        --danger: #bc4749;
                        --radius: 18px;
                        --shadow: 0 14px 35px rgba(21, 97, 109, 0.16);
                    }
                    * { box-sizing: border-box; }
                    body {
                        margin: 0;
                        min-height: 100vh;
                        color: var(--ink);
                        font-family: 'Manrope', 'Avenir Next', sans-serif;
                        background:
                            radial-gradient(circle at 10% -10%, rgba(244, 162, 97, 0.22), transparent 45%),
                            radial-gradient(circle at 100% 0%, rgba(21, 97, 109, 0.22), transparent 45%),
                            linear-gradient(145deg, #fffdf4 0%, #f5fbfb 48%, #f0f6f7 100%);
                    }
                    .app-shell { max-width: 980px; margin: 0 auto; padding: 18px 14px 28px; }
                    .hero {
                        border-radius: calc(var(--radius) + 6px);
                        background: linear-gradient(130deg, var(--brand) 0%, #1d7874 58%, #2a9d8f 100%);
                        color: #fff;
                        padding: 20px 18px;
                        box-shadow: var(--shadow);
                        margin-bottom: 14px;
                    }
                    h1 {
                        margin: 0;
                        font-size: clamp(1.45rem, 5vw, 2rem);
                        font-family: 'Fraunces', Georgia, serif;
                        letter-spacing: 0.2px;
                        line-height: 1.15;
                    }
                    .hero p { margin: 8px 0 0; color: rgba(255, 255, 255, 0.9); }
                    .section-grid {
                        display: grid;
                        grid-template-columns: 1fr;
                        gap: 12px;
                    }
                    .card {
                        background: var(--card);
                        border: 1px solid var(--line);
                        border-radius: var(--radius);
                        padding: 14px;
                        box-shadow: 0 8px 26px rgba(10, 23, 45, 0.08);
                        backdrop-filter: blur(2px);
                    }
                    .card h2 {
                        margin: 0 0 8px;
                        font-size: 1.05rem;
                        color: var(--brand-strong);
                    }
                    .metric-row {
                        display: grid;
                        grid-template-columns: repeat(2, minmax(0, 1fr));
                        gap: 10px;
                    }
                    .metric {
                        background: rgba(21, 97, 109, 0.08);
                        border-radius: 12px;
                        padding: 10px;
                    }
                    .metric-label { display: block; font-size: 0.78rem; color: var(--muted); }
                    .metric-value { display: block; margin-top: 3px; font-size: 1.2rem; font-weight: 800; }
                    .nav-grid {
                        display: grid;
                        gap: 8px;
                        grid-template-columns: repeat(2, minmax(0, 1fr));
                    }
                    .nav-pill {
                        display: inline-block;
                        width: 100%;
                        text-align: center;
                        text-decoration: none;
                        color: var(--brand-strong);
                        background: rgba(21, 97, 109, 0.1);
                        border: 1px solid rgba(21, 97, 109, 0.22);
                        border-radius: 999px;
                        padding: 10px 12px;
                        font-weight: 700;
                        font-size: 0.92rem;
                    }
                    form { margin: 0; }
                    label {
                        display: block;
                        margin: 10px 0 5px;
                        font-size: 0.83rem;
                        font-weight: 700;
                        color: var(--brand-strong);
                    }
                    input, button {
                        width: 100%;
                        font: inherit;
                        border-radius: 12px;
                        border: 1px solid rgba(31, 42, 55, 0.2);
                        padding: 11px 12px;
                        background: #fff;
                    }
                    input:focus {
                        outline: 2px solid rgba(21, 97, 109, 0.18);
                        border-color: var(--brand);
                    }
                    button {
                        margin-top: 12px;
                        border: 0;
                        font-weight: 800;
                        color: #fff;
                        background: linear-gradient(125deg, var(--brand) 0%, #1f7a7a 100%);
                        box-shadow: 0 8px 18px rgba(21, 97, 109, 0.28);
                    }
                    .btn-danger {
                        background: linear-gradient(125deg, var(--danger) 0%, #d9534f 100%);
                    }
                    .hint { margin-top: 8px; color: var(--muted); font-size: 0.86rem; }
                    .list-clean { list-style: none; margin: 0; padding: 0; display: grid; gap: 10px; }
                    .row-item {
                        display: flex;
                        align-items: center;
                        justify-content: space-between;
                        gap: 10px;
                        border: 1px solid var(--line);
                        border-radius: 12px;
                        padding: 10px;
                        background: rgba(255, 255, 255, 0.76);
                    }
                    .row-main { min-width: 0; }
                    .row-title { font-weight: 700; }
                    .row-meta { color: var(--muted); font-size: 0.85rem; }
                    .inline-link { color: var(--brand-strong); text-decoration: none; font-weight: 700; }
                    .stack { display: grid; gap: 12px; }
                    @media (min-width: 720px) {
                        .app-shell { padding: 26px 22px 36px; }
                        .section-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
                        .section-grid.full { grid-template-columns: 1fr; }
                    }
                </style>
                """

    def _ui_header(title: str, subtitle: str) -> str:
                return f"""
                <div class="hero">
                    <h1>{title}</h1>
                    <p>{subtitle}</p>
                </div>
                """

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
                        {{ ui_css|safe }}
                        <main class="app-shell">
                            {{ ui_header|safe }}
                            <section class="section-grid">
                                <article class="card">
                                    <h2>Panorama del dia</h2>
                                    <div class="metric-row">
                                        <div class="metric">
                                            <span class="metric-label">Sobres</span>
                                            <span class="metric-value">{{ summary.envelopes }}</span>
                                        </div>
                                        <div class="metric">
                                            <span class="metric-label">Total</span>
                                            <span class="metric-value">{{ summary.total }}</span>
                                        </div>
                                    </div>
                                    <p class="hint">Registro rapido para momentos de alta afluencia.</p>
                                </article>

                                <article class="card">
                                    <h2>Nuevo sobre</h2>
                                    <form action="/process" method="post" enctype="multipart/form-data">
                                        <label>Imagen del sobre</label>
                                        <input type="file" name="image" accept="image/*" capture="environment" required>
                                        <p class="hint">En celular se abrira la camara para tomar la foto del sobre.</p>
                                        <button type="submit">Procesar captura</button>
                                    </form>
                                </article>
                            </section>

                            <section class="card" style="margin-top:12px;">
                                <h2>Navegacion</h2>
                                <div class="nav-grid">
                                    <a class="nav-pill" href="/day-log">Day Log</a>
                                    <a class="nav-pill" href="/summary">Resumen</a>
                                    <a class="nav-pill" href="/workflow/cash">Caja</a>
                                    <a class="nav-pill" href="/workflow/outputs">Salidas</a>
                                    <a class="nav-pill" href="/workflow/kiosk">Kiosk POS</a>
                                </div>
                            </section>
                        </main>
            """,
            summary=summary,
                        ui_css=_ui_base_css(),
                        ui_header=_ui_header("Ofrendas", "Operacion diaria con enfoque mobile-first y auditoria visible."),
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
                        {{ ui_css|safe }}
                        <main class="app-shell">
                            {{ ui_header|safe }}
                            <section class="card stack">
                                <div class="metric-row">
                                    <div class="metric">
                                        <span class="metric-label">Sobres</span>
                                        <span class="metric-value">{{ data.envelopes }}</span>
                                    </div>
                                    <div class="metric">
                                        <span class="metric-label">Total</span>
                                        <span class="metric-value">{{ data.total }}</span>
                                    </div>
                                </div>
                                <a class="inline-link" href="/">Volver al inicio</a>
                            </section>
                        </main>
            """,
            data=data,
                        ui_css=_ui_base_css(),
                        ui_header=_ui_header("Resumen del dia", "Vista rapida para tesoreria y auditoria."),
        )

    @app.get("/day-log")
    def day_log():
        denied = _require_policy("day_log")
        if denied:
            return denied
        rows = storage.get_by_date(_current_service_date())
        return render_template_string(
            """
                        {{ ui_css|safe }}
                        <main class="app-shell">
                            {{ ui_header|safe }}
                            <section class="card">
                                <ul class="list-clean">
                                {% for row in rows %}
                                    <li class="row-item">
                                        <div class="row-main">
                                            <div class="row-title">{{ row.member_name or 'Sin nombre' }}</div>
                                            <div class="row-meta">Total: {{ row.total }}</div>
                                        </div>
                                        <a class="inline-link" href="/review/{{ row.id }}">Revisar</a>
                                    </li>
                                {% endfor %}
                                {% if not rows %}
                                    <li class="row-item">
                                        <div class="row-main">
                                            <div class="row-title">Sin registros aun</div>
                                            <div class="row-meta">Empieza capturando un nuevo sobre.</div>
                                        </div>
                                    </li>
                                {% endif %}
                                </ul>
                                <p class="hint">Cada fila conserva trazabilidad para correccion diferida.</p>
                                <a class="inline-link" href="/">Volver al inicio</a>
                            </section>
                        </main>
            """,
            rows=rows,
                        ui_css=_ui_base_css(),
                        ui_header=_ui_header("Day Log", "Cola de revision y correccion post-captura."),
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
                        {{ ui_css|safe }}
                        <main class="app-shell">
                            {{ ui_header|safe }}
                            <section class="section-grid full">
                                <article class="card stack">
                                    <h2>Apertura y cierre</h2>
                                    <p class="hint">Fecha de servicio: {{ service_date }}</p>
                                    <form method="post" action="/cash-window/open">
                                        <input type="hidden" name="service_date" value="{{ service_date }}">
                                        <label>Notas de apertura</label>
                                        <input name="notes" placeholder="Notas apertura">
                                        <button type="submit">Abrir sesion</button>
                                    </form>
                                    <form method="post" action="/cash-window/close">
                                        <input type="hidden" name="service_date" value="{{ service_date }}">
                                        <label>Notas de cierre</label>
                                        <input name="notes" placeholder="Notas cierre">
                                        <button type="submit">Cerrar sesion</button>
                                    </form>
                                </article>

                                <article class="card stack">
                                    <h2>Conteo por denominacion</h2>
                                    <form method="post" action="/cash-window/line">
                                        <input type="hidden" name="service_date" value="{{ service_date }}">
                                        <label>Valor</label>
                                        <input name="denomination_value" value="20">
                                        <label>Tipo</label>
                                        <input name="denomination_type" value="bill">
                                        <label>Cantidad</label>
                                        <input name="quantity" value="1">
                                        <button type="submit">Actualizar linea</button>
                                    </form>
                                    <form method="post" action="/cash-window/reopen">
                                        <input type="hidden" name="service_date" value="{{ service_date }}">
                                        <label>Motivo reapertura</label>
                                        <input name="reason" placeholder="Motivo reapertura">
                                        <button class="btn-danger" type="submit">Reabrir sesion (admin)</button>
                                    </form>
                                </article>
                            </section>
                            <a class="inline-link" href="/">Volver al inicio</a>
                        </main>
            """,
            service_date=service_date,
                        ui_css=_ui_base_css(),
                        ui_header=_ui_header("Cash Workflow", "Control de caja por flujo guiado y listo para movil."),
        )

    @app.get("/workflow/outputs")
    def workflow_outputs_view():
        denied = _require_policy("workflow_outputs_view")
        if denied:
            return denied
        output_date = _current_service_date()
        return render_template_string(
            """
                        {{ ui_css|safe }}
                        <main class="app-shell">
                            {{ ui_header|safe }}
                            <section class="section-grid full">
                                <article class="card">
                                    <h2>Crear salida</h2>
                                    <p class="hint">Fecha de salida: {{ output_date }}</p>
                                    <form method="post" action="/outputs/draft">
                                        <input type="hidden" name="output_date" value="{{ output_date }}">
                                        <label>Categoria</label>
                                        <input name="category" value="other">
                                        <label>Descripcion</label>
                                        <input name="description" value="Pago servicio">
                                        <label>Monto</label>
                                        <input name="amount" value="10">
                                        <label>Fuente de fondo</label>
                                        <input name="fund_source_code" value="other">
                                        <button type="submit">Crear draft</button>
                                    </form>
                                    <p class="hint">Las transiciones submit, approve y pay usan los endpoints API por id.</p>
                                </article>
                            </section>
                            <a class="inline-link" href="/">Volver al inicio</a>
                        </main>
            """,
            output_date=output_date,
                        ui_css=_ui_base_css(),
                        ui_header=_ui_header("Outputs Workflow", "Registro de salidas con base operativa y control de estados."),
        )

    @app.get("/workflow/kiosk")
    def workflow_kiosk_view():
        denied = _require_policy("workflow_kiosk_view")
        if denied:
            return denied
        service_date = _current_service_date()
        items = kiosk_pos_service.list_items(active_only=True)
        return render_template_string(
            """
                        {{ ui_css|safe }}
                        <main class="app-shell">
                            {{ ui_header|safe }}
                            <section class="section-grid full">
                                <article class="card">
                                    <h2>Abrir orden</h2>
                                    <p class="hint">Fecha de servicio: {{ service_date }}</p>
                                    <form method="post" action="/kiosk/order/open">
                                        <input type="hidden" name="service_date" value="{{ service_date }}">
                                        <label>Notas</label>
                                        <input name="notes" placeholder="Notas opcionais">
                                        <button type="submit">Abrir orden</button>
                                    </form>
                                </article>

                                <article class="card stack">
                                    <h2>Agregar item de catalogo</h2>
                                    <form method="post" action="/kiosk/order/line/catalog">
                                        <label>Order ID</label>
                                        <input name="kiosk_order_id" placeholder="UUID de orden abierta">
                                        <label>Item ID</label>
                                        <input name="kiosk_item_id" placeholder="UUID item">
                                        <label>Cantidad</label>
                                        <input name="quantity" value="1">
                                        <button type="submit">Agregar item</button>
                                    </form>
                                    <p class="hint">Items activos: {{ items|length }}</p>
                                </article>

                                <article class="card stack">
                                    <h2>Agregar item custom</h2>
                                    <form method="post" action="/kiosk/order/line/custom">
                                        <label>Order ID</label>
                                        <input name="kiosk_order_id" placeholder="UUID de orden abierta">
                                        <label>Nombre item</label>
                                        <input name="item_name" placeholder="Empanada especial">
                                        <label>Precio unitario</label>
                                        <input name="unit_price" value="5">
                                        <label>Cantidad</label>
                                        <input name="quantity" value="1">
                                        <button type="submit">Agregar custom</button>
                                    </form>
                                </article>

                                <article class="card stack">
                                    <h2>Cerrar pago</h2>
                                    <form method="post" action="/kiosk/order/pay">
                                        <label>Order ID</label>
                                        <input name="kiosk_order_id" placeholder="UUID de orden abierta">
                                        <label>Metodo (cash o zelle)</label>
                                        <input name="payment_method" value="cash">
                                        <label>Monto pagado</label>
                                        <input name="amount_paid" value="10">
                                        <label>Cash recibido (cash)</label>
                                        <input name="cash_received" value="10">
                                        <label>Nombre pagador (zelle)</label>
                                        <input name="zelle_customer_name" placeholder="Nombre completo">
                                        <label>Referencia</label>
                                        <input name="transaction_reference" placeholder="ref-123">
                                        <button type="submit">Registrar pago</button>
                                    </form>
                                    <p class="hint">Para zelle se requiere nombre del pagador; total debe ser mayor a cero.</p>
                                </article>
                            </section>
                            <a class="inline-link" href="/">Volver al inicio</a>
                        </main>
            """,
            service_date=service_date,
            items=items,
            ui_css=_ui_base_css(),
            ui_header=_ui_header("Kiosk Workflow", "POS rapido para cash y zelle con items custom."),
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

    @app.post("/kiosk/order/open")
    def kiosk_open_order():
        denied = _require_policy("kiosk_open_order")
        if denied:
            return denied
        order = kiosk_pos_service.get_or_create_open_order(
            service_date=request.form.get("service_date", _current_service_date()),
            actor_user_id=getattr(g, "auth_user_id", None),
            notes=request.form.get("notes"),
        )
        status_code = 201 if order.get("created") else 200
        transition = {
            "entity": "kiosk_order",
            "action": "open_order",
            "from_status": "none" if order.get("created") else "open",
            "to_status": order.get("order_status", "open"),
        }
        return _ok_response({"order": order, "transition": transition}, "Kiosk order opened", status_code)

    @app.get("/kiosk/items")
    def kiosk_items():
        denied = _require_policy("kiosk_list_items")
        if denied:
            return denied
        items = kiosk_pos_service.list_items(active_only=request.args.get("active_only", "1") != "0")
        return _ok_response({"items": items}, "Kiosk items fetched")

    @app.post("/kiosk/order/line/catalog")
    def kiosk_add_catalog_line():
        denied = _require_policy("kiosk_add_catalog_line")
        if denied:
            return denied
        kiosk_order_id = (request.form.get("kiosk_order_id") or "").strip()
        kiosk_item_id = (request.form.get("kiosk_item_id") or "").strip()
        if not kiosk_order_id or not kiosk_item_id:
            return jsonify({"status": "error", "error": "invalid_payload", "message": "Order and item are required"}), 400
        try:
            order = kiosk_pos_service.add_catalog_line(
                kiosk_order_id=kiosk_order_id,
                kiosk_item_id=kiosk_item_id,
                quantity=int(request.form.get("quantity", "1") or 1),
                actor_user_id=getattr(g, "auth_user_id", None),
            )
            transition = {
                "entity": "kiosk_order",
                "action": "line_add_catalog",
                "from_status": "open",
                "to_status": order.get("order_status", "open"),
            }
            return _ok_response({"order": order, "transition": transition}, "Catalog line added")
        except ValueError as exc:
            return _domain_error_response(exc)

    @app.post("/kiosk/order/line/custom")
    def kiosk_add_custom_line():
        denied = _require_policy("kiosk_add_custom_line")
        if denied:
            return denied
        kiosk_order_id = (request.form.get("kiosk_order_id") or "").strip()
        item_name = (request.form.get("item_name") or "").strip()
        if not kiosk_order_id or not item_name:
            return jsonify({"status": "error", "error": "invalid_payload", "message": "Order and item name are required"}), 400
        try:
            order = kiosk_pos_service.add_custom_line(
                kiosk_order_id=kiosk_order_id,
                item_name=item_name,
                unit_price=float(request.form.get("unit_price", "0") or 0),
                quantity=int(request.form.get("quantity", "1") or 1),
                actor_user_id=getattr(g, "auth_user_id", None),
            )
            transition = {
                "entity": "kiosk_order",
                "action": "line_add_custom",
                "from_status": "open",
                "to_status": order.get("order_status", "open"),
            }
            return _ok_response({"order": order, "transition": transition}, "Custom line added")
        except ValueError as exc:
            return _domain_error_response(exc)

    @app.post("/kiosk/order/pay")
    def kiosk_pay_order():
        denied = _require_policy("kiosk_pay_order")
        if denied:
            return denied
        kiosk_order_id = (request.form.get("kiosk_order_id") or "").strip()
        method = (request.form.get("payment_method") or "").strip().lower()
        amount_raw = (request.form.get("amount_paid") or "").strip()
        if not kiosk_order_id or not method or not amount_raw:
            return jsonify({"status": "error", "error": "invalid_payload", "message": "Order, payment method and amount are required"}), 400
        try:
            result = kiosk_pos_service.pay_order(
                kiosk_order_id=kiosk_order_id,
                payment_method=method,
                amount_paid=float(amount_raw),
                cash_received=(
                    float(request.form.get("cash_received"))
                    if request.form.get("cash_received") not in {None, ""}
                    else None
                ),
                zelle_customer_name=request.form.get("zelle_customer_name"),
                transaction_reference=request.form.get("transaction_reference"),
                actor_user_id=getattr(g, "auth_user_id", None),
            )
            transition = {
                "entity": "kiosk_order",
                "action": "pay",
                "from_status": "open",
                "to_status": result.get("order", {}).get("order_status", "paid"),
            }
            return _ok_response({"payment": result.get("payment"), "order": result.get("order"), "transition": transition}, "Kiosk order paid")
        except ValueError as exc:
            return _domain_error_response(exc)

    return app


def _review_template() -> str:
    return """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap');
            :root {
                --ink: #1f2a37;
                --muted: #5c6675;
                --brand: #15616d;
                --card: rgba(255, 255, 255, 0.9);
                --line: rgba(31, 42, 55, 0.14);
            }
            * { box-sizing: border-box; }
            body {
                margin: 0;
                min-height: 100vh;
                color: var(--ink);
                font-family: 'Manrope', 'Avenir Next', sans-serif;
                background:
                    radial-gradient(circle at 0 0, rgba(21, 97, 109, 0.2), transparent 34%),
                    linear-gradient(150deg, #fffdf4 0%, #f4fbfb 100%);
            }
            .shell { max-width: 920px; margin: 0 auto; padding: 18px 14px 26px; }
            .hero {
                border-radius: 20px;
                background: linear-gradient(130deg, #15616d 0%, #2a9d8f 100%);
                color: #fff;
                padding: 18px;
                margin-bottom: 12px;
            }
            h1 {
                margin: 0;
                font-family: 'Fraunces', Georgia, serif;
                font-size: clamp(1.3rem, 5vw, 1.9rem);
            }
            .hero p { margin: 8px 0 0; color: rgba(255, 255, 255, 0.88); }
            .card {
                background: var(--card);
                border: 1px solid var(--line);
                border-radius: 16px;
                padding: 14px;
            }
            .grid { display: grid; grid-template-columns: 1fr; gap: 10px; }
            @media (min-width: 760px) { .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
            label {
                display: block;
                margin: 2px 0 5px;
                font-size: 0.83rem;
                font-weight: 700;
                color: #0f4a53;
            }
            input, button {
                width: 100%;
                font: inherit;
                border: 1px solid rgba(31, 42, 55, 0.24);
                border-radius: 12px;
                padding: 11px 12px;
                background: #fff;
            }
            button {
                margin-top: 12px;
                border: 0;
                color: #fff;
                font-weight: 800;
                background: linear-gradient(125deg, #15616d 0%, #1f7a7a 100%);
            }
            .meta { margin: 8px 0 0; color: var(--muted); font-size: 0.86rem; }
            .inline-link { display: inline-block; margin-top: 12px; color: #0f4a53; font-weight: 700; text-decoration: none; }
        </style>

        <main class="shell">
            <section class="hero">
                <h1>{{ title }}</h1>
                <p>Ajusta montos, valida metodo de pago y guarda con trazabilidad.</p>
            </section>

            <section class="card">
                <form method="post" action="{{ action }}">
                    <input type="hidden" name="image_path" value="{{ data.image_path or '' }}">
                    <input type="hidden" name="ocr_confidence" value="{{ data.ocr_confidence or 0.5 }}">

                    <div class="grid">
                        <div>
                            <label>Nombre</label>
                            <input name="member_name" value="{{ data.member_name or '' }}">
                        </div>
                        <div>
                            <label>Fecha</label>
                            <input name="service_date" value="{{ data.service_date or '' }}">
                        </div>
                        <div>
                            <label>Diezmo</label>
                            <input name="diezmo" value="{{ data.diezmo or 0 }}">
                        </div>
                        <div>
                            <label>Ofrenda</label>
                            <input name="ofrenda" value="{{ data.ofrenda or 0 }}">
                        </div>
                        <div>
                            <label>Primicias</label>
                            <input name="primicias" value="{{ data.primicias or 0 }}">
                        </div>
                        <div>
                            <label>Pro templo</label>
                            <input name="pro_templo" value="{{ data.pro_templo or 0 }}">
                        </div>
                        <div>
                            <label>Ofrenda misionera</label>
                            <input name="ofrenda_misionera" value="{{ data.ofrenda_misionera or 0 }}">
                        </div>
                        <div>
                            <label>Ofrenda pastoral</label>
                            <input name="ofrenda_pastoral" value="{{ data.ofrenda_pastoral or 0 }}">
                        </div>
                        <div>
                            <label>Metodo de pago</label>
                            <input name="payment_method" value="{{ data.payment_method or 'cash' }}">
                        </div>
                        {% if offering_id %}
                        <div>
                            <label>Motivo</label>
                            <input name="reason" value="">
                        </div>
                        {% endif %}
                    </div>

                    <button type="submit">Guardar</button>
                    <p class="meta">OCR confidence: {{ data.ocr_confidence or 0.5 }}</p>
                </form>
                <a class="inline-link" href="/">Volver al inicio</a>
            </section>
        </main>
    """


def _configure_logging(app: Flask) -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    app.logger.setLevel(logging.INFO)
