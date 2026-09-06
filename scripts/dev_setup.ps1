# dev_setup.ps1 — Entorno de desarrollo local en un solo paso.
# Uso: powershell -ExecutionPolicy Bypass -File scripts\dev_setup.ps1
$ErrorActionPreference = "Stop"

Write-Host "==> Entorno virtual"
if (-not (Test-Path .venv)) { python -m venv .venv }
$pip = ".\.venv\Scripts\pip.exe"
$alembic = ".\.venv\Scripts\alembic.exe"
$uvicorn = ".\.venv\Scripts\uvicorn.exe"

Write-Host "==> Dependencias"
& $pip install -r requirements.txt -q

Write-Host "==> Configuración (.env)"
if (-not (Test-Path .env)) { Copy-Item .env.example .env }

Write-Host "==> Postgres + Redis en Docker"
docker compose up -d postgres redis

Write-Host "==> Migraciones"
& $alembic upgrade head

Write-Host "`nSETUP COMPLETO. Arranca la API con:" -ForegroundColor Green
Write-Host "  .\.venv\Scripts\uvicorn app.main:app --reload --port 8000"
