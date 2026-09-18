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
- [ ] Endpoint para subir foto de evidencia a S3 (reutilizando el patrón que ya tienes en `fastapi-gemini-s3/main.py`).
- [ ] Guardar en la base de datos solo la key/URL resultante, nunca el binario.

## Fase 10 — Conversión de moneda
- [ ] Integrar la Currency Exchange API del brief (`GET /convert?from=USD&to=SGD&amount=...`).
- [ ] Exponer cada cifra monetaria en USD y SGD, resuelta en el momento de la consulta (nunca una tasa fija en el código).

## Fase 11 — Reporte mensual con Gemini
- [ ] Calcular en el backend los agregados del mes: número de decomisos, nacionalidad del traficante, pérdida potencial total (ambas monedas), especies más afectadas.
- [ ] Enviar **solo esas cifras ya calculadas** a Gemini para que redacte el resumen narrativo (nunca pedirle que calcule).
- [ ] Flujo de estado: el informe nace como borrador y requiere aprobación explícita de un `lab_director`.
- [ ] Generar también el informe en mandarín, japonés y vietnamita, como PDF, con la bandera del país destino en la portada — solo el informe compilado, nunca datos crudos de casos.

## Fase 12 — Validación de tus propios cálculos
- [ ] Al menos una forma de verificar `POTENTIAL_LOSS_PER_CASE` (test automatizado o endpoint secundario con lógica distinta que recalcule y compare).
- [ ] Dejarla visible en el repositorio (no borrarla).

## Fase 13 — Limpieza y revisión de código
- [ ] Confirmar arquitectura en una sola dirección (controlador → servicio → repositorio).
- [ ] Nombres de variables/tablas/funciones en inglés, `snake_case`, que reflejen el dominio (`evidence_item`, `custody_event`), nunca genéricos (`data`, `temp`, `x`).
- [ ] Sin comentarios innecesarios — el código se explica por sus nombres.
- [ ] Revisar que no haya SQL crudo fuera de los repositorios, ni reglas de negocio dentro de un repositorio o controlador.

## Fase 14 — Documentación y entregables
- [ ] README con pasos de instalación y el porqué de tus decisiones de diseño.
- [ ] ERD como archivo aparte (ya generado en Fase 1).
- [ ] `.env.example` sin secretos reales.
- [ ] Repositorio en GitHub con historial de commits real (no todo en un solo commit).

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
