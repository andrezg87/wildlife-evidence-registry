# Roadmap — Straits Trace Labs: Wildlife Evidence Registry

Checklist de desarrollo en orden de dependencias reales (cada bloque se apoya en el anterior).
Referencias entre paréntesis apuntan a la sección del PDF del taller (`MiniProyectoBackend636.pdf`).

Convención de marcado: `[ ]` pendiente, `[x]` hecho, `[~]` en progreso.

---

## Fase 0 — Fundamentos (base teórica)
- [x] Leer el módulo de JWT (§01) — hecho, pero lo repasamos oralmente antes de implementar login, sin mirar el PDF, para confirmar que quedó interiorizado.
- [ ] Leer §02-§03 (brief del cliente y recursos de la compañía) en inglés, sin traducir — es parte del ejercicio.

## Fase 1 — Diseño del modelo de datos (ERD)
**Por qué va primero:** la rúbrica lo exige explícitamente ("diseña tu propio diagrama entidad-relación antes de escribir código", §05) y es lo que vas a explicar en la Fase 2 de la sustentación.
- [x] Identificar entidades mínimas exigidas: `case`, `evidence_item`, `species` (catálogo de 15), `suspect`, `custody_event` (historial append-only).
- [x] Decidir atributos de cada entidad, tipos de dato y cuáles son obligatorios.
- [x] Decidir relaciones y cardinalidades — resueltas en conversación:
  - `case` 1—N `evidence_item`, `species` 1—N `evidence_item` (llave foránea simple).
  - `case` N—N `suspect` vía tabla puente `case_suspect` (evita duplicar valores en una celda).
  - `custody_event`: holder guardado como texto (`handed_from`/`handed_to`), porque puede ser externo (NParks) o interno; solo `recorded_by_user_id` es FK real a `users` (quién registró el evento vía su sesión).
  - `monthly_report`: agregados **congelados** en el momento de generación (no recalculados después), mismo principio que la cadena de custodia — un documento oficial no cambia solo.
  - `monthly_report_translation`: tabla aparte por idioma, para no duplicar los números agregados (normalización).
- [x] Decidir claves primarias/foráneas y candidatos a `ENUM`/`CHECK` (rol de usuario, estado del caso, estado del informe) — pendiente de definir los valores exactos en la Fase 3 (DDL).
- [x] Diagrama generado (mermaid ERD, 9 tablas) — revisado en conversación.
- [ ] Dibujarlo a mano/Excalidraw (tarea del usuario, imitando el generado) y exportar como archivo aparte — entregable obligatorio.
- [ ] Explicar el diagrama en voz alta, en palabras simples, como si se lo mostraras a Dr. Suresh — sin mirar notas.

## Fase 2 — Entorno y esqueleto del proyecto
- [x] Crear base de datos PostgreSQL local — `wildlife_evidence_registry` (dedicada; `mini_proyecto` era de otro ejercicio, no se tocó).
- [x] Crear entorno virtual de Python e instalar dependencias: `fastapi`, `uvicorn`, `asyncpg`, `pydantic-settings`, `bcrypt`, `pyjwt`, `httpx`, `boto3`, `python-multipart`.
- [x] Definir estructura de carpetas de 3 capas: `app/presentation`, `app/services`, `app/repositories`, `app/db` (pool de `asyncpg`), `app/config.py` (settings).
- [x] Configurar `.env` (real, git-ignorado; reutiliza credenciales de AWS/Gemini de `fastapi-gemini-s3`) y `.env.example` (placeholders, sí se sube al repo).
- [x] Endpoint de salud (`GET /health`) — probado, responde `200 OK` con el pool conectado.
- [x] Inicializar repositorio Git — primer commit real hecho (`a64c887`).

## Fase 3 — Esquema de base de datos (DDL)
- [x] Traducir el ERD de la Fase 1 a `CREATE TABLE` en SQL puro — `sql/schema.sql`, 9 tablas.
- [x] Aplicar `CHECK` de Postgres para campos con valores fijos: `users.role`, `case_record.case_type`/`status`, `species.unit`/`evidence_item.unit`, `monthly_report.status`, `monthly_report_translation.language`. Se eligió `CHECK` sobre `ENUM` nativo por flexibilidad (más fácil de modificar con `ALTER TABLE` que un `ALTER TYPE`).
- [x] Tabla `case` renombrada a `case_record` — `case` es palabra reservada en SQL (expresión `CASE WHEN`).
- [x] Cadena de custodia: `custody_event` solo admite `INSERT` — la inmutabilidad se hace cumplir en la capa de servicios (Fase 7), no con una restricción de base de datos.
- [x] Script ejecutado contra `wildlife_evidence_registry` — verificado: 9 tablas y 8 llaves foráneas, coinciden exactamente con el ERD.

## Fase 4 — Datos de prueba (seed)
- [x] Insertar las 15 especies del catálogo (§03) con su valor de referencia — `sql/seed.sql`.
- [x] Insertar varios casos (5), evidencia de distintos tipos (15 ítems, uno por especie), sospechosos con nacionalidades distintas (6 sospechosos, 5 nacionalidades).
- [x] Insertar al menos un caso con más de un cambio de custodia — el primer ítem de evidencia (escamas de pangolín) tiene 3 eventos de custodia encadenados.
- [x] Volumen realista: 3 usuarios, 15 especies, 6 sospechosos, 5 casos, 15 evidencias, 8 vínculos caso-sospechoso, 17 eventos de custodia. Verificado con un JOIN de 3 tablas — los datos son consistentes entre sí.

## Fase 5 — Capa de repositorios (acceso a datos)
**Qué es:** funciones que ejecutan SQL explícito con `asyncpg` — sin ORM. Es la única capa que le habla a la base de datos.
- [x] Repositorio de `species` — construido como plantilla completa (repositorio + servicio + ruta), probado de punta a punta por HTTP. Bug real encontrado y corregido: `asyncpg` devuelve `UUID` de Python para columnas `uuid`, el esquema Pydantic debe declarar `UUID`, no `str`.
- [x] Repositorio de `case_record` — CRUD completo (`list`, `get`, `create`, `update_case_status`, `delete`).
- [x] Repositorio de `evidence_item` — CRUD completo, incluye `set_photo_url` (para la Fase 9, S3).
- [x] Repositorio de `suspect` — incluye `link_to_case` y `list_by_case` (usa `JOIN` con la tabla puente `case_suspect`).
- [x] Repositorio de `custody_event` — deliberadamente **solo** `create` y `list`, sin `update` ni `delete`: la inmutabilidad se garantiza porque esas funciones no existen, no por convención.
- [x] Repositorio de `users` — `get_by_username`, lo mínimo necesario para el login de la Fase 6.
- [x] Los 5 repositorios probados directamente contra la base de datos (sin esperar a tener rutas HTTP) — resultados consistentes con los datos de la Fase 4.

## Fase 6 — Autenticación JWT
**Por qué aquí:** ya tenemos usuarios y roles en el modelo; ahora conectamos el módulo teórico de §01 con código real.
- [x] Hashing de contraseñas con `bcrypt` — usuarios semilla ya guardados con hash (Fase 4), verificado con `bcrypt.checkpw` en el login real.
- [x] Endpoint `POST /auth/login`: valida contraseña contra el hash, firma JWT con claims `sub` + `role`. Probado: login correcto da token, contraseña incorrecta da `401` sin revelar cuál de los dos datos falló.
- [x] Dependencia `get_current_user` (`Depends`) que verifica firma y expiración — probado con token ausente, válido, y manipulado (los 3 casos responden como se espera).
- [x] Expiración corta y fija (`JWT_EXPIRATION_MINUTES=30` en `.env`), sin endpoint de refresh — a propósito.
- [x] Dependencia adicional `require_lab_director` (compone sobre `get_current_user`) — escrita y lista; se ejercita con una ruta real en la Fase 8 (eliminar evidencia).
- [x] Endpoint bonus `GET /auth/me` — útil en cualquier sistema real y nos sirvió para probar la protección sin esperar a tener las rutas de negocio.

## Fase 7 — Capa de servicios (lógica de negocio)
- [x] `case_service.py` — CRUD de casos + `calculate_potential_loss_usd`, la fórmula real en Python (`Decimal`, nunca `float`, para evitar errores de redondeo con dinero). Verificada a mano contra el caso 1 sembrado: 10005.00000 exacto.
- [x] `evidence_service.py` — `register_evidence_item` usa una **transacción real** (`pool.acquire()` + `connection.transaction()`): crea el ítem de evidencia y su primer evento de custodia como una sola unidad atómica. Los repositorios de `evidence_item` y `custody_event` se modificaron para aceptar una conexión opcional, así pueden participar en la misma transacción.
- [x] `custody_service.py` — `record_transfer` para movimientos posteriores (después del ingreso inicial automático); valida que la evidencia exista antes de insertar.
- [x] `suspect_service.py` — CRUD de sospechosos + vínculo a casos.
- [x] Probado con un caso y evidencia nuevos de punta a punta: transacción, custodia automática, segunda transferencia manual, y fórmula de pérdida — todo verificado con números exactos antes de limpiar los datos de prueba.

## Fase 8 — Capa de presentación (rutas/API)
- [x] `case_router.py` — CRUD de casos, `GET /cases/{id}/potential-loss`, evidencia y sospechosos anidados bajo `/cases/{id}/...`. Esquemas Pydantic usan `Literal` para `case_type`/`status`/`unit` — mismos valores que el `CHECK` de la base de datos, rechazados con `422` antes de llegar a la lógica de negocio (defensa en profundidad).
- [x] `evidence_router.py` — incluye `DELETE /evidence/{id}` restringido a `lab_director` (el ejemplo textual de la rúbrica) y los endpoints de historial/registro de custodia.
- [x] `suspect_router.py` — CRUD de sospechosos.
- [x] **Bug real encontrado y resuelto durante las pruebas:** `DELETE` sobre evidencia/caso fallaba con `500` (`ForeignKeyViolationError`) porque Postgres bloquea por defecto borrar una fila que otra tabla todavía referencia. Decisión de diseño tomada conscientemente: `ON DELETE CASCADE` en las relaciones donde el hijo no tiene sentido sin el padre (`evidence_item.case_id`, `custody_event.evidence_item_id`, `case_suspect.*`) — nunca en relaciones de "quién lo hizo" (`recorded_by_user_id`, `species_id`), para no destruir accidentalmente historial al borrar un usuario o una especie.
- [x] Probado con Swagger implícito vía `curl`: `analyst` recibe `403` al intentar eliminar evidencia, `lab_director` recibe `204`; la cascada se verificó consultando la base de datos directamente después del borrado.

## Fase 9 — Fotos en S3
- [x] `storage_repository.py` — cliente de `boto3` creado una sola vez (no por petición, a diferencia del proyecto anterior), en la capa de repositorios (S3 es "otro sistema externo", igual que Postgres, aunque no sea SQL).
- [x] `evidence_service.upload_evidence_photo` — envuelve la llamada bloqueante de `boto3` con `asyncio.to_thread`, para no congelar el servidor mientras sube el archivo (mismo problema conceptual que las transacciones de la Fase 7, resuelto con otra herramienta porque `boto3` no es async).
- [x] `POST /evidence/{id}/photo` — probado subiendo un archivo real y confirmando su existencia directamente en el bucket S3 (no solo que la URL se ve bien).
- [x] Base de datos guarda solo la URL resultante en `evidence_item.photo_url`, nunca el binario.
- [x] **Limitación documentada, no un bug escondido:** al eliminar una evidencia (cascada de la Fase 8), el archivo en S3 no se borra automáticamente — queda huérfano en el bucket. No lo resolvimos porque el taller no lo exige, pero en producción se agregaría una llamada a `storage_repository` dentro de `delete_evidence_item` para borrarlo también.

## Fase 10 — Conversión de moneda
- [x] `currency_repository.py` — llama la Currency Exchange API del brief con `httpx.AsyncClient` (nativamente async, a diferencia de `boto3` — por eso no necesitó `asyncio.to_thread`). Se revisó la respuesta real de la API antes de asumir su forma.
- [x] `case_service.calculate_potential_loss` — combina la fórmula propia (USD, Fase 7) con la tasa en vivo de la API externa (SGD), resuelta en cada consulta, nunca una tasa fija en el código.
- [x] `GET /cases/{id}/potential-loss` ahora devuelve ambas cifras. Verificado contra el caso 1: 10005.00000 USD → SGD, y el resultado coincide exactamente con una llamada manual e independiente a la misma API.

## Fase 11 — Reporte mensual con Gemini
- [x] **Hueco de esquema encontrado y corregido:** `monthly_report` no tenía columna para "nacionalidad del traficante", aunque el brief (§02) la pide explícitamente. Se agregó `top_trafficker_nationality`.
- [x] `report_repository.py` trae datos crudos por mes (evidencia + especie, nacionalidades de sospechosos) — la decisión de "cuál es la más afectada/común" vive en el servicio, no en SQL, mismo principio que la Fase 7.
- [x] `report_service._compute_monthly_aggregates` — número de decomisos, pérdida potencial (USD vía Fase 7, SGD vía Fase 10 en vivo), especie más afectada, nacionalidad más común — todo en Python puro.
- [x] `gemini_repository.py` — mismo patrón que `fastapi-gemini-s3`, con reintentos (backoff exponencial) agregados tras un `503` real de la API en pruebas.
- [x] El prompt a Gemini incluye explícitamente "no calcules ni inventes ningún número, solo narra lo que te doy" — cumple "nunca le pidas que calcule" (§05).
- [x] **Bug real: generación no reanudable.** El primer intento falló a medias por un timeout de Gemini (2 de 3 idiomas ya guardados); la función original revisaba "¿ya existe el informe?" y se detenía ahí, sin completar lo que faltaba. Corregido: ahora resume generando solo las traducciones faltantes.
- [x] **Bug real: fuentes de PDF sin soporte para CJK.** Las fuentes básicas (`Helvetica`) no dibujan chino/japonés — se investigó y probó una fuente Unicode real (`Arial Unicode.ttf`) con texto en los 3 idiomas antes de confiar en que funcionaría.
- [x] **Bug real: URLs de S3 "públicas" que en realidad no funcionan** (bucket privado → `AccessDenied`). Corregido en `storage_repository` y en Fase 9 también: ahora se guarda solo la **key** del objeto (`photo_key`/`pdf_key`, columnas renombradas para que el nombre no mienta) y se genera una **URL firmada** bajo demanda en cada consulta — así un informe ya aprobado nunca queda con un link roto ni uno que expira en silencio.
- [x] Flujo de aprobación probado con ambos roles: `analyst` → `403`, `lab_director` → `200` (`status: approved`), segundo intento de aprobar → `409`.
- [x] Probado de punta a punta con datos reales: informe de enero 2026 generado, agregados verificados a mano, PDF en chino descargado y leído — bandera, título y texto de Gemini con los números exactos.

## Fase 12 — Validación de tus propios cálculos
- [x] `tests/test_potential_loss_cross_check.py` — la prueba central: recalcula `POTENTIAL_LOSS_PER_CASE` con SQL puro (`SUM()`), un camino completamente distinto al de producción (loop en Python), y compara que coincidan. Segunda prueba compara contra el valor calculado a mano.
- [x] `tests/test_custody_immutability.py` — prueba "estructural": confirma que `custody_event_repository` no expone ninguna función de `update`/`delete` (la garantía de la Fase 5, verificada automáticamente).
- [x] `tests/test_auth_service.py` — hash de contraseñas (acepta la correcta, rechaza la incorrecta) y la dependencia `require_lab_director` (acepta `lab_director`, rechaza `analyst` con `403`).
- [x] `pytest.ini` — configuración necesaria para que el pool de base de datos (de sesión) y las pruebas async compartan el mismo event loop; sin esto, las pruebas con base de datos fallan con un error de "different loop".
- [x] 6 pruebas, todas pasando. Quedan en el repositorio, no se borran.

## Fase 13 — Limpieza y revisión de código
- [x] **Arquitectura confirmada con `grep`:** cero SQL crudo fuera de `app/repositories`. La fórmula de pérdida potencial vive en `case_service`, no en un repositorio (Fase 7). Todos los endpoints usan `response_model` con esquemas Pydantic propios — ninguno devuelve un `Record` de `asyncpg` directamente.
- [x] **Nombrado:** encontrada y corregida una variable genérica (`data` → `generation_result` en `gemini_repository.py`, la respuesta parseada de Gemini). Cero `camelCase` accidental — todo `snake_case` consistente. Cero texto en español en `app/` ni `sql/` (verificado con `grep` de acentos y palabras comunes).
- [x] **Comentarios:** un solo bloque en todo `app/` (`pdf_repository.py`) — explica por qué se necesita una fuente Unicode específica, una restricción externa no obvia, no un nombre mal elegido.
- [x] Suite de pruebas (Fase 12) y arranque completo de la app (21 rutas) verificados de nuevo después de la limpieza — nada se rompió.

## Fase 14 — Documentación y entregables
- [x] `README.md` — instalación, usuarios de prueba, y cada decisión de diseño no trivial con su porqué (pensado como material de repaso, no solo como onboarding).
- [x] ERD como archivo aparte — `erd.png` / `erd.mmd` (Fase 1, actualizado en Fase 11 con la columna nueva).
- [x] `.env.example` sin secretos reales — verificado con `git ls-files` que el `.env` real nunca se subió.
- [x] **Repositorio en GitHub:** https://github.com/andrezg87/wildlife-evidence-registry — público, historial de commits real (14 commits, uno por fase/hito, no un solo commit final).

## Fase 15 — Preparación de la sustentación
- [ ] **Fase 1 (inglés):** ensayar presentar hallazgos a "Dr. Suresh" en lenguaje de negocio — casos, especies, pérdidas evitadas — sin jerga técnica.
- [ ] **Fase 2 (español):** para 3-4 funcionalidades candidatas (login, registro de evidencia, cambio de custodia, reporte mensual), ensayar explicarlas de punta a punta: tablas → 3 capas → respuesta de la API → manejo de JWT — sin mirar notas ni PDF.
- [ ] Reflexión personal: qué aprendiste, qué se te dificultó, qué conceptos fueron más importantes (se evalúa directamente, 0.5 pts).
- [ ] Generar el PDF de repaso final (lo armamos juntos cuando todo esté probado y funcionando).

---

## Mapeo a la rúbrica (7.0 pts total, mínimo 4.9)
| Pts | Criterio | Fases que lo cubren |
|-----|----------|----------------------|
| 2.0 | Backend funcional | 1–12 |
| 2.0 | Revisión de código | 3, 4, 13 |
| 1.0 | Fase 1 — presentación al cliente | 15 |
| 0.5 | Fase 2 — explicación técnica | 15 |
| 0.5 | Fase 2 — reflexión de aprendizaje | 15 |
| 1.0 | Fase 2 — funcionalidad de punta a punta | 6, 7, 8, 15 |
