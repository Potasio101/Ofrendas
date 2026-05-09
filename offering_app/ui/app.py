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

from offering_app.config import validate_auth_configuration
from offering_app.repositories.postgresql_repo import PostgreSQLRepo
from offering_app.services.cash_window_service import CashWindowService
from offering_app.services.kiosk_pos_service import KioskPOSService
from offering_app.services.offering_service import OfferingService
from offering_app.services.outputs_service import OutputsService
from offering_app.ui.presentation import review_template, ui_base_css, ui_header
from offering_app.ui.routes_workflow import register_workflow_routes


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
    app.config["APP_ENV"] = os.getenv("APP_ENV", "local")
    app.config["UPLOAD_PATH"] = upload_path
    app.config["APP_TIMEZONE"] = os.getenv("APP_TIMEZONE", "UTC")
    app.config["APP_DEFAULT_ROLE"] = os.getenv("APP_DEFAULT_ROLE", "treasurer")
    app.config["APP_DEFAULT_USER_ID"] = os.getenv("APP_DEFAULT_USER_ID", "local-dev-user")
    app.config["APP_AUTH_MODE"] = os.getenv("APP_AUTH_MODE", "local-dev")
    app.config["APP_AUTH_PROXY_TOKEN"] = os.getenv("APP_AUTH_PROXY_TOKEN", "")
    app.config["APP_AUTH_PROXY_SIGNING_SECRET"] = os.getenv("APP_AUTH_PROXY_SIGNING_SECRET", "")
    app.config["APP_AUTH_PROXY_MAX_AGE_SECONDS"] = int(os.getenv("APP_AUTH_PROXY_MAX_AGE_SECONDS", "300"))

    validate_auth_configuration(
        app_env=app.config["APP_ENV"],
        auth_mode=app.config["APP_AUTH_MODE"],
        proxy_token=app.config["APP_AUTH_PROXY_TOKEN"],
        proxy_signing_secret=app.config["APP_AUTH_PROXY_SIGNING_SECRET"],
    )

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
        return ui_base_css()

    def _ui_header(title: str, subtitle: str) -> str:
        return ui_header(title, subtitle)

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
                                        <div class="metric">
                                            <span class="metric-label">Ofrendas</span>
                                            <span class="metric-value">{{ summary.ofrenda or 0 }}</span>
                                        </div>
                                        <div class="metric">
                                            <span class="metric-label">Diezmo</span>
                                            <span class="metric-value">{{ summary.diezmo or 0 }}</span>
                                        </div>
                                    </div>
                                    <p class="hint">Registro rapido para momentos de alta afluencia.</p>
                                </article>

                                <article class="card">
                                    <h2>Nuevo sobre</h2>
                                    <div id="capture-tab">
                                        <form action="/process" method="post" enctype="multipart/form-data">
                                            <label style="display: block; margin: 2px 0 5px; font-size: 0.83rem; font-weight: 700; color: #0f4a53;">Imagen del sobre</label>
                                            <input
                                                id="image-input"
                                                type="file"
                                                name="image"
                                                accept="image/*"
                                                capture="environment"
                                                required
                                                onchange="const status=document.getElementById('camera-status'); if (this.files && this.files.length > 0) { status.textContent='Procesando captura...'; this.form.submit(); }"
                                                style="position: absolute; left: -9999px; width: 1px; height: 1px; opacity: 0;">
                                            <button type="button" onclick="document.getElementById('image-input').click();" style="width: 100%; margin-top: 4px; padding: 11px 12px; border: 0; border-radius: 12px; color: #fff; font-weight: 800; background: linear-gradient(125deg, #1d4ed8 0%, #2563eb 100%); cursor: pointer;">Abrir camara</button>
                                            <p id="camera-status" class="hint" style="margin-top: 8px; font-size: 0.86rem; color: #5c6675;">Toca Abrir camara para tomar la foto.</p>
                                        </form>
                                        <button type="button" onclick="document.getElementById('manual-tab').style.display='block'; this.style.display='none';" style="width: 100%; margin-top: 12px; padding: 11px 12px; border: 0; border-radius: 12px; color: #fff; font-weight: 800; background: linear-gradient(125deg, #475569 0%, #334155 100%); cursor: pointer;">Manual</button>
                                    </div>

                                    <div id="manual-tab" style="display: none;">
                                        <form method="post" action="/process-manual">
                                            <div style="display: grid; grid-template-columns: 1fr; gap: 8px;">
                                                <div>
                                                    <label>Nombre*</label>
                                                    <input name="member_name" required style="width: 100%; font: inherit; border: 1px solid rgba(31, 42, 55, 0.24); border-radius: 12px; padding: 11px 12px; background: #fff;">
                                                </div>
                                                <div>
                                                    <label>Diezmo</label>
                                                    <input name="diezmo" type="number" step="0.01" style="width: 100%; font: inherit; border: 1px solid rgba(31, 42, 55, 0.24); border-radius: 12px; padding: 11px 12px; background: #fff;">
                                                </div>
                                                <div>
                                                    <label>Ofrenda</label>
                                                    <input name="ofrenda" type="number" step="0.01" style="width: 100%; font: inherit; border: 1px solid rgba(31, 42, 55, 0.24); border-radius: 12px; padding: 11px 12px; background: #fff;">
                                                </div>
                                                <div>
                                                    <label>Primicias</label>
                                                    <input name="primicias" type="number" step="0.01" style="width: 100%; font: inherit; border: 1px solid rgba(31, 42, 55, 0.24); border-radius: 12px; padding: 11px 12px; background: #fff;">
                                                </div>
                                                <div>
                                                    <label>Pro templo</label>
                                                    <input name="pro_templo" type="number" step="0.01" style="width: 100%; font: inherit; border: 1px solid rgba(31, 42, 55, 0.24); border-radius: 12px; padding: 11px 12px; background: #fff;">
                                                </div>
                                                <div>
                                                    <label>Ofrenda misionera</label>
                                                    <input name="ofrenda_misionera" type="number" step="0.01" style="width: 100%; font: inherit; border: 1px solid rgba(31, 42, 55, 0.24); border-radius: 12px; padding: 11px 12px; background: #fff;">
                                                </div>
                                                <div>
                                                    <label>Ofrenda pastoral</label>
                                                    <input name="ofrenda_pastoral" type="number" step="0.01" style="width: 100%; font: inherit; border: 1px solid rgba(31, 42, 55, 0.24); border-radius: 12px; padding: 11px 12px; background: #fff;">
                                                </div>
                                                <div>
                                                    <label>Metodo de pago</label>
                                                    <select name="payment_method" style="width: 100%; font: inherit; border: 1px solid rgba(31, 42, 55, 0.24); border-radius: 12px; padding: 11px 12px; background: #fff;">
                                                        <option value="cash">Efectivo</option>
                                                        <option value="zelle">Zelle</option>
                                                        <option value="check">Cheque</option>
                                                    </select>
                                                </div>
                                            </div>
                                            <button type="submit" style="width: 100%; margin-top: 12px; padding: 11px 12px; border: 0; border-radius: 12px; color: #fff; font-weight: 800; background: linear-gradient(125deg, #15616d 0%, #1f7a7a 100%); cursor: pointer;">Crear sobre</button>
                                        </form>
                                    </div>
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
        if service.should_fallback_to_manual(data):
            data["member_name"] = ""
            data["ocr_manual_fallback"] = True
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

    @app.post("/process-manual")
    def process_manual():
        denied = _require_policy("process_image")
        if denied:
            return denied
        actor = getattr(g, "auth_user_id", None)
        manual_payload = {
            "member_name": request.form.get("member_name", ""),
            "diezmo": request.form.get("diezmo", "0"),
            "ofrenda": request.form.get("ofrenda", "0"),
            "primicias": request.form.get("primicias", "0"),
            "pro_templo": request.form.get("pro_templo", "0"),
            "ofrenda_misionera": request.form.get("ofrenda_misionera", "0"),
            "ofrenda_pastoral": request.form.get("ofrenda_pastoral", "0"),
            "payment_method": request.form.get("payment_method", "cash"),
            "service_date": _current_service_date(),
            "ocr_confidence": "1.0",
            "image_path": "",
        }
        offering = service.build_offering_from_form(manual_payload, actor)
        service.confirm(offering, [])
        return redirect(url_for("day_log", notice="manual_saved"))

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
        notice = (request.args.get("notice") or "").strip().lower()
        return render_template_string(
            """
                        {{ ui_css|safe }}
                        <main class="app-shell">
                            {{ ui_header|safe }}
                            {% if notice == 'manual_saved' %}
                            <div id="toast-manual-saved" style="position: sticky; top: 12px; z-index: 40; margin-bottom: 12px;">
                                <div style="background: linear-gradient(125deg, #0f766e 0%, #0d9488 100%); color: #fff; border-radius: 12px; padding: 10px 12px; font-weight: 700; box-shadow: 0 8px 20px rgba(15, 118, 110, 0.35);">
                                    Sobre manual guardado
                                </div>
                            </div>
                            <script>
                                window.setTimeout(function () {
                                    var toast = document.getElementById('toast-manual-saved');
                                    if (toast) {
                                        toast.style.opacity = '0';
                                        toast.style.transition = 'opacity 220ms ease';
                                        window.setTimeout(function () { toast.remove(); }, 260);
                                    }
                                }, 2500);
                            </script>
                            {% endif %}
                            <section class="card">
                                <ul class="list-clean">
                                {% for row in rows %}
                                    <li class="row-item">
                                        <div class="daylog-entry">
                                            <div class="daylog-header">
                                                <div>
                                                    <div class="row-title">{{ row.member_name or 'Sin nombre' }}</div>
                                                    <div class="daylog-date">{{ row.service_date }}</div>
                                                </div>
                                                <div class="daylog-total">Total: {{ '%.2f'|format((row.total or 0)|float) }}</div>
                                            </div>
                                            <div class="daylog-grid">
                                                <div class="kv"><span class="kv-label">Ofrenda</span><span class="kv-value">{{ '%.2f'|format((row.ofrenda or 0)|float) }}</span></div>
                                                <div class="kv"><span class="kv-label">Diezmo</span><span class="kv-value">{{ '%.2f'|format((row.diezmo or 0)|float) }}</span></div>
                                                <div class="kv"><span class="kv-label">Primicias</span><span class="kv-value">{{ '%.2f'|format((row.primicias or 0)|float) }}</span></div>
                                                <div class="kv"><span class="kv-label">Pro Templo</span><span class="kv-value">{{ '%.2f'|format((row.pro_templo or 0)|float) }}</span></div>
                                                <div class="kv"><span class="kv-label">Misionera</span><span class="kv-value">{{ '%.2f'|format((row.ofrenda_misionera or 0)|float) }}</span></div>
                                                <div class="kv"><span class="kv-label">Pastoral</span><span class="kv-value">{{ '%.2f'|format((row.ofrenda_pastoral or 0)|float) }}</span></div>
                                                <div class="kv" style="grid-column: 1 / -1;"><span class="kv-label">Metodo de pago</span><span class="kv-value">{{ row.payment_method or 'N/A' }}</span></div>
                                            </div>
                                            <div class="row-actions">
                                                <a class="action-pill" href="/review/{{ row.id }}">Revisar</a>
                                            </div>
                                        </div>
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
            notice=notice,
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
        # Normalize user ID to UUID or None
        actor_user_id = getattr(g, "auth_user_id", None)
        if actor_user_id:
            from uuid import UUID
            try:
                actor_user_id = str(UUID(actor_user_id))
            except (ValueError, TypeError):
                actor_user_id = None
        
        ok = storage.update_offering_fields(
            offering_id=offering_id,
            updates=updates,
            changed_by_user_id=actor_user_id,
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

    register_workflow_routes(
        app,
        cash_window_service=cash_window_service,
        outputs_service=outputs_service,
        kiosk_pos_service=kiosk_pos_service,
        require_policy=_require_policy,
        current_service_date=_current_service_date,
        ok_response=_ok_response,
        domain_error_response=_domain_error_response,
        ui_base_css=_ui_base_css,
        ui_header=_ui_header,
    )

    return app


def _review_template() -> str:
    return review_template()


def _configure_logging(app: Flask) -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    app.logger.setLevel(logging.INFO)
