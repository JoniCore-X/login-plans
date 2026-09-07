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

Clona y levanta el stack completo (Postgres + Redis + App + Prometheus + Jaeger). La app corre las migraciones automáticamente al arrancar:

```bash
git clone https://github.com/JoniCore-X/login-plans.git
cd login-plans
docker compose up -d
docker compose ps
```

Espera ~30 segundos hasta que `docker compose ps` muestre todo `healthy`. Verifica:

```bash
curl http://localhost:8000/api/v1/health
```

Resultado esperado:

```json
{"status":"healthy","components":{"database":"connected","redis":"connected"}}
```

Todo el flujo de usuario (registro → verificación → login → primer plan) se verifica con un comando, sin depender de quoting de tu shell:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify_install.ps1
```

```bash
bash scripts/verify_install.sh
```

Salida esperada: `INSTALACIÓN VERIFICADA — todos los pasos OK`.

El script registra un usuario, extrae el `VERIFICATION TOKEN` de los logs, verifica el email, hace login y crea un plan. Si prefieres hacerlo manualmente, los endpoints son `POST /api/v1/auth/register`, `POST /api/v1/auth/verify-email`, `POST /api/v1/auth/login` y `POST /api/v1/plans` (ver Swagger en http://localhost:8000/docs).

> **Nota:** la contraseña debe tener mínimo 12 caracteres con mezcla de caracteres (política de seguridad del dominio).

## Desarrollo local (API en tu máquina, datos en Docker)

Para modificar el código con hot reload — setup completo en un solo comando:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\dev_setup.ps1
```

```bash
bash scripts/dev_setup.sh
```

El script crea el venv, instala dependencias, copia `.env`, levanta
Postgres+Redis en Docker y corre las migraciones. Luego arranca la API:

```powershell
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

```bash
./.venv/bin/uvicorn app.main:app --reload --port 8000
```

Requisitos: Python 3.12+, Docker (solo para Postgres/Redis), pip.
> **Consejo Windows:** ejecuta los comandos línea por línea, o usa los scripts
> — pegar bloques enteros en `cmd.exe` puede perder los saltos de línea.

Tests:

```text
pytest -q          # serial
pytest -n auto -q  # paralelo (pytest-xdist)
mypy app
ruff check .
```
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
curl http://localhost:8000/api/v1/health
curl -X POST http://localhost:8000/api/v1/auth/register -H "Content-Type: application/json" -d "{\"email\":\"verify@example.com\",\"password\":\"Strong-password-123!\"}"
```

Health debe responder `{"status":"healthy",...}` y el registro `201`.
Luego: token en logs → verificar email → login → crear plan
(pasos completos en el Quick Start).

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










