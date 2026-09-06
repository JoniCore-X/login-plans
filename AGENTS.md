# AGENTS.md — Canon del Sistema login_plans

Documento de referencia para cualquier sesión futura (humana o AI). Contiene la
arquitectura, las leyes inmutables, los comandos verificados, los patrones de
extensión, las decisiones técnicas, la deuda operacional y la observabilidad.

Principio rector: **ningún componente existe sin justificación**. Toda adición
debe explicar qué problema real resuelve.

---

## 1. Arquitectura

### 1.1 Flujo de un request

```text
HTTP Request
  │
  ▼
OpenTelemetryMiddleware      (span raíz, trace_id, via build_middleware_stack)
  │
  ▼
RequestIdMiddleware          (app/api/middleware/request_id.py)
  │   ├── request_id (uuid4 o echo de X-Request-ID entrante)
  │   ├── bind_contextvars(request_id, trace_id, method, path, client_ip)
  │   ├── log request_completed {status_code, duration_ms}
  │   └── headers: X-Request-ID + X-Trace-ID
  ▼
SecurityHeadersMiddleware    (app/api/middleware/security_headers.py)
  │   └── X-Frame-Options, X-Content-Type-Options, HSTS (prod)
  ▼
CORSMiddleware               (origins allowlist via settings.allowed_origins)
  ▼
Router (app/api/router.py)
  ├── /api/v1/auth/*         (register, login, verify-email, change-password,
  │                          logout, refresh)
  ├── /api/v1/plans/*        (CRUD + publish/archive)
  ├── /api/v1/health         (real DB check → 200/503)
  └── /metrics               (Prometheus, excluido de OpenAPI)
  ▼
Dependencies (app/api/dependencies.py, app/api/auth/dependencies.py)
  │   ├── enforce_login_rate_limit → container.rate_limiter.allow("login:{ip}")
  │   └── bearer → AuthenticationService.authenticate
  ▼
Application Services         (app/application/*/services.py)
  │   ├── Command/Query objects (CQRS-lite)
  │   ├── UnitOfWorkFactory → UnitOfWork (transacción + collect_event)
  │   └── Métricas de negocio (.inc() en puntos de decisión)
  ▼
Domain                       (app/domain/{users,sessions,plans})
  │   ├── Aggregates: User, Session, Plan
  │   ├── Value Objects inmutables validados en constructor
  │   └── DomainEvents: UserRegistered, SessionRevoked, PlanCreated,
  │       PlanPublished, PlanArchived, ReplayAttackDetected,
  │       PasswordChanged, EmailVerified, SessionRotated
  ▼
Repositories (ports en app/domain/repositories → impl en
             app/infrastructure/persistence)
  ▼
Post-Commit:
  ├── UnitOfWork.commit() → dispatch de eventos → AuditLogDispatcher
  │     → audit_logs (Postgres, JSONB, request_id indexado)
  └── EmailSender port → ConsoleEmailSender (dev) / futuro provider real
  ▼
PostgreSQL + Redis (rate limiting distribuido)
```

### 1.2 Agregados y sus Value Objects

| Aggregate | Value Objects | Métodos clave | Invariantes |
|---|---|---|---|
| `User` | `Email`, `PlainPassword`, `PasswordHash`, `UserId` | `create`, `can_authenticate`, `start_email_verification`, `verify_email`, `change_password`, `suspend/deactivate/activate` | Email verificado obligatorio para crear planes; password policy en `PlainPassword` |
| `Session` | `SessionCredential`, `SessionId`, `family_id` | `create`, `rotate`, `revoke`, `was_rotated`, `is_active` | Expiración fija; rotación con familia; credencial opaca (solo hash persiste) |
| `Plan` | `PlanName`, `PlanDescription`, `PlanId`, `version` | `create`, `update`, `publish`, `archive`, `pull_events` | Versionado optimista (`version` check); owner-scoped (`user_id` + `plan_id`); inmutable tras archivo |

### 1.3 Mapa de Puertos y Adaptadores

| Puerto (`app/application/ports/`) | Adaptador (`app/infrastructure/`) | Notas |
|---|---|---|
| `PasswordHasher` | `security/password_hasher.py` (Argon2) | sync, `@trace_span` |
| `RateLimiter` | `security/rate_limiter.py` (in-memory) / `security/redis_rate_limiter.py` (Lua atómico) | Selección por `settings.redis_url` |
| `Clock` | `clock.py` | Inyectado en servicios — tests deterministas |
| `EmailSender` | `email/console_sender.py` | Stub dev; producción requiere provider real |
| `EventDispatcher` | `events/audit_log_dispatcher.py` | Persiste en `audit_logs` con `request_id` |
| `HealthChecker` | `persistence/postgres_health.py` | `SELECT 1` real |
| `SessionCredentialGenerator` | `security/session_credentials.py` | Genera opacos + hash |
| `UnitOfWork`/`UnitOfWorkFactory` | `unit_of_work.py` | Transacción + collect_event → dispatch post-commit |

Repos en `app/domain/repositories` (puertos) → impls en
`app/infrastructure/persistence/` con mappers en `persistence/mappers/`.

---

## 2. Leyes Inmutables

Estas leyes están **enforced por tests de arquitectura** en
`tests/architecture/test_import_boundaries.py`. Violarlas rompe el build.

### Ley 1 — `domain` no importa nada fuera de `app.domain`

```python
# PROHIBIDO en app/domain/**:
from app.application.services import ...      # viola
from app.infrastructure.database import ...  # viola
import sqlalchemy                             # prohibido (framework)
```

Justificación: el dominio debe ser testeable sin DB, sin framework, sin I/O.
Es el núcleo de negocio puro.

### Ley 2 — `application` solo importa `app.application` y `app.domain`

```python
# PROHIBIDO en app/application/**:
from app.infrastructure.metrics import ...   # viola — por eso los counters
from app.api.dependencies import ...         # viola   viven en
from app.bootstrap.container import ...      # viola   app/application/metrics.py
```

Consecuencia directa: los contadores Prometheus viven en
`app/application/metrics.py`, NO en `app/infrastructure/`. La regla manda
sobre la convención.

### Ley 3 — `api` no importa `infrastructure` ni `database`

La capa API recibe implementaciones via DI (`Depends(container.*)`),
nunca via import directo.

### Ley 4 — `infrastructure` nunca importa `api`

Los adaptadores son consumidos; nunca conocen al consumidor.

### Ley 5 — Credenciales opacas: solo hashes en persistencia

`SessionCredential` y tokens de verificación se almacenan **siempre** como
hash. El valor crudo vive solo en memoria durante el request.

```python
# ANTI-PATTERN:
await repo.save(session.credential.value)  # NUNCA el valor crudo

# CORRECTO:
await repo.save(credential_generator.hash(credential).value)
```

### Ley 6 — Comparación timing-safe de tokens

`secrets.compare_digest` para tokens de verificación. Nunca `==`.

### Ley 7 — Rate limiting: fail-closed

Si Redis falla, el error se propaga → 500 sanitizado. **Nunca** se permite
silenciosamente un request cuando el limiter está caído.

### Ley 8 — Todo evento de dominio auditable termina en `audit_logs`

`collect_event` en UoW → dispatch post-commit → `AuditLogDispatcher`.
Nunca llamar al dispatcher directamente desde servicios.

### Ley 9 — El `Clock` se inyecta, nunca `datetime.now()` directo en
dominio/aplicación. Los tests dependen de tiempo controlable.

### Ley 10 — No crear configuración en `.claude/`, `.cursor/` u otros
directorios de herramientas. Toda config nueva va en `.devin/`.

---

## 3. Comandos Verificados

Todos verificados en este repo (Python 3.14, Windows + venv):

```powershell
# Suite completa
.venv\Scripts\python -m pytest -q                  # 200 passed
.venv\Scripts\python -m pytest -n auto -q          # paralelo (pytest-xdist)

# Calidad
.venv\Scripts\python -m mypy app                   # 0 issues, 116 files
.venv\Scripts\python -m ruff check .
.venv\Scripts\python -m ruff check . --fix
.venv\Scripts\python -m ruff format .
.venv\Scripts\python -m ruff format --check .

# Migraciones
$env:DATABASE_URL='postgresql+asyncpg://login_plans:login_plans_dev_password@localhost:5432/login_plans'
.venv\Scripts\python -m alembic upgrade head
.venv\Scripts\python -m alembic revision --autogenerate -m "descripcion"

# Stack completo (Docker)
docker compose up -d                        # postgres + redis + jaeger + prometheus + app
docker compose ps                           # estado
docker compose logs -f app                  # logs JSON estructurados
docker compose build app                    # rebuild tras cambios de código
docker compose down -v                      # limpieza total (destructivo)

# Health y observabilidad
curl http://localhost:8000/api/v1/health    # {"status":"healthy","components":{"database":"connected"}}
curl http://localhost:8000/metrics          # métricas Prometheus
curl -i http://localhost:8000/api/v1/auth/login ...  # mirar X-Request-ID + X-Trace-ID
```

Notas:
- Los tests usan `login_plans_test` (+ `login_plans_test_gwN` por worker
  con `-n auto`); el schema se crea via `create_all`, no por Alembic.
- `pytest` lee `.env.test` (`APP_ENV=test`): tracing activo pero sin
  exporter (provider sin processor — spans y trace_ids válidos sin ruido).
- `.env.example` documenta `REDIS_URL`, `OTLP_ENDPOINT`, `ENABLE_TRACING`.

---

## 4. Patrones de Extensión

### Ejemplo: agregar agregado `Project`

```text
Paso 1  app/domain/projects/entities.py
        class Project: create/update/pull_events — invariantes aquí.
Paso 2  app/domain/projects/value_objects.py
        ProjectId, ProjectName (validan en __post_init__).
Paso 3  app/domain/projects/exceptions.py + enums.py
Paso 4  app/domain/repositories/projects.py (puerto ABC)
Paso 5  app/application/projects/{commands,queries,dto,services}.py
        Servicios reciben unit_of_work_factory + clock (DI).
        Incrementar counters en app/application/metrics.py si aplica.
Paso 6  app/infrastructure/persistence/models/project.py (SQLAlchemy)
        + persistence/mappers/project.py (model ↔ entidad)
        + persistence/postgres_project_repository.py (impl puerto)
Paso 7  Migración Alembic:
        alembic revision --autogenerate -m "add projects table"
Paso 8  app/api/projects/router.py + schemas.py
        Registrar router en app/api/router.py
        Registrar handlers de excepciones en app/bootstrap/application.py
Paso 9  Wiring en app/bootstrap/container.py
        (factory del servicio con las deps inyectadas)
Paso 10 Tests:
        tests/domain/projects/        → invariantes puras
        tests/application/projects/   → servicios con fakes
        tests/api/projects/           → E2E con client httpx
        tests/infrastructure/         → repo contra test DB
```

Si el agregado emite eventos: definirlos en `app/domain/events/` y recolectar
con `unit_of_work.collect_event(...)` — el audit trail es automático.

---

## 5. Decisiones Técnicas

| Decisión | Alternativas | Por qué esta |
|---|---|---|
| Redis **Lua script** para rate limiting | Pipeline secuencial | Race real: dos instancias podían limpiar→contar→insertar concurrentemente y sobre-aceptar. Lua ejecuta cleanup+count+insert+expire **atómicamente** en el servidor. |
| `allow(key)` con limit/window en constructor | `allow(key, limit, window)` | El puerto existente fija configuración por instancia; la API no sabe los valores. No se toca el contrato. |
| `request_id` como **columna** en `audit_logs` | Campo dentro de `payload` JSONB | Indexable: `WHERE request_id = ?` sin scan de JSONB. |
| Counters Prometheus en `app/application/` | `app/infrastructure/metrics/` | La regla de arquitectura prohíbe application→infrastructure. La ley gana sobre la convención. |
| `structlog.contextvars` para request_id | Pasar request_id por parámetro | Cero contaminación de firmas; propagación implícita por async context. |
| Tracing: provider sin exporter en tests | ConsoleSpanExporter siempre | El exporter a stdout rompe bajo pytest (I/O en stream cerrado). En `APP_ENV=test`: provider real, spans y trace_ids válidos, sin escritura. |
| Parche `_patch_route_details_for_lazy_routers` | Downgrade FastAPI | FastAPI 0.141 usa `_IncludedRouter` lazy; OTel accede `.path` en `Match.PARTIAL` (CORS preflight) sin try/except. Parche quirúrgico sobre la función, no sobre el framework. |
| `Instrumentator` una sola vez por proceso | instrument() por app | REGISTRY es global → segunda instrumentación = `Duplicated timeseries`. Flag `_instrumented` module-level. |
| `prometheus-fastapi-instrumentator==8.1.0` | 7.x | 7.x downgradea starlette a 0.52.x y rompe `_IncludedRouter`. 8.1.0 restaura starlette 1.6.0 y maneja routers lazy. |
| Excluir `/health` y `/metrics` de traces y métricas | Instrumentar todo | Docker healthcheck + scrape cada N segundos inflarían métricas y traces con ruido de infraestructura. |
| `Session` con `family_id` y rotación | Tokens de larga vida | Replay de credencial robada → `was_rotated()` → purga de familia completa + evento `ReplayAttackDetected`. |
| `AuditLogDispatcher` abre su propia sesión | Reusar sesión del request | El dispatch es post-commit; reusar la sesión acoplaría el audit al ciclo transaccional del request. |

---

## 6. Deuda Operacional

Lo que el código NO cubre y debe existir antes de producción real:

### 6.1 Urgente — Sacar el repo de OneDrive

OneDrive ha revertido/corrompido archivos 12+ veces durante el desarrollo
(incluyendo `application.py` y tests mid-edición). Operación manual:

```powershell
# 1. Cerrar IDE y terminales sobre el repo
# 2. Mover
Move-Item "C:\Users\jonie\OneDrive\Desktop\login_plans" "C:\dev\login_plans"
# 3. Recrear venv (los paths absolutos quedan rotos tras el move)
cd C:\dev\login_plans
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
# 4. Verificar
.venv\Scripts\python -m pytest -q   # esperado: 200 passed
git remote -v
```

### 6.2 Checklist de producción

- [ ] **TLS/HTTPS**: reverse proxy (nginx/Caddy) + certificado (Let's Encrypt).
      La app asume proxy delante; `X-Forwarded-*` ya se respeta vía headers.
- [ ] **Secrets manager**: `DATABASE_URL`, `REDIS_URL`, credenciales SMTP —
      sacarlos de `.env` (AWS Secrets Manager / Vault / vars del orquestador).
- [ ] **Email provider real**: reemplazar `ConsoleEmailSender` (SendGrid/SES).
      Hoy los emails se imprimen en consola.
- [ ] **Backups**: `pg_dump` programado + retención + restore testeado.
- [ ] **Alertas**: `prometheus_rules.yml` + Alertmanager
      (5xx rate, p95 latency, `audit_failures_total > 0`, rate_limit spikes).
- [ ] **Rate limiting en el borde**: Cloudflare/WAF además del limiter interno.
- [ ] **Graceful shutdown de Redis**: `redis_client.aclose()` en lifespan
      shutdown (hoy solo se cierra `database.engine`).
- [ ] **Revisión `docker-compose.yml` para prod**: es orientado a desarrollo
      (passwords hardcodeadas, `latest` tags, puertos expuestos).
- [ ] **Rotación/retención de logs**: stdout JSON → collector (Loki/ELK).
- [ ] **Pentest / OWASP ZAP** antes de datos reales.
- [ ] Nunca inferir estado de PRs/deploys desde tests o commits exitosos.

---

## 7. Observabilidad

### 7.1 Servicios del stack (docker compose)

| Servicio | URL | Uso |
|---|---|---|
| App | http://localhost:8000 | API + `/metrics` + `/api/v1/health` |
| Jaeger UI | http://localhost:16686 | Explorar traces |
| OTLP gRPC | http://localhost:4317 | Receiver (app → Jaeger) |
| Prometheus | http://localhost:9090 | Métricas, scrape cada 5s |
| Postgres | localhost:5432 | DB principal |
| Redis | localhost:6379 | Rate limiting compartido |

### 7.2 Queries Prometheus útiles

```promql
# Throughput por endpoint
rate(http_requests_total[5m])

# p95 de latencia
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Errores 5xx
rate(http_requests_total{status=~"5.."}[5m])

# Intentos de login
auth_login_attempts_total

# Rate limits disparados
rate_limit_hits_total

# Eventos de auditoría por tipo
audit_events_total

# Auditorías que fallaron al persistir (debe ser 0)
audit_failures_total
```

### 7.3 Correlación: encontrar TODO sobre un request

```text
1. Response headers del request:
   X-Request-ID: abc123...
   X-Trace-ID:   def456...

2. Logs (stdout JSON en prod):
   buscar "request_id": "abc123..."  → request_completed/failed

3. Audit trail:
   SELECT * FROM audit_logs WHERE request_id = 'abc123...';

4. Jaeger UI (:16686):
   service "login-plans-test" → Search → tag trace_id=def456...
   → timeline: HTTP → SQLAlchemy → redis.rate_limit_check →
     argon2.verify_password → audit.persist_events
```

### 7.4 Estructura del log estructurado

```json
{
  "event": "request_completed",
  "level": "info",
  "timestamp": "2026-09-06T13:00:00Z",
  "request_id": "abc123...",
  "trace_id": "def456...",
  "method": "POST",
  "path": "/api/v1/auth/login",
  "client_ip": "10.0.0.1",
  "status_code": 200,
  "duration_ms": 145.2
}
```

En `APP_ENV` distinto de production: ConsoleRenderer coloreado.
En production: JSONRenderer (una línea por log, parseable).

---

## Apéndice — Estado verificado

```text
Tests:     200 passed (serial y paralelo con -n auto)
Typecheck: mypy app → 0 issues (116 archivos)
Lint:      ruff check + format → clean
Commit de referencia: ce00879 (OpenTelemetry + Jaeger)
```
