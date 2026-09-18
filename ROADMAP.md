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
- [ ] Insertar las 15 especies del catálogo (§03) con su valor de referencia.
- [ ] Insertar varios casos, evidencia de distintos tipos, sospechosos con nacionalidades distintas.
- [ ] Insertar al menos un caso con más de un cambio de custodia en su historial.
- [ ] Volumen que se sienta real, no 2-3 filas de juguete (exigido en "Revisión de código", §05).

## Fase 5 — Capa de repositorios (acceso a datos)
**Qué es:** funciones que ejecutan SQL explícito con `asyncpg` — sin ORM. Es la única capa que le habla a la base de datos.
- [ ] Repositorio de `species`.
- [ ] Repositorio de `case`.
- [ ] Repositorio de `evidence_item`.
- [ ] Repositorio de `suspect`.
- [ ] Repositorio de `custody_event` (solo `INSERT`, nunca `UPDATE`).
- [ ] Repositorio de usuarios (para login).

## Fase 6 — Autenticación JWT
**Por qué aquí:** ya tenemos usuarios y roles en el modelo; ahora conectamos el módulo teórico de §01 con código real.
- [ ] Hashing de contraseñas al crear usuario (`passlib`/`bcrypt`).
- [ ] Endpoint `POST /auth/login`: valida contraseña contra el hash, firma JWT con claim `role`.
- [ ] Dependencia de FastAPI (`Depends`) que verifica la firma y expiración del token en cada ruta protegida.
- [ ] Expiración corta y fija, sin refresh tokens (a propósito, según el brief).
- [ ] Dependencia adicional que restrinja rutas solo a `lab_director` (ej. eliminar evidencia).

## Fase 7 — Capa de servicios (lógica de negocio)
- [ ] Servicio de casos y evidencia (reglas de creación/actualización).
- [ ] Servicio de custodia: cada cambio de custodia **crea automáticamente** una entrada en el historial (nunca editable directamente por el usuario).
- [ ] Servicio de cálculo: `POTENTIAL_LOSS_PER_CASE = Σ (cantidad_incautada × valor_referencia_especie)`, calculado en backend con código determinista.

## Fase 8 — Capa de presentación (rutas/API)
- [ ] Endpoints CRUD de casos y evidencia, protegidos por JWT.
- [ ] Endpoints del catálogo de especies y sospechosos.
- [ ] Endpoint(s) de historial de custodia (solo lectura + creación vía servicio, nunca edición).
- [ ] Verificar con Swagger (`/docs`) que cada ruta exige el rol correcto.

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
