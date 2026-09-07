#!/usr/bin/env bash
# dev_setup.sh — Entorno de desarrollo local en un solo paso.
# Uso: bash scripts/dev_setup.sh
set -euo pipefail

echo "==> Entorno virtual"
[ -d .venv ] || python -m venv .venv

echo "==> Dependencias"
./.venv/bin/pip install -r requirements.txt -q

echo "==> Configuración (.env)"
[ -f .env ] || cp .env.example .env

echo "==> Postgres + Redis en Docker"
docker compose up -d postgres redis

echo "==> Migraciones"
./.venv/bin/alembic upgrade head

echo ""
echo "SETUP COMPLETO. Arranca la API con:"
echo "  ./.venv/bin/uvicorn app.main:app --reload --port 8000"
