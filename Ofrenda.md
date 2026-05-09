# App de Ofrendas — LLM Prompt Plan v1.0
**SOLID + Strategy Pattern · Python · Flask · EasyOCR · PostgreSQL**, TDD

> Scope update (Mayo 2026): PostgreSQL es la fuente de verdad operativa. SharePoint queda fuera del alcance actual y se considera solo como destino de export futuro opcional.

---

## ¿Por qué SOLID + Strategy?

Sin arquitectura, si el OCR cambia de EasyOCR a Tesseract, o el backend de datos evoluciona en el futuro, todo el código colapsa. Con SOLID + Strategy, cambias una pieza sin tocar nada más.

---

## Principios SOLID Aplicados

### S — Single Responsibility
Una clase, una razón para cambiar. Cada clase hace UNA sola cosa.
```
ImageProcessor  → solo limpia imagen
OCRReader       → solo lee texto
OfferingRepository → solo guarda datos
```

### O — Open/Closed
Abierto para extender, cerrado para modificar. Añadir un nuevo tipo de ofrenda NO modifica el código existente.
```
TitheStrategy, OfferingStrategy, TalentoStrategy, OfrendaDeAmorStrategy, MissionStrategy
→ agregar MissionStrategy sin tocar nada existente
```

### L — Liskov Substitution
Subclases intercambiables. EasyOCRReader y TesseractReader implementan la misma interfaz.
```
OCRStrategy → EasyOCRStrategy
OCRStrategy → TesseractStrategy
El sistema no nota el cambio
```

### I — Interface Segregation
Interfaces pequeñas y específicas. No forzar métodos innecesarios.
```
IReader     → solo read()
ICorrector  → solo correct()
IStorage    → solo save()
```

### D — Dependency Inversion
Depende de abstracciones, no implementaciones.
```
OfferingService(repo: IStorage)
→ PostgreSQLStorage ✅
→ LocalFileStorage  ✅ (mismo código)
```

---

## Strategy Pattern — El Corazón del Sistema

| Strategy | Hoy | Mes 2 | Futuro |
|---|---|---|---|
| **OCR** | EasyOCR | EasyOCR entrenado | Azure AI |
| **Storage** | PostgreSQL | PostgreSQL | PostgreSQL + export adapters |
| **Correction** | Fuzzy Matching | Modelo entrenado | LLM |

> Mismo contrato, distinta implementación. Cero cambios en la lógica de negocio.

---

## Arquitectura

```
📱 UI Flask
    ↓
OfferingService
    ├── OCRStrategy         → EasyOCRStrategy
    ├── CorrectionStrategy  → FuzzyStrategy
  ├── IStorageRepo        → PostgreSQLRepo
    └── ITrainingRepo       → TrainingDataRepo

ImageProcessor (OpenCV: limpia, recorta, endereza)
```

---

## Estructura de Carpetas

```
offering_app/
│
├── interfaces/                  # D de SOLID — abstracciones
│   ├── i_ocr_strategy.py        # → read(image) -> dict
│   ├── i_correction_strategy.py # → correct(text, field, members) -> tuple
│   ├── i_storage_repo.py        # → save(offering) -> bool
│   └── i_training_repo.py       # → save_correction(data) -> bool
│
├── strategies/                  # Strategy Pattern
│   ├── easyocr_strategy.py      # OCR con EasyOCR
│   ├── fuzzy_correction.py      # Corrección con FuzzyWuzzy
│   └── trained_correction.py    # Mes 2: modelo entrenado (stub por ahora)
│
├── repositories/                # Storage intercambiable
│   ├── postgresql_repo.py       # Guarda en PostgreSQL
│   ├── local_export_repo.py     # Destino local de export en MVP
│   └── training_repo.py         # Guarda training data
│
├── services/                    # Lógica de negocio
│   ├── offering_service.py      # Orquesta todo el flujo
│   ├── image_processor.py       # OpenCV: limpia imagen
│   └── training_job.py          # Job nocturno 11 PM
│
├── models/                      # Entidades del dominio
│   ├── offering.py              # Dataclass Offering
│   └── correction.py            # Dataclass Correction
│
├── ui/                          # Flask app del tesorero
│   ├── app.py                   # Routes Flask
│   └── templates/               # HTML mobile-first
│
├── config.py                    # Coordenadas sobre, paths
├── main.py                      # Wiring + arranque
├── scheduler.py                 # Job 11 PM APScheduler
├── requirements.txt
└── .env.example
```

---

## Prompts para Claude — Paso a Paso

> **Instrucción:** Usa estos prompts en orden. Cada prompt construye sobre el anterior. Pega el código generado antes de continuar al siguiente.

---

### PROMPT 1 — Interfaces y Modelos

```
Eres un arquitecto de software senior. Crea las interfaces y modelos base
para una app de digitalización de sobres de ofrenda de iglesia usando
Python y principios SOLID.

Crea exactamente estos archivos:

models/offering.py
→ Dataclass con campos: nombre, diezmo, ofrenda, primicias, pro_templo,
  ofrenda_misionera, ofrenda_pastoral, fecha, metodo_pago, total

models/correction.py
→ Dataclass con campos: imagen_path, campo, ocr_leyo, correcto,
  confianza, fecha, domingo_num

interfaces/i_ocr_strategy.py
→ ABC con método abstracto: read(image: np.ndarray) -> dict

interfaces/i_correction_strategy.py
→ ABC con método abstracto:
  correct(text: str, field: str, members: list) -> tuple[str, float]

interfaces/i_storage_repo.py
→ ABC con métodos:
  save(offering: Offering) -> bool
  get_by_date(date: str) -> list

interfaces/i_training_repo.py
→ ABC con método: save_correction(correction: Correction) -> bool

Usa type hints completos. Incluye docstrings. Respeta Single Responsibility
— cada archivo una sola responsabilidad.
```

---

### PROMPT 2 — Strategy: OCR + Corrección

```
Usando las interfaces del paso anterior, crea las implementaciones
Strategy concretas:

strategies/easyocr_strategy.py
→ Implementa IOCRStrategy. Usa EasyOCR para leer texto de imagen numpy.
  El método read() retorna dict con todos los campos del sobre.
  Maneja excepciones con confianza mínima de 0.5.

strategies/fuzzy_correction.py
→ Implementa ICorrectionStrategy. Usa FuzzyWuzzy process.extractOne()
  para nombres. Para montos usa regex para limpiar caracteres no numéricos.
  Retorna tuple (texto_corregido, confianza_float).

strategies/trained_correction.py
→ Implementa ICorrectionStrategy. Por ahora es un STUB que delega a
  FuzzyCorrection. Comentar claramente dónde se cargará el modelo
  entrenado en el Mes 2.

Aplica Open/Closed — estas clases NO modifican las interfaces.
Si no hay modelo entrenado, el sistema cae back al fuzzy automáticamente.
```

---

### PROMPT 3 — ImageProcessor + Coordenadas

```
Crea services/image_processor.py siguiendo Single Responsibility
— SOLO procesa imágenes, no sabe nada de OCR ni storage.

La clase ImageProcessor debe tener estos métodos:

clean(image) -> np.ndarray
→ convierte a escala de grises, aumenta contraste con CLAHE,
  elimina ruido con fastNlMeans, endereza con detección de ángulo

crop_field(image, field_name: str) -> np.ndarray
→ recorta zona del campo usando coordenadas de config.py

crop_all_fields(image) -> dict[str, np.ndarray]
→ retorna dict con imagen recortada de cada campo

Crea config.py con las coordenadas de cada campo del sobre de la
Iglesia de Dios de la Profecía. Campos: nombre, diezmo, ofrenda,
primicias, pro_templo, ofrenda_misionera, ofrenda_pastoral,
fecha, metodo_pago.

Usa coordenadas relativas (porcentaje del ancho/alto) para que funcione
con fotos de distintos tamaños.
```

---

### PROMPT 4 — Repositories

```
Crea los repositorios implementando IStorageRepo e ITrainingRepo:

repositories/postgresql_repo.py
→ Implementa IStorageRepo. Usa PostgreSQL para persistencia operativa.
  Método save() guarda la ofrenda en tablas transaccionales.
  Método get_by_date() filtra por columna fecha.
  Usa variables de entorno para conexión — nunca hardcoded.

repositories/training_repo.py
→ Implementa ITrainingRepo. Guarda en almacenamiento local configurable:
  imagen recortada como .jpg en /training-data/YYYY-MM-DD/
  metadata en JSON: { imagen_path, campo, ocr_leyo, correcto,
  confianza, timestamp }

repositories/local_export_repo.py
→ Implementa repositorio de salida local para exportes y evidencias del MVP.

Aplica Dependency Inversion — los repos dependen de las interfaces,
no al revés.
```

---

### PROMPT 5 — OfferingService (Orquestador)

```
Crea services/offering_service.py — el orquestador central.
Debe recibir todo por inyección de dependencias en el constructor:

OfferingService(
  ocr: IOCRStrategy,
  corrector: ICorrectionStrategy,
  storage: IStorageRepo,
  training: ITrainingRepo,
  processor: ImageProcessor,
  members: list[str]
)

Métodos requeridos:

process_image(image_path: str) -> dict
→ limpia imagen → recorta campos → OCR lee → corrector mejora
→ retorna resultado para mostrar al tesorero

confirm(offering: Offering, corrections: list[Correction]) -> bool
→ guarda ofrenda en storage + guarda correcciones en training repo

get_daily_summary(date: str) -> dict
→ totales del día por tipo de ofrenda

Este servicio NO sabe si el OCR es EasyOCR o Tesseract.
NO sabe si el storage es PostgreSQL o cualquier backend compatible.
Solo conoce las interfaces.
Así cumple Dependency Inversion y es completamente testeable.
```

---

### PROMPT 6 — Flask UI del Tesorero

```
Crea ui/app.py con Flask y el HTML completo de la app del tesorero.
La UI debe ser mobile-first (el tesorero usa celular).

Pantallas requeridas:

GET /
→ Pantalla inicio con contador de sobres del día
  y botón "📸 Nuevo Sobre"
  y botón "💵 Ventana Cash"

GET /day-log
→ Lista de sobres ingresados en el dia (filtros por estado, usuario, hora)
  con acceso a detalle para auditar y corregir despues

GET /cash
→ Ventana de cash del dia con:
  - total esperado en efectivo
  - conteo por denominaciones
  - diferencia (sobrante/faltante)
  - estado de caja (abierta/cerrada)

GET /kiosk
→ Ventana Kiosk/POS para la tiendita:
  - agregar items al ticket
  - cantidad por item
  - total del ticket
  - metodo de pago: `cash` o `zelle`

POST /kiosk/order
→ Crea orden del kiosk con lineas (item, quantity, unit_price)

POST /kiosk/payment
→ Registra pago del ticket:
  - `cash`: monto recibido y cambio
  - `zelle`: nombre del pagador (buscar en lista o crear si no existe)

GET /kiosk/history
→ Historial del dia (ventas, metodo de pago, usuario, hora)

GET /outputs
→ Ventana de salidas/desembolsos del dia:
  - listado de pagos realizados
  - monto total de salidas
  - filtro por fondo origen (catalogo configurable)

POST /outputs/create
→ Registra una salida (ej. pago agua, ayuda/ofrenda a persona, compras)
  con motivo, monto, fondo origen y responsable

POST /outputs/approve
→ Marca salida como aprobada/pagada con trazabilidad de usuario

GET /outputs/fund-sources
→ Lista fondos origen configurados (activos/inactivos)

POST /outputs/fund-sources
→ Crea nuevo fondo origen (ej. `misiones`, `construccion`, `social`)

POST /outputs/fund-sources/<code>/deactivate
→ Desactiva fondo sin borrar historial

POST /cash/save
→ Guarda conteo parcial o final de cash, con auditoria de cambios

POST /cash/close
→ Cierra caja del dia y registra responsable de cierre

POST /process
→ Recibe foto, llama offering_service.process_image(),
  muestra resultado al tesorero

GET /review
→ Muestra campos detectados:
  - Nombre: dropdown de 200 miembros
  - Montos: inputs numéricos con teclado numérico
  - Botones: "✅ Confirmar" y "✏️ Corregir"

GET /review/<offering_id>
→ Reabrir un sobre del dia para correccion diferida de campos no corregidos
  en el momento de captura

POST /review/<offering_id>/save
→ Guarda cambios de correccion diferida y registra auditoria por campo

POST /confirm
→ Llama offering_service.confirm()
  redirige a inicio con contador actualizado

GET /summary
→ Resumen del día para el pastor

El HTML debe ser limpio, sin frameworks CSS pesados.
Fuente grande para fácil lectura. Botones grandes para dedos.
Sin complicaciones visuales — el tesorero solo necesita que funcione.

Requisito critico:

- Cada edicion posterior debe registrar: usuario, campo, valor anterior,
  valor nuevo, timestamp y motivo (opcional).
- Cierre de cash debe registrar: usuario, monto esperado, monto contado,
  diferencia, timestamp y observacion.
- Kiosk debe permitir crear items custom desde UI sin desplegar codigo.
- Toda salida debe registrar: motivo, fondo origen, monto, usuario y evidencia.
- `fund_source` debe ser extensible sin cambios de codigo/migracion.
```

---

### PROMPT 7 — Job Nocturno de Training

```
Crea services/training_job.py — el job nocturno que corre a las 11 PM.

Clase TrainingJob con método run(date: str) que:
1. Lee todas las correcciones del día desde el training repo
2. Las formatea como pares (imagen, etiqueta) para fine-tuning
3. Si hay más de 10 correcciones nuevas: ejecuta fine-tune de EasyOCR
4. Guarda el modelo actualizado en almacenamiento local configurable
5. Registra métricas: total correcciones, precisión antes vs después
6. Si fine-tune falla: el sistema queda con el modelo anterior
   (nunca se rompe)

Crea también scheduler.py usando APScheduler para registrar el job
a las 23:00 todos los domingos.
Debe correr como proceso separado del servidor Flask.
```

---

### PROMPT 8 — Wiring + main.py

```
Crea main.py — el punto de entrada que conecta todo usando
inyección de dependencias manual.

Debe:
1. Cargar lista de miembros desde PostgreSQL (o CSV de fallback)
2. Instanciar estrategias: EasyOCRStrategy, FuzzyCorrection
3. Instanciar repositorios: PostgreSQLRepo, TrainingRepo
4. Instanciar ImageProcessor
5. Inyectar todo en OfferingService
6. Pasar el service a la Flask app
7. Arrancar Flask: debug=False, host='0.0.0.0', port=5000

Crear requirements.txt con todas las dependencias y versiones exactas.
Crear .env.example con todas las variables de entorno necesarias
(sin valores reales).

Al final muestra cómo cambiar de EasyOCR a Tesseract en UNA sola línea
cambiando solo la estrategia en main.py — esto demuestra que el
Strategy Pattern funciona correctamente.
```

---

## Orden de Ejecución

| # | Prompt | Por qué primero |
|---|---|---|
| 1 | Interfaces y Modelos | La base de todo. Sin esto nada compila |
| 2 | Strategies OCR + Corrección | Las implementaciones que el servicio usará |
| 3 | ImageProcessor + Config | Aquí defines coordenadas del sobre real |
| 4 | Repositories | Define persistencia en PostgreSQL y export local para MVP |
| 5 | OfferingService | El orquestador. Aquí se conecta todo |
| 6 | Flask UI | Lo que verá el tesorero en su celular |
| 7 | Training Job | El ciclo de aprendizaje nocturno automático |
| 8 | Wiring Final | Conecta todo y arranca el sistema |

---

## Lo que demuestra que el Strategy Pattern funciona

```python
# main.py — Cambiar de EasyOCR a Tesseract en UNA línea:

# Hoy:
ocr = EasyOCRStrategy()

# Mañana:
ocr = TesseractStrategy()   # ← una sola línea, nada más cambia

# El resto del sistema no se toca ✅
service = OfferingService(ocr=ocr, ...)
```

---

## Review de Arquitectura (Local Ahora, Produccion Futuro)

### Hallazgos Criticos

1. Falta una estrategia formal de entornos (local/dev/staging/prod). Hoy el documento define componentes, pero no define como se ejecutan por ambiente.
2. Falta una estrategia de despliegue de produccion (WSGI, reverse proxy, workers, health checks, rollback).
3. Falta cerrar una estrategia clara para destinos de export opcionales en MVP y futuro.
4. No hay observabilidad operativa definida (logs estructurados, metricas, alertas, trazabilidad por sobre).
5. Falta una ruta de evolucion de capacidad (usuarios, sobres por dia, limites de latencia).

### Supuestos de Escala (para decisiones actuales)

- Sobres por semana: 30-40
- Dias operativos: martes, jueves y domingo
- Usuarios concurrentes: 1-3 (tesorero y respaldo)
- Presupuesto inicial: cero o muy bajo (preferencia por stack self-hosted)
- Capacidades del equipo: Linux + Docker + Cloud + M365

### Decision de Contexto Confirmado (Mayo 2026)

Para esta escala y presupuesto, la arquitectura recomendada es:

1. Monolito Flask en Docker (sin microservicios por ahora).
2. Publicacion segura con Cloudflare Tunnel (sin exponer puertos publicos).
3. PostgreSQL como repositorio principal y export local configurable en MVP.
4. Entrenamiento OCR en maquina local con GPU, desacoplado del servicio web.

Si estos supuestos cambian, actualizar ADRs y topologia.

---

## Runbook de Desarrollo Local

### Objetivo

Poder levantar el sistema en laptop con PostgreSQL como base operativa unica para el ciclo basico de desarrollo.

### Perfil de ejecucion local

- OCR: `EasyOCRStrategy`
- Correccion: `FuzzyCorrection`
- Storage principal: `PostgreSQLRepo`
- Training repo: carpeta local `./data/training`
- Flask: modo debug solo en local

### Variables de entorno (local)

Archivo `.env` (ejemplo):

```env
APP_ENV=local
FLASK_DEBUG=true
HOST=127.0.0.1
PORT=5000

OCR_STRATEGY=easyocr
CORRECTION_STRATEGY=fuzzy

STORAGE_BACKEND=postgresql
DATABASE_URL=postgresql://ofrendas:ofrendas@localhost:5432/ofrendas

TRAINING_BACKEND=local
TRAINING_PATH=./data/training
LOCAL_EXPORT_PATH=./data/exports
```

### Comandos recomendados

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

### Alternativa local recomendada con Docker

```bash
docker compose up --build
```

Este modo evita diferencias de entorno y prepara el salto a produccion.

### Validacion minima local

1. Subir foto de sobre y verificar OCR de campos.
2. Corregir nombre y confirmar guardado.
3. Validar que el Excel local recibe la fila.
4. Ejecutar resumen diario y validar totales.

---

## Runbook de Produccion (Roadmap)

### Objetivo

Operacion estable, segura y auditable para uso semanal continuo.

### Topologia objetivo (fase 1)

```text
Usuario movil
  -> Cloudflare Edge (WAF basico + TLS)
    -> Cloudflare Tunnel (cloudflared en host Docker)
      -> Gunicorn + Flask (1-2 workers)
        -> OfferingService
          -> OCR/Correction strategies
          -> PostgreSQLRepo (principal)
          -> LocalExportRepo (destino de export opcional)

APScheduler/TrainingJob corre como proceso separado
Training OCR pesado corre en host GPU local (job manual o programado)
```

### Perfil de ejecucion produccion

- `FLASK_DEBUG=false`
- Servidor WSGI: Gunicorn
- Ingreso publico: Cloudflare Tunnel
- Secretos via variables de entorno seguras (no `.env` en servidor)
- Logs JSON con `request_id`, `image_id`, `member`, `status`, `latency_ms`
- Base del stack: Docker Compose (host Linux)
- Base de reportes y consultas de app: PostgreSQL

### Controles de seguridad minimos

1. Validar tamano/tipo MIME de imagen antes de procesar.
2. Sanitizar nombres de archivo y bloquear path traversal.
3. Limitar intentos por IP y por sesion (rate-limit en Cloudflare).
4. Guardar secretos solo en vault o secret manager.
5. Cifrado en transito (TLS) y en reposo (PostgreSQL/almacen local).
6. Restringir acceso administrativo con Cloudflare Access (email allowlist).

### Confiabilidad y fallback

1. Reintentos exponenciales para escritura en destino de export opcional.
2. Si un destino de export falla: escribir en cola local durable y reintentar async.
3. Health endpoint `/healthz` y readiness `/readyz`.
4. Backup diario de datos de ofrendas y training metadata.

### Observabilidad minima

- Metricas:
  - `ocr_processing_seconds`
  - `ocr_confidence_avg`
  - `offering_confirm_success_total`
  - `export_write_fail_total`
- Alertas:
  - error rate > 5% en 15 min
  - latencia p95 > 4s
  - fallas continuas de export > 10 min

### Capacidad objetivo para esta fase

- SLO inicial: disponibilidad 99% mensual.
- Latencia objetivo en `/process`: p95 < 5s con imagen de movil normal.
- Capacidad esperada: hasta 100 sobres/semana sin cambios estructurales.

### Cadencia operativa recomendada

1. Operacion activa: martes, jueves y domingo.
2. Reconciliacion de exportes pendientes: cada madrugada.
3. Entrenamiento OCR (si aplica): lunes en ventana de baja carga.
4. Backup y verificacion de restore: semanal.

---

## Roles y Permisos (Confirmado)

Modelo RBAC aceptado:

1. Tesorero: crear, corregir y confirmar sobres.
2. Admin: gestionar usuarios, parametros de sistema, exportaciones y reconciliacion.
3. Auditor: solo lectura de registros, historial de cambios, reportes y evidencias.

Reglas minimas:

- Todas las confirmaciones deben registrar `user_id`, timestamp y origen.
- Acciones administrativas requieren autenticacion reforzada.
- Auditor no puede editar ni eliminar registros.
- Correcciones diferidas solo por `treasurer` y `admin`; `auditor` solo lectura.
- Apertura/cierre de caja: solo `treasurer` y `admin`; `auditor` solo lectura.
- Salidas (`outputs`): crear por `treasurer`, aprobar por `admin` (recomendado).

---

## Control de Salidas (Outputs)

### Objetivo

Registrar dinero que sale de caja (pagos, ayudas, compras operativas) con
trazabilidad completa y distincion por fondo de origen.

### Casos comunes

1. Pago a quien trae agua.
2. Ofrenda/ayuda entregada a una persona.
3. Compra de insumos menores.

### Campos minimos por salida

- `output_date`
- `category` (`operational`, `benevolence`, `reimbursement`, `other`)
- `description`
- `amount`
- `fund_source` (catalogo configurable; inicial: `offering`, `tithe`, `other`)
- `beneficiary_name` (si aplica)
- `created_by_user_id`
- `approved_by_user_id` (si aplica)

### Politica de fondos (flexible)

Como aun no esta cerrada la politica de diezmo, el sistema debe manejarlo
configurable:

1. Permitir seleccionar fondo origen en cada salida.
2. Marcar por defecto `offering` para gastos operativos.
3. Requerir justificacion adicional cuando el fondo origen sea `tithe`.
4. Permitir auditoria y reporte separado por fondo.
5. Permitir agregar nuevos fondos desde UI (sin despliegue).

### Reglas de negocio

1. No permitir salidas con monto <= 0.
2. No permitir aprobar una salida sin usuario aprobador.
3. Toda edicion de salida debe crear evento de auditoria.
4. Perfil `auditor` solo lectura.
5. No permitir borrar fondos en uso; solo `deactivate`.

---

## Estrategia de Exportaciones Contables

### Objetivo

Exportar ofrendas a sistemas contables sin acoplar la logica de negocio a un solo proveedor.

### Patron recomendado

Agregar una nueva familia de estrategias:

```text
IExportStrategy
  -> QuickBooksExportStrategy
  -> XeroExportStrategy
  -> ZohoBooksExportStrategy
  -> SageExportStrategy
  -> GenericCsvExportStrategy
```

### Formatos de salida iniciales

1. QuickBooks Online: CSV mapeado a chart of accounts.
2. QuickBooks Desktop: IIF (cuando sea requerido por la iglesia).
3. Xero/Zoho/Sage: CSV configurable por plantilla.
4. Export universal: CSV canonico (respaldo y migracion).

### Flujo recomendado

1. Confirmacion de sobre guarda en PostgreSQL.
2. Proceso de export genera archivo por periodo (dia/semana/mes).
3. Archivo se guarda en destino local configurado (`/exports/accounting/YYYY-MM/`).
4. Contabilidad importa desde el destino configurado.
5. Resultado de export (`success/fail`) se guarda en tabla de auditoria.

### Modo smart: upload de esquema CSV + mapping dinamico

Para evitar codificar un export por cada proveedor, el sistema debe permitir
que Admin suba un CSV ejemplo (plantilla real del software contable) y
configure el mapping una sola vez.

Flujo propuesto:

1. Admin sube archivo de esquema (headers objetivo) en pantalla de configuracion.
2. Sistema detecta columnas y propone auto-mapping con campos canonicos.
3. Admin ajusta transformaciones (default, formato fecha, moneda, etc.).
4. Mapping se guarda en PostgreSQL como perfil versionado por proveedor.
5. Cada export usa ese perfil para generar el archivo final sin tocar codigo.

Campos canonicos minimos sugeridos:

- `service_date`
- `member_name`
- `payment_method`
- `diezmo`
- `ofrenda`
- `primicias`
- `pro_templo`
- `ofrenda_misionera`
- `ofrenda_pastoral`
- `total`

Campos extendidos/custom:

- `custom_fields` (objeto JSON con claves dinamicas por iglesia/proveedor).
- Convencion recomendada: `custom_<nombre_campo>` para columnas sueltas.
- Todo custom field debe incluir tipo esperado (`string`, `number`, `date`, `bool`).
- Si un custom field es obligatorio para un proveedor, marcar `is_required=true` en el mapping profile.

### Contrato sugerido para export

```python
class IExportStrategy(ABC):
   @abstractmethod
   def export(self, records: list[dict], destination: str) -> dict:
      """Retorna metadata: file_path, rows, status, errors."""
```

---

## Kiosk Mode (POS) - Tiendita

### Objetivo

Operar ventas simples desde la app para la tiendita de iglesia con flujo rapido,
auditable y compatible con `cash` y `zelle`.

### Flujo base

1. Operador abre pantalla kiosk.
2. Selecciona item (o crea item custom) y cantidad.
3. Sistema calcula subtotal y total.
4. Operador elige metodo de pago:
  - `cash`: registra efectivo recibido y cambio.
  - `zelle`: busca cliente por nombre; si no existe, lo crea al vuelo.
5. Orden y pago quedan auditados con usuario y timestamp.

### Campos minimos por ticket

- `quantity`
- `item_name` (ej. Quesadilla)
- `unit_price`
- `payment_method` (`cash` | `zelle`)
- `zelle_customer_name` (si aplica)
- `created_by_user_id`

### Items custom

- Admin/Tesorero puede crear item desde UI con nombre, precio y activo/inactivo.
- Si es venta ocasional, permitir linea custom sin guardar catalogo global.
- Toda creacion/edicion de item debe quedar en auditoria.

### Reglas de negocio

1. No cerrar ticket con total <= 0.
2. Si pago es `zelle`, `zelle_customer_name` es requerido.
3. Si cliente no existe en lista, se crea automaticamente con marca `created_from_kiosk=true`.
4. Perfil `auditor` solo lectura de ventas y pagos.

---

## Modelo de Datos (PostgreSQL + Export Opcional)

### Decision

1. PostgreSQL es la fuente principal para consultas y reportes de la app.
2. En MVP, los archivos de export se guardan en destino local configurable.
3. Integraciones externas como SharePoint se tratan como adaptadores futuros opcionales.

### Matriz de source-of-truth (alineada con ADR-002 y ADR-006)

| Dataset | Fuente autoritativa | Ruta de escritura | Sincronizacion | Politica de conflicto |
|---|---|---|---|---|
| Ofrendas, correcciones, cash, kiosk, outputs, auditoria | PostgreSQL | App -> PostgreSQL | N/A | PostgreSQL gana; no hay sobrescritura externa de transacciones |
| Archivos de export contable (`/exports/accounting/...`) | Storage local configurable | Export job -> storage local | Metadata de corrida en PostgreSQL (`export_runs`) | Storage conserva archivo; PostgreSQL conserva trazabilidad |
| Plantillas CSV subidas por admin | Storage local + metadata en PostgreSQL | Admin UI -> storage local (+ registro en PostgreSQL) | Reintentos async si storage no disponible | Version activa se decide en PostgreSQL; archivo referenciado por path/version |
| Cola local de contingencia para fallas de export | Cola durable local temporal | Fallback writer local | Replay async hacia storage local | Cola solo reintenta; no altera datos canonicos de PostgreSQL |

### Ventajas

- Reportes rapidos y filtrables desde la app (fechas, tipos, totales, usuario).
- Menor friccion para analitica futura.
- Menor complejidad operativa al evitar sincronizacion obligatoria en MVP.
- Campos custom de export se configuran por perfil (JSON) sin crear nuevas columnas cada vez.

### Riesgos y mitigaciones

1. Doble persistencia puede causar inconsistencias.
  Mitigacion: matriz de fuente autoritativa por dataset + IDs idempotentes + reconciliacion nocturna.
2. Mayor complejidad operativa.
  Mitigacion: iniciar con 1 pipeline de escritura principal y sync asincrono.

---

## Pipeline de Entrega (CI/CD recomendado)

1. `lint + unit tests + contract tests` en cada pull request.
2. Build de imagen Docker versionada por commit SHA.
3. Deploy a staging automatico.
4. Smoke tests de OCR y guardado.
5. Aprobacion manual para produccion.
6. Despliegue blue/green o rolling con rollback rapido.

Para presupuesto cero, iniciar con deploy semiautomatico por script + checklist,
y evolucionar a CI/CD completo cuando el flujo este estable.

---

## Checklist de Preparacion para Produccion

- [ ] `main.py` separa wiring por ambiente (`local`, `staging`, `prod`).
- [ ] Repositorios tienen timeouts y reintentos configurables.
- [ ] Existe estrategia de export local configurable y proceso de reconciliacion.
- [ ] Endpoints de health/readiness implementados.
- [ ] Logs estructurados y dashboard operativo basico.
- [ ] Procedimiento de backup/restore documentado y probado.
- [ ] `cloudflared` corre como servicio Docker con autostart.
- [ ] Cloudflare Access protege rutas administrativas.
- [ ] Runbook para dias operativos (martes/jueves/domingo) definido.
- [ ] RBAC implementado para tesorero/admin/auditor.
- [ ] PostgreSQL operativo con backups y migraciones versionadas.
- [ ] Modulo `IExportStrategy` implementado con al menos QuickBooks + CSV canonico.
- [ ] Job de export deja archivos en destino configurado y registra auditoria.
- [ ] UI de Admin para upload de esquema CSV y edicion de mapping.
- [ ] Perfiles de mapping versionados por proveedor en PostgreSQL.
- [ ] Bandeja `GET /day-log` implementada con filtros y detalle por sobre.
- [ ] Correccion diferida implementada con trazabilidad por campo.
- [ ] Historial de cambios visible para perfil auditor.
- [ ] Ventana `GET /cash` implementada con conteo por denominaciones.
- [ ] Cierre de caja (`POST /cash/close`) con auditoria y control de diferencia.
- [ ] Ventana `GET /kiosk` implementada para POS basico.
- [ ] Flujo de pago `cash` y `zelle` implementado en kiosk.
- [ ] Alta de items custom desde UI con auditoria.
- [ ] Registro/alta automatica de cliente Zelle desde pago.
- [ ] Ventana `GET /outputs` implementada con filtros por fondo y categoria.
- [ ] Flujo `POST /outputs/create` y `POST /outputs/approve` implementado.
- [ ] Reportes separados por `fund_source` (catalogo dinamico).
- [ ] Gestion de fondos (`GET/POST/deactivate`) implementada en UI Admin.

---

## ADRs Asociados

- `ADR-001`: Topologia de ejecucion local y produccion.
- `ADR-002`: PostgreSQL como almacenamiento operativo principal (SharePoint diferido).
- `ADR-003`: Configuracion por entorno y gestion de secretos.
- `ADR-004`: Exposicion segura con Cloudflare Tunnel en presupuesto cero.
- `ADR-005`: Arquitectura de exportaciones contables multi-proveedor.
- `ADR-006`: PostgreSQL como fuente unica para operaciones y reportes en MVP.
- `ADR-007`: Mapping de export por upload de esquema CSV (configurable).
- `ADR-008`: Flujo de correccion diferida y auditoria por campo en UI.
- `ADR-009`: Ventana de cash con cierre diario y trazabilidad.
- `ADR-010`: Kiosk mode (POS) con items custom y pago cash/zelle.
- `ADR-011`: Control de salidas con fondo origen y aprobacion auditable.

---

*// offering-app v1.0 · SOLID + Strategy · Iglesia de Dios de la Profecía · 2026*