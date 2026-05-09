from typing import Callable

from flask import Flask, jsonify, render_template_string, request, g


def register_workflow_routes(
    app: Flask,
    *,
    cash_window_service,
    outputs_service,
    kiosk_pos_service,
    require_policy: Callable[[str], tuple[str, int] | None],
    current_service_date: Callable[[], str],
    ok_response: Callable,
    domain_error_response: Callable,
    ui_base_css: Callable[[], str],
    ui_header: Callable[[str, str], str],
) -> None:
    @app.get("/workflow/cash")
    def workflow_cash_view():
        denied = require_policy("workflow_cash_view")
        if denied:
            return denied
        service_date = current_service_date()
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
            ui_css=ui_base_css(),
            ui_header=ui_header("Cash Workflow", "Control de caja por flujo guiado y listo para movil."),
        )

    @app.get("/workflow/outputs")
    def workflow_outputs_view():
        denied = require_policy("workflow_outputs_view")
        if denied:
            return denied
        output_date = current_service_date()
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
            ui_css=ui_base_css(),
            ui_header=ui_header("Outputs Workflow", "Registro de salidas con base operativa y control de estados."),
        )

    @app.get("/workflow/kiosk")
    def workflow_kiosk_view():
        denied = require_policy("workflow_kiosk_view")
        if denied:
            return denied
        service_date = current_service_date()
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
            ui_css=ui_base_css(),
            ui_header=ui_header("Kiosk Workflow", "POS rapido para cash y zelle con items custom."),
        )

    @app.post("/cash-window/open")
    def cash_window_open():
        denied = require_policy("cash_window_open")
        if denied:
            return denied
        session = cash_window_service.open_session(
            service_date=request.form.get("service_date", current_service_date()),
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
        return ok_response({"session": session, "transition": transition}, "Cash session opened", status_code)

    @app.get("/cash-window")
    def cash_window_get():
        denied = require_policy("cash_window_get")
        if denied:
            return denied
        service_date = request.args.get("service_date", current_service_date())
        session = cash_window_service.get_session(service_date)
        if not session:
            return jsonify({"status": "not-found", "service_date": service_date}), 404
        return ok_response({"session": session}, "Cash session fetched")

    @app.post("/cash-window/line")
    def cash_window_line():
        denied = require_policy("cash_window_line")
        if denied:
            return denied
        try:
            session = cash_window_service.upsert_line(
                service_date=request.form.get("service_date", current_service_date()),
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
            return ok_response({"session": session, "transition": transition}, "Cash line updated")
        except ValueError as exc:
            return domain_error_response(exc)

    @app.post("/cash-window/close")
    def cash_window_close():
        denied = require_policy("cash_window_close")
        if denied:
            return denied
        try:
            session = cash_window_service.close_session(
                service_date=request.form.get("service_date", current_service_date()),
                actor_user_id=getattr(g, "auth_user_id", None),
                notes=request.form.get("notes"),
            )
            transition = {
                "entity": "cash_session",
                "action": "close",
                "from_status": "open",
                "to_status": session.get("session_status", "closed"),
            }
            return ok_response({"session": session, "transition": transition}, "Cash session closed")
        except ValueError as exc:
            return domain_error_response(exc)

    @app.post("/cash-window/reopen")
    def cash_window_reopen():
        denied = require_policy("cash_window_reopen")
        if denied:
            return denied
        try:
            session = cash_window_service.reopen_session(
                service_date=request.form.get("service_date", current_service_date()),
                actor_user_id=getattr(g, "auth_user_id", None),
                reason=request.form.get("reason"),
            )
            transition = {
                "entity": "cash_session",
                "action": "reopen",
                "from_status": "closed",
                "to_status": session.get("session_status", "open"),
            }
            return ok_response({"session": session, "transition": transition}, "Cash session reopened")
        except ValueError as exc:
            return domain_error_response(exc)

    @app.post("/outputs/draft")
    def outputs_create_draft():
        denied = require_policy("outputs_create_draft")
        if denied:
            return denied
        description = request.form.get("description", "").strip()
        amount_raw = request.form.get("amount", "").strip()
        if not description:
            return jsonify({"status": "error", "error": "invalid_payload", "message": "Description is required"}), 400
        if not amount_raw:
            return jsonify({"status": "error", "error": "invalid_payload", "message": "Amount is required"}), 400
        payload = {
            "output_date": request.form.get("output_date", current_service_date()),
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
        return ok_response({"disbursement": row, "transition": transition}, "Disbursement draft created", 201)

    @app.get("/outputs/drafts")
    def outputs_list_drafts():
        denied = require_policy("outputs_list_drafts")
        if denied:
            return denied
        rows = outputs_service.list_drafts(request.args.get("output_date"))
        return ok_response({"items": rows}, "Disbursement drafts fetched")

    @app.post("/outputs/<disbursement_id>/update")
    def outputs_update_draft(disbursement_id: str):
        denied = require_policy("outputs_update_draft")
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
            return ok_response({"disbursement": row, "transition": transition}, "Disbursement draft updated")
        except ValueError as exc:
            return domain_error_response(exc)

    @app.post("/outputs/<disbursement_id>/submit")
    def outputs_submit(disbursement_id: str):
        denied = require_policy("outputs_submit")
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
            return ok_response({"disbursement": row, "transition": transition}, "Disbursement submitted")
        except ValueError as exc:
            return domain_error_response(exc)

    @app.post("/outputs/<disbursement_id>/approve")
    def outputs_approve(disbursement_id: str):
        denied = require_policy("outputs_approve")
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
            return ok_response({"disbursement": row, "transition": transition}, "Disbursement approved")
        except ValueError as exc:
            return domain_error_response(exc)

    @app.post("/outputs/<disbursement_id>/pay")
    def outputs_pay(disbursement_id: str):
        denied = require_policy("outputs_pay")
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
            return ok_response({"disbursement": row, "transition": transition}, "Disbursement paid")
        except ValueError as exc:
            return domain_error_response(exc)

    @app.post("/kiosk/order/open")
    def kiosk_open_order():
        denied = require_policy("kiosk_open_order")
        if denied:
            return denied
        order = kiosk_pos_service.get_or_create_open_order(
            service_date=request.form.get("service_date", current_service_date()),
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
        return ok_response({"order": order, "transition": transition}, "Kiosk order opened", status_code)

    @app.get("/kiosk/items")
    def kiosk_items():
        denied = require_policy("kiosk_list_items")
        if denied:
            return denied
        items = kiosk_pos_service.list_items(active_only=request.args.get("active_only", "1") != "0")
        return ok_response({"items": items}, "Kiosk items fetched")

    @app.post("/kiosk/order/line/catalog")
    def kiosk_add_catalog_line():
        denied = require_policy("kiosk_add_catalog_line")
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
            return ok_response({"order": order, "transition": transition}, "Catalog line added")
        except ValueError as exc:
            return domain_error_response(exc)

    @app.post("/kiosk/order/line/custom")
    def kiosk_add_custom_line():
        denied = require_policy("kiosk_add_custom_line")
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
            return ok_response({"order": order, "transition": transition}, "Custom line added")
        except ValueError as exc:
            return domain_error_response(exc)

    @app.post("/kiosk/order/pay")
    def kiosk_pay_order():
        denied = require_policy("kiosk_pay_order")
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
            return ok_response({"payment": result.get("payment"), "order": result.get("order"), "transition": transition}, "Kiosk order paid")
        except ValueError as exc:
            return domain_error_response(exc)
