#!/usr/bin/env bash
# verify_install.sh — Verificación end-to-end de la instalación.
# Uso: bash scripts/verify_install.sh  (requiere docker compose y curl)
set -euo pipefail
BASE="${BASE:-http://localhost:8000/api/v1}"
EMAIL="demo-$RANDOM@example.com"
PASSWORD="Demo-Password-123!"
ESC=$(printf '\033')

echo "==> Health check"
curl -sf "$BASE/health" | grep -q '"healthy"' && echo "    healthy"

echo "==> Registro ($EMAIL)"
curl -sf -X POST "$BASE/auth/register" -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}" > /dev/null && echo "    201 Created"

echo "==> Token de verificación (logs del contenedor)"
sleep 2
TOKEN=$(docker compose logs app --no-log-prefix 2>/dev/null \
  | sed "s/${ESC}\[[0-9;]*m//g" \
  | sed -n 's/.*TOKEN:[[:space:]]*\([^[:space:]]*\).*/\1/p' | tail -1)
[ -n "$TOKEN" ] || { echo "ERROR: no VERIFICATION TOKEN in logs"; exit 1; }
echo "    token: $TOKEN"

echo "==> Verificar email"
curl -sf -o /dev/null -w "%{http_code}\n" -X POST "$BASE/auth/verify-email" -H "Content-Type: application/json" -d "{\"token\": \"$TOKEN\"}"

echo "==> Login"
CRED=$(curl -sf -X POST "$BASE/auth/login" -H "Content-Type: application/json" -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}" \
  | sed -n 's/.*"credential"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')
[ -n "$CRED" ] || { echo "ERROR: no credential en login"; exit 1; }
echo "    credential obtenida"

echo "==> Crear plan"
curl -sf -X POST "$BASE/plans" -H "Content-Type: application/json" -H "Authorization: Bearer $CRED" -d '{"name": "Plan de prueba"}'

echo ""
echo "INSTALACIÓN VERIFICADA — todos los pasos OK"
