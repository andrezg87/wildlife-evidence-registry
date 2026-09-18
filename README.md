# Wildlife Evidence Registry — Straits Trace Labs

Backend para un laboratorio forense que rastrea evidencia de tráfico de especies: casos,
ítems de evidencia, cadena de custodia, y un informe mensual con agregados calculados por
el backend y redactados con Gemini.

Construido para el miniproyecto de desarrollo backend — modelo de datos propio,
arquitectura de 3 capas, autenticación JWT, acceso a datos con `asyncpg` (sin ORM).

## Stack

- **FastAPI** (Python) sobre **PostgreSQL**, acceso con `asyncpg` directo — sin ORM.
- **JWT** (`pyjwt` + `bcrypt`) para autenticación, dos roles: `analyst` y `lab_director`.
- **AWS S3** para fotos de evidencia y PDFs del informe (URLs firmadas, no públicas).
- **Gemini** para redactar el resumen narrativo del informe mensual (nunca calcula números).
- Currency Exchange API del cliente, para USD ↔ SGD en vivo.
- `pytest` para la suite de validación.

## Arquitectura

```
app/
  presentation/   rutas de FastAPI — reciben HTTP, validan con Pydantic, llaman servicios
  services/       lógica de negocio — nunca SQL crudo, nunca conocen FastAPI
  repositories/   el único lugar que toca sistemas externos: Postgres, S3, Gemini, la API de moneda
  db/             pool de conexiones asyncpg
  config.py       variables de entorno (pydantic-settings)
  main.py         punto de entrada, wiring de routers y lifespan
sql/
  schema.sql      DDL — 9 tablas, CHECK constraints, ON DELETE CASCADE donde aplica
  seed.sql        datos de prueba realistas
tests/            suite de validación (pytest)
```

La dependencia entre capas fluye en una sola dirección: **presentación → servicios →
repositorios**. Un repositorio nunca decide una regla de negocio; un servicio nunca ejecuta
SQL directamente.

## Instalación

Requisitos: Python 3.11+, PostgreSQL corriendo localmente.

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# completa .env con tus propias credenciales (ver más abajo)

createdb wildlife_evidence_registry
psql -d wildlife_evidence_registry -f sql/schema.sql
psql -d wildlife_evidence_registry -f sql/seed.sql

uvicorn app.main:app --reload
```

La API queda en `http://localhost:8000`, documentación interactiva en `/docs`.

### Variables de entorno

Ver `.env.example` para la lista completa. Necesitas: una base de datos Postgres local, una
clave de API de Gemini, credenciales de AWS con acceso a un bucket S3, y una clave secreta
para firmar los JWT (cualquier string largo y aleatorio sirve para desarrollo local).

### Usuarios de prueba (sembrados en `seed.sql`)

| username | password | role |
|---|---|---|
| `rsuresh` | `DirectorPass123!` | `lab_director` |
| `agarcia` | `AnalystPass123!` | `analyst` |
| `jtan` | `AnalystPass123!` | `analyst` |

### Correr las pruebas

```bash
pytest tests/ -v
```

## Decisiones de diseño y su razonamiento

Esta sección existe para poder explicar el proyecto sin tener que releer el código —
cada decisión no trivial, con el porqué.

**UUID en vez de IDs autoincrementales.** En un sistema de evidencia legal, no quieres que
alguien pueda enumerar cuántos casos existen contando IDs consecutivos.

**`CHECK` en vez de `ENUM` nativo de Postgres** para campos de valores fijos (`role`,
`case_type`, `status`, etc.). Mismo efecto práctico, pero modificar la lista de valores
permitidos es un `ALTER TABLE` simple en vez de un `ALTER TYPE`.

**Tabla `case_record`, no `case`.** `CASE` es palabra reservada en SQL (la expresión
`CASE WHEN`). Nombrar la tabla `case` a secas obligaría a usar comillas dobles en cada
consulta.

**`case_suspect` como tabla puente**, con llave primaria compuesta `(case_id, suspect_id)`
— no tiene un `id` propio porque cada fila representa exclusivamente la existencia de un
vínculo; no tendría sentido que existieran dos filas idénticas.

**`custody_event.handed_from`/`handed_to` son texto, no llaves foráneas a `users`.** Quien
tiene la evidencia puede ser un oficial externo (NParks, ICA) que nunca tendrá cuenta en el
sistema. Solo `recorded_by_user_id` es una llave foránea real — es quién *registró* el
evento desde su sesión autenticada, no quién *tenía* la evidencia.

**`custody_event_repository.py` no expone ninguna función de `update` ni `delete`.** La
inmutabilidad de la cadena de custodia se garantiza porque esas funciones no existen, no
por convención. Verificado con una prueba estructural en `tests/`.

**`monthly_report` guarda los agregados congelados en el momento de generación**, no los
recalcula cada vez que se consulta. Un informe ya aprobado y enviado a NParks no debería
cambiar de números si después se corrige un dato histórico — mismo principio que la cadena
de custodia: un registro oficial no cambia solo.

**`monthly_report_translation` es una tabla aparte**, no una fila por idioma en
`monthly_report`. Evita repetir los mismos números agregados 3 veces — si hubiera que
corregir una cifra, se corregiría en un solo lugar.

**`ON DELETE CASCADE` solo en relaciones "el hijo pertenece al padre"** (`evidence_item` →
`case_record`, `custody_event` → `evidence_item`, `case_suspect` → ambos lados). Nunca en
relaciones "quién hizo esto" (`recorded_by_user_id`, `species_id`, `approved_by_user_id`) —
borrar un usuario o una especie nunca debería destruir historial en cascada.

**La fórmula `POTENTIAL_LOSS_PER_CASE` vive en `case_service`, en Python, con `Decimal`.**
Nunca `float` para dinero (errores de redondeo binario), nunca dentro de un repositorio
(el repositorio solo trae `quantity` y `reference_value_usd` crudos; la multiplicación y
la suma son la regla de negocio).

**Fotos y PDFs se guardan como `photo_key`/`pdf_key` (la key de S3), no como URL.** La
primera versión guardaba una URL "pública" que en realidad no funcionaba (bucket privado →
`AccessDenied`). La solución correcta es generar una URL firmada bajo demanda en cada
consulta — así un informe ya aprobado nunca queda con un link roto ni con uno que expiró en
silencio.

**Llamadas bloqueantes (`boto3`, generación de PDF) se envuelven con `asyncio.to_thread`.**
Ninguna de las dos es nativamente async; llamarlas directo dentro de una función `async def`
congelaría el servidor para todas las demás peticiones mientras duran. `httpx` (Gemini, la
API de moneda) sí es nativamente async y no lo necesita.

**`register_evidence_item` usa una transacción real** (`pool.acquire()` +
`connection.transaction()`) para crear el ítem de evidencia y su primer evento de custodia
como una sola unidad atómica — si la segunda inserción fallara, la primera se deshace sola.

**`generate_monthly_report` es reanudable, no todo-o-nada.** Si Gemini falla a la mitad
(pasó en pruebas reales — la API devolvió `503`), una segunda llamada completa solo las
traducciones que faltan, no repite las que ya se generaron.

**El prompt a Gemini incluye explícitamente "no calcules ni inventes ningún número".**
Todos los números que aparecen en el texto ya fueron calculados por el backend antes de
construir el prompt — Gemini solo redacta.

## Limitaciones conocidas (documentadas a propósito, no descubiertas por el profesor)

- Al eliminar una evidencia, el archivo en S3 no se borra (solo el registro en la base de
  datos) — queda huérfano en el bucket.
- `pdf_repository.py` depende de una fuente del sistema (`Arial Unicode.ttf`, macOS) para
  poder dibujar chino/japonés/vietnamita. En otro sistema operativo habría que embeber una
  fuente Unicode propia en el repositorio (ej. Noto Sans CJK) en vez de depender de una ruta
  del sistema.
- Sin refresh tokens ni lista de revocación de JWT — a propósito, fuera de alcance según el
  brief del cliente.

## Endpoints principales

Ver `/docs` para la lista completa e interactiva. Resumen:

- `POST /auth/login`, `GET /auth/me`
- `GET/POST /cases`, `GET/PATCH/DELETE /cases/{id}`, `GET /cases/{id}/potential-loss`
- `GET/POST /cases/{id}/evidence`, `GET/DELETE /evidence/{id}`, `POST /evidence/{id}/photo`
- `GET/POST /evidence/{id}/custody-events`
- `GET/POST /suspects`, `GET/POST /cases/{id}/suspects`
- `GET/POST /reports`, `POST /reports/generate`, `PATCH /reports/{id}/approve`,
  `GET /reports/{id}/translations`
- `GET /species`

`DELETE /evidence/{id}` y `PATCH /reports/{id}/approve` están restringidos a `lab_director`.
