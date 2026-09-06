# Login Plans API

Plantilla de autenticación y gestión de planes con arquitectura DDD production-ready.

## Antes de usar

Este proyecto es una **PLANTILLA** de alta calidad, no un producto terminado. Incluye:

- Motor de autenticación completo (Argon2, rate limiting distribuido, replay protection)
- Gestión de Planes con ownership, estados y concurrencia optimista
- Observabilidad completa (logs JSON + métricas Prometheus + traces OpenTelemetry)
- 200 tests passing, Docker Compose, CI/CD con GitHub Actions
- Arquitectura DDD estricta con tests de fronteras entre capas

**Requiere configuración de proveedor de email para producción:**

- Por defecto usa `ConsoleEmailSender` — imprime el token de verificación en los logs de la app
- Para producción, configura `RESEND_API_KEY` en `.env` (el adaptador ya está implementado)
- Ver [docs/CUSTOMIZATION.md](docs/CUSTOMIZATION.md) para otros proveedores (SendGrid, SES)

## Quick Start (5 minutos)

```bash
# 1. Clonar
git clone <url-del-repo>
cd login-plans

# 2. Levantar stack completo (Postgres + Redis + App + Prometheus + Jaeger)
docker compose up -d

# La app corre las migraciones automáticamente al arrancar.
# Espera ~30s hasta que `docker compose ps` muestre todo healthy.

# 3. Verificar
curl http://localhost:8000/api/v1/health
# {"status":"healthy","components":{"database":"connected","redis":"connected"}}

# 4. Registrar un usuario
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Test123456!"}'

# 5. Obtener el token de verificación de los logs
docker compose logs app | Select-String "VERIFICATION TOKEN"   # PowerShell
docker compose logs app | grep "VERIFICATION TOKEN"            # bash

# 6. Verificar el email
curl -X POST http://localhost:8000/api/v1/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{"token": "TOKEN_OBTENIDO_DE_LOGS"}'

# 7. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "Test123456!"}'
# → {"credential": "...", "expires_at": "..."}

# 8. Crear un plan (requiere email verificado)
curl -X POST http://localhost:8000/api/v1/plans \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <credential>" \
  -d '{"name": "Mi primer plan"}'
```

## Desarrollo local (API en tu máquina, datos en Docker)

Para modificar el código con hot reload:

```bash
# 1. Entorno virtual
python -m venv .venv
.\.venv\Scripts\Activate.ps1        # Windows
source .venv/bin/activate            # Linux/macOS

# 2. Dependencias (incluye pytest, mypy, ruff, alembic)
pip install -r requirements.txt

# 3. Configuración — las credenciales dev ya coinciden con docker-compose.yml
cp .env.example .env                 # Windows: copy .env.example .env

# 4. Solo las bases de datos en Docker
docker compose up -d postgres redis

# 5. Migraciones
alembic upgrade head

# 6. API local con hot reload
uvicorn app.main:app --reload --port 8000
```

`uvicorn` arranca en http://localhost:8000 con `--reload` — los cambios se
reflejan al guardar. Health: `curl http://localhost:8000/api/v1/health`.

Tests:

```bash
pytest -q          # serial
pytest -n auto -q  # paralelo (pytest-xdist)
mypy app
ruff check .
```

Requisitos: Python 3.12+, Docker (solo para Postgres/Redis), pip.
## Nuevo proyecto desde cero (Cookiecutter)

Si estás empezando un SaaS nuevo y quieres esta arquitectura desde el día 1:

```bash
pip install cookiecutter
cookiecutter https://github.com/JoniCore-X/login-plans --checkout template

# Responde las preguntas:
#   project_name [My SaaS]: fitness-tracker
#   project_slug [fitness_tracker]:
#   author_name  [Your Name]: Tu Nombre
#   email        [you@example.com]: tu@email.com
#   use_stripe   [n]: y
#   use_oauth    [n]: y

cd fitness-tracker
docker compose up -d
```

Genera el proyecto completo renombrado (nombre, contenedores Docker, bases
de datos, `pyproject.toml`, `.env.example`, tests) listo para desarrollar.
## CLI `login-plans` (próximamente)

Experiencia todo-en-uno en desarrollo activo:

```bash
pipx install login-plans-cli     # próximamente

lp init mi-saas                  # Genera proyecto (cookiecutter por dentro)
lp up                            # Stack completo (Docker por dentro)
lp deploy --env prod             # Deploy guiado a producción
```

Mientras tanto, los tres métodos anteriores cubren el mismo flujo.
## Integración como dependencia (próximamente)

Para agregar auth + planes a un proyecto FastAPI existente sin reescribirlo:

```bash
# próximamente — empaquetado como librería instalable
pip install login-plans
```

```python
# Uso planeado: montar el router y container en tu app existente
from login_plans.api import router as login_plans_router

app.include_router(login_plans_router, prefix="/api/v1")
```

Estado: en desarrollo. Hoy el camino equivalente es clonar el repo y
adaptar — los puertos (`app/application/ports/`) ya están diseñados para
inyectar sobre tu infraestructura existente.

## Comparación rápida

| Método | Tiempo | Para quién | Curva |
|---|---|---|---|
| Docker Compose | ~5 min | Probar / demo | Baja |
| Git clone + venv | ~10 min | Desarrolladores | Media |
| Cookiecutter | ~3 min | Proyectos nuevos | Baja |
| CLI `lp` | ~1 min | Todos (futuro) | Mínima |
| Dependencia | ~15 min | Integración avanzada | Alta |

## Verificación post-instalación

Independientemente del método:

```bash
# 1. Health (db + redis conectados)
curl http://localhost:8000/api/v1/health
# → {"status":"healthy","components":{"database":"connected","redis":"connected"}}

# 2. Registro
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"verify@example.com","password":"Strong-password-123!"}'
# → 201

# 3. Token en logs (modo consola) → verificar email → login → crear plan
#    (ver Quick Start pasos 5-8)
```

Si todos devuelven 200/201/204, la instalación es correcta.

## Troubleshooting

**`Port 8000 already in use`**

```bash
# Windows: encontrar y liberar el puerto
netstat -ano | findstr :8000
Stop-Process -Id <PID> -Force

# O cambia el puerto en docker-compose.yml → "8001:8000"
```

**`Database connection failed`**

```bash
docker compose ps            # postgres debe estar healthy
docker compose logs postgres # causa raíz
# Credenciales: login_plans / login_plans_dev_password (solo dev)
```

**`Migrations failed`**

```bash
docker compose exec app alembic current   # estado actual
docker compose logs app | Select-String "alembic"   # PowerShell
```

**`VERIFICATION TOKEN` no aparece en logs**

El token solo se imprime cuando `APP_ENV != production`. En
`docker-compose.yml` del repo ya es `development`. En local, revisa tu `.env`.

**Redis caído → login devuelve 500**

Es intencional (fail-closed). Verifica `docker compose ps` → redis healthy.
Sin `REDIS_URL` la app usa rate limiting in-memory.

## Siguiente paso

- [AGENTS.md](AGENTS.md) — arquitectura, leyes inmutables, patrones
- [docs/CUSTOMIZATION.md](docs/CUSTOMIZATION.md) — adaptar a tu proyecto
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — checklist de producción
## Observabilidad

| Servicio | URL | Uso |
|---|---|---|
| API Docs | http://localhost:8000/docs | Swagger UI |
| Health | http://localhost:8000/api/v1/health | DB check real |
| Métricas | http://localhost:8000/metrics | Prometheus endpoint |
| Prometheus | http://localhost:9090 | Queries y alertas |
| Jaeger | http://localhost:16686 | Traces distribuidos |

Cada response incluye `X-Request-ID` y `X-Trace-ID` para correlación
logs ↔ métricas ↔ traces.

## Documentación

- [AGENTS.md](AGENTS.md) — Canon del sistema (arquitectura, leyes inmutables, patrones)
- [docs/CUSTOMIZATION.md](docs/CUSTOMIZATION.md) — Cómo adaptar a tu proyecto
- [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — Checklist de producción

## Stack Técnico

- Python 3.14 + FastAPI + SQLAlchemy 2 async
- PostgreSQL + Redis (rate limiting compartido, Lua atómico)
- Argon2 (password hashing)
- OpenTelemetry → Jaeger, Prometheus → métricas
- structlog (logs JSON en prod, coloreados en dev)
- Docker Compose + GitHub Actions CI

## Configuración

Variables de entorno (ver `.env.example`):

| Variable | Default | Uso |
|---|---|---|
| `DATABASE_URL` | — | Postgres connection string |
| `REDIS_URL` | — (opcional) | Rate limiting distribuido; sin ella usa in-memory |
| `RESEND_API_KEY` | — (opcional) | Emails reales vía Resend; sin ella usa consola |
| `EMAIL_FROM` | `noreply@example.com` | Remitente de emails |
| `OTLP_ENDPOINT` | — (opcional) | Traces → Jaeger/Tempo en producción |
| `ENABLE_TRACING` | `true` | Desactivar tracing |
| `CORS_ORIGINS` | localhost dev | Orígenes permitidos (coma-separados) |
| `APP_ENV` | `development` | `development` / `test` / `production` |

## Licencia

MIT


