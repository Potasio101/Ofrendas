from datetime import date
import json
import logging
from pathlib import Path
import time

from flask import Flask, jsonify, redirect, render_template_string, request, url_for, g
from werkzeug.utils import secure_filename

from offering_app.repositories.postgresql_repo import PostgreSQLRepo
from offering_app.services.offering_service import OfferingService


def create_app(service: OfferingService, storage: PostgreSQLRepo, upload_path: str) -> Flask:
    app = Flask(__name__)
    app.config["UPLOAD_PATH"] = upload_path
    _configure_logging(app)

    @app.before_request
    def before_request():
        g._request_started_at = time.time()

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
            storage.get_daily_totals(date.today().isoformat())
            return jsonify({"status": "ready"})
        except Exception as exc:
            return jsonify({"status": "not-ready", "error": str(exc)}), 503

    @app.get("/")
    def home():
        summary = service.get_daily_summary(date.today().isoformat())
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
        file = request.files.get("image")
        if not file or file.filename == "":
            return "Image is required", 400

        safe_name = secure_filename(file.filename)
        target = Path(app.config["UPLOAD_PATH"]) / safe_name
        target.parent.mkdir(parents=True, exist_ok=True)
        file.save(target)

        data = service.process_image(str(target))
        return render_template_string(
            _review_template(),
            data=data,
            action=url_for("confirm"),
            title="Revisar Captura",
            offering_id="",
        )

    @app.post("/confirm")
    def confirm():
        actor = request.form.get("actor_user_id")
        offering = service.build_offering_from_form(request.form, actor)
        corrections = service.build_corrections_from_form(request.form)
        offering_id = service.confirm(offering, corrections)
        return redirect(url_for("review_existing", offering_id=offering_id))

    @app.get("/summary")
    def summary():
        data = service.get_daily_summary(date.today().isoformat())
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
        rows = storage.get_by_date(date.today().isoformat())
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
            changed_by_user_id=request.form.get("actor_user_id"),
            reason=request.form.get("reason"),
        )
        if not ok:
            return "Not found", 404
        return redirect(url_for("day_log"))

    return app


def _review_template() -> str:
    return """
    <h1>{{ title }}</h1>
    <form method="post" action="{{ action }}">
      <input type="hidden" name="image_path" value="{{ data.image_path or '' }}">
      <input type="hidden" name="ocr_confidence" value="{{ data.ocr_confidence or 0.5 }}">
      <label>Usuario</label><input name="actor_user_id" placeholder="UUID usuario"><br>
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
