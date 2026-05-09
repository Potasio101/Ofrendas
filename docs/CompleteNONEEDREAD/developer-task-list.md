# Developer Task List - Ofrendas

Objetivo: reducir deuda tecnica, mejorar seguridad y mantener el flujo operativo estable en iPad/mobile.

## Task 1 - Extraer logica de OCR fallback fuera de UI
Prioridad: Alta

Problema:
- La logica de decision para fallback manual OCR esta en la capa web.
- Esto acopla reglas de negocio a rendering/routes.

Trabajo:
1. Mover la logica de fallback OCR a la capa de servicios.
2. Exponer metodo de servicio tipo should_fallback_to_manual(data).
3. Mantener en UI solo la decision de render segun respuesta del servicio.

Archivos impactados:
- offering_app/ui/app.py
- offering_app/services/offering_service.py

Criterio de aceptacion:
1. UI no contiene reglas de negocio OCR (solo llamadas al servicio).
2. Tests de flujo OCR y fallback manual siguen pasando.
3. No hay cambio funcional visible para usuario final.

---

## Task 2 - Eliminar SQL directo desde main
Prioridad: Alta

Problema:
- main.py usa conexion directa repo._connect con SQL inline para miembros.
- Se rompe abstraccion del repositorio y hay excepciones silenciadas.

Trabajo:
1. Crear metodo en repositorio para obtener miembros activos.
2. Reemplazar load_members para usar el metodo formal.
3. Cambiar except Exception silencioso por logging controlado.

Archivos impactados:
- main.py
- offering_app/repositories/postgresql_repo.py

Criterio de aceptacion:
1. main.py no usa repo._connect directo.
2. Errores quedan logueados con contexto (no pass silencioso).
3. App inicia igual con y sin miembros en tabla users.

---

## Task 3 - Harden de auth por entorno
Prioridad: Alta

Problema:
- Defaults de auth permiten modo local-dev por omision.
- Riesgo de despliegue inseguro si no se configuran variables.

Trabajo:
1. Definir validacion fuerte al iniciar app para entorno production.
2. En production, fallar startup si APP_AUTH_MODE inseguro o secretos faltantes.
3. Documentar combinaciones validas de auth mode y variables requeridas.

Archivos impactados:
- offering_app/ui/app.py
- offering_app/config.py
- README.md

Criterio de aceptacion:
1. En production sin secretos requeridos, app no inicia.
2. En local-dev, comportamiento actual se mantiene.
3. README incluye matriz de configuracion de auth.

---

## Task 4 - Docker runtime para produccion
Prioridad: Media-Alta

Problema:
- Imagen actual usa python main.py (servidor dev de Flask).
- Falta usuario no-root y servidor WSGI de produccion.

Trabajo:
1. Agregar gunicorn a dependencias.
2. Cambiar CMD en Dockerfile a gunicorn.
3. Ejecutar contenedor como usuario no-root.
4. Mantener puerto y health checks compatibles con docker-compose actual.

Archivos impactados:
- Dockerfile
- requirements.txt
- docker-compose.yml

Criterio de aceptacion:
1. Contenedor arranca con gunicorn y responde healthz.
2. No corre como root.
3. Tests y smoke test basicos siguen verdes.

---

## Task 5 - Dividir UI monolitica en modulos
Prioridad: Media

Problema:
- app.py esta creciendo como archivo unico con rutas, templates y estilos.
- Dificulta mantenimiento y revisiones.

Trabajo:
1. Separar routes por dominio (core, cash, outputs, kiosk).
2. Mover helpers HTML/CSS a modulo dedicado de presentacion.
3. Mantener create_app como composition root de Flask.

Archivos impactados:
- offering_app/ui/app.py
- offering_app/ui/ (nuevos modulos)

Criterio de aceptacion:
1. app.py baja de tamano significativamente.
2. Rutas siguen respondiendo igual.
3. Tests existentes pasan sin regresion.

---

## Task 6 - Cobertura de pruebas de regresion clave
Prioridad: Media

Problema:
- Varias correcciones recientes son sensibles (manual flow, deferred correction total, day-log UX).

Trabajo:
1. Agregar tests de regresion para:
   - Manual save directo a day-log con notice.
   - Recalculo de total en correccion diferida.
   - Fallback OCR con baja confianza.
2. Agregar test de auth hardening en production.

Archivos impactados:
- tests/test_app_modules.py
- tests/test_app_workflow_views.py
- nuevos tests segun convenga

Criterio de aceptacion:
1. Casos criticos quedan cubiertos por test automatizado.
2. Suite completa pasa en Docker.

---

## Orden recomendado de ejecucion
1. Task 2
2. Task 1
3. Task 3
4. Task 4
5. Task 6
6. Task 5

## Definition of Done global
1. Todos los tests pasan en Docker.
2. No hay cambios de comportamiento no documentados.
3. README actualizado cuando aplique.
4. Commit por task con mensaje claro.
