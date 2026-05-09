def ui_base_css() -> str:
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
        .hero-top {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 10px;
        }
        .hero-home {
            display: inline-block;
            text-decoration: none;
            color: #fff;
            border: 1px solid rgba(255, 255, 255, 0.35);
            background: rgba(255, 255, 255, 0.14);
            border-radius: 999px;
            padding: 7px 12px;
            font-size: 0.82rem;
            font-weight: 800;
            white-space: nowrap;
        }
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
        .daylog-entry {
            display: grid;
            gap: 10px;
            width: 100%;
        }
        .daylog-header {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            gap: 10px;
            flex-wrap: wrap;
        }
        .daylog-date {
            color: var(--muted);
            font-size: 0.82rem;
            font-weight: 700;
        }
        .daylog-total {
            font-weight: 800;
            color: var(--brand-strong);
            font-size: 1rem;
        }
        .daylog-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
        }
        .kv {
            border: 1px solid var(--line);
            border-radius: 10px;
            background: rgba(21, 97, 109, 0.06);
            padding: 8px;
        }
        .kv-label {
            display: block;
            color: var(--muted);
            font-size: 0.74rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.2px;
        }
        .kv-value {
            display: block;
            margin-top: 2px;
            font-weight: 800;
            color: var(--ink);
            font-size: 0.96rem;
        }
        .row-actions {
            display: flex;
            justify-content: flex-end;
        }
        .action-pill {
            display: inline-block;
            text-decoration: none;
            color: var(--brand-strong);
            background: rgba(21, 97, 109, 0.1);
            border: 1px solid rgba(21, 97, 109, 0.22);
            border-radius: 999px;
            padding: 8px 12px;
            font-weight: 800;
            font-size: 0.85rem;
        }
        .inline-link { color: var(--brand-strong); text-decoration: none; font-weight: 700; }
        .stack { display: grid; gap: 12px; }
        @media (min-width: 720px) {
            .app-shell { padding: 26px 22px 36px; }
            .section-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .section-grid.full { grid-template-columns: 1fr; }
            .daylog-grid { grid-template-columns: repeat(4, minmax(0, 1fr)); }
        }
    </style>
    """


def ui_header(title: str, subtitle: str) -> str:
    return f"""
    <div class=\"hero\">
        <div class=\"hero-top\">
            <h1>{title}</h1>
            <a class=\"hero-home\" href=\"/\">Inicio</a>
        </div>
        <p>{subtitle}</p>
    </div>
    """


def review_template() -> str:
    return """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap');
            :root {
                --ink: #1f2a37;
                --muted: #5c6675;
                --brand: #15616d;
                --card: rgba(255, 255, 255, 0.9);
                --line: rgba(31, 42, 55, 0.14);
                --warning: #f59e0b;
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
            .warning-box {
                background: rgba(245, 158, 11, 0.1);
                border: 2px solid var(--warning);
                border-radius: 12px;
                padding: 12px;
                margin-bottom: 12px;
                color: #78350f;
            }
            .warning-box strong { color: #92400e; }
            .grid { display: grid; grid-template-columns: 1fr; gap: 10px; }
            @media (min-width: 760px) { .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
            label {
                display: block;
                margin: 2px 0 5px;
                font-size: 0.83rem;
                font-weight: 700;
                color: #0f4a53;
            }
            input, select, button {
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
                cursor: pointer;
            }
            .btn-secondary {
                background: linear-gradient(125deg, #6b7280 0%, #4b5563 100%);
            }
            .meta { margin: 8px 0 0; color: var(--muted); font-size: 0.86rem; }
            .inline-link { display: inline-block; margin-top: 12px; color: #0f4a53; font-weight: 700; text-decoration: none; }
            .button-group { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 12px; }
            .button-group button { margin-top: 0; }
        </style>

        <main class=\"shell\">
            <section class=\"hero\">
                <h1>{{ title }}</h1>
                <p>Ajusta montos, valida metodo de pago y guarda con trazabilidad.</p>
            </section>

            <script>
                function checkIfEmpty() {
                    const name = document.querySelector('input[name=\"member_name\"]');
                    const isEmpty = !name || !name.value || name.value.trim() === '';
                    const emptyBox = document.getElementById('empty-warning');
                    const emptyForm = document.getElementById('empty-form');
                    const filledForm = document.getElementById('filled-form');
                    
                    if (isEmpty && {{ (data.member_name or '') | tojson }}.trim() === '') {
                        if (emptyBox) emptyBox.style.display = 'block';
                        if (emptyForm) emptyForm.style.display = 'block';
                        if (filledForm) filledForm.style.display = 'none';
                    } else {
                        if (emptyBox) emptyBox.style.display = 'none';
                        if (emptyForm) emptyForm.style.display = 'none';
                        if (filledForm) filledForm.style.display = 'block';
                    }
                }
                window.addEventListener('load', checkIfEmpty);
            </script>

            {% if not data.member_name or data.member_name.strip() == '' %}
            <section class=\"card\">
                <div id=\"empty-warning\" class=\"warning-box\">
                    <strong>⚠️ La captura no tiene datos</strong><br/>
                    El OCR no pudo leer la foto con precision. Puedes rellenar los campos manualmente.<br/>
                    <span style=\"font-size: 0.82rem;\">OCR confidence detectada: {{ data.ocr_confidence or 0.5 }}</span>
                </div>

                <form id=\"empty-form\" method=\"post\" action=\"/confirm\">
                    <input type=\"hidden\" name=\"image_path\" value=\"{{ data.image_path or '' }}\">
                    <input type=\"hidden\" name=\"ocr_confidence\" value=\"{{ data.ocr_confidence or 0.5 }}\">

                    <div class=\"grid\">
                        <div>
                            <label>Nombre*</label>
                            <input name=\"member_name\" required>
                        </div>
                        <div>
                            <label>Fecha</label>
                            <input name=\"service_date\" value=\"{{ data.service_date or '' }}\">
                        </div>
                        <div>
                            <label>Diezmo</label>
                            <input name=\"diezmo\" type=\"number\" step=\"0.01\" value=\"0\">
                        </div>
                        <div>
                            <label>Ofrenda</label>
                            <input name=\"ofrenda\" type=\"number\" step=\"0.01\" value=\"0\">
                        </div>
                        <div>
                            <label>Primicias</label>
                            <input name=\"primicias\" type=\"number\" step=\"0.01\" value=\"0\">
                        </div>
                        <div>
                            <label>Pro templo</label>
                            <input name=\"pro_templo\" type=\"number\" step=\"0.01\" value=\"0\">
                        </div>
                        <div>
                            <label>Ofrenda misionera</label>
                            <input name=\"ofrenda_misionera\" type=\"number\" step=\"0.01\" value=\"0\">
                        </div>
                        <div>
                            <label>Ofrenda pastoral</label>
                            <input name=\"ofrenda_pastoral\" type=\"number\" step=\"0.01\" value=\"0\">
                        </div>
                        <div>
                            <label>Metodo de pago</label>
                            <select name=\"payment_method\">
                                <option value=\"cash\">Efectivo</option>
                                <option value=\"zelle\">Zelle</option>
                                <option value=\"check\">Cheque</option>
                            </select>
                        </div>
                        {% if offering_id %}
                        <div>
                            <label>Motivo</label>
                            <input name=\"reason\" value=\"\">
                        </div>
                        {% endif %}
                    </div>

                    <div class=\"button-group\">
                        <button type=\"submit\">✓ Guardar</button>
                        <a href=\"/\" style=\"display: flex; align-items: center; justify-content: center; text-decoration: none; color: white; background: linear-gradient(125deg, #6b7280 0%, #4b5563 100%); border-radius: 12px; font-weight: 800;\">← Volver</a>
                    </div>
                </form>
            </section>
            {% else %}
            <section class=\"card\" id=\"filled-form\">
                <form method=\"post\" action=\"{{ action }}\">
                    <input type=\"hidden\" name=\"image_path\" value=\"{{ data.image_path or '' }}\">
                    <input type=\"hidden\" name=\"ocr_confidence\" value=\"{{ data.ocr_confidence or 0.5 }}\">

                    <div class=\"grid\">
                        <div>
                            <label>Nombre</label>
                            <input name=\"member_name\" value=\"{{ data.member_name or '' }}\">
                        </div>
                        <div>
                            <label>Fecha</label>
                            <input name=\"service_date\" value=\"{{ data.service_date or '' }}\">
                        </div>
                        <div>
                            <label>Diezmo</label>
                            <input name=\"diezmo\" value=\"{{ data.diezmo or 0 }}\">
                        </div>
                        <div>
                            <label>Ofrenda</label>
                            <input name=\"ofrenda\" value=\"{{ data.ofrenda or 0 }}\">
                        </div>
                        <div>
                            <label>Primicias</label>
                            <input name=\"primicias\" value=\"{{ data.primicias or 0 }}\">
                        </div>
                        <div>
                            <label>Pro templo</label>
                            <input name=\"pro_templo\" value=\"{{ data.pro_templo or 0 }}\">
                        </div>
                        <div>
                            <label>Ofrenda misionera</label>
                            <input name=\"ofrenda_misionera\" value=\"{{ data.ofrenda_misionera or 0 }}\">
                        </div>
                        <div>
                            <label>Ofrenda pastoral</label>
                            <input name=\"ofrenda_pastoral\" value=\"{{ data.ofrenda_pastoral or 0 }}\">
                        </div>
                        <div>
                            <label>Metodo de pago</label>
                            <input name=\"payment_method\" value=\"{{ data.payment_method or 'cash' }}\">
                        </div>
                        {% if offering_id %}
                        <div>
                            <label>Motivo</label>
                            <input name=\"reason\" value=\"\">
                        </div>
                        {% endif %}
                    </div>

                    <button type=\"submit\">Guardar</button>
                    <p class=\"meta\">OCR confidence: {{ data.ocr_confidence or 0.5 }}</p>
                </form>
                <a class=\"inline-link\" href=\"/\">Volver al inicio</a>
            </section>
            {% endif %}
        </main>
    """
