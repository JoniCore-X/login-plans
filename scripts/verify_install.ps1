# verify_install.ps1 — Verificación end-to-end de la instalación.
# Uso: powershell -ExecutionPolicy Bypass -File scripts\verify_install.ps1
$ErrorActionPreference = "Stop"
$base = "http://localhost:8000/api/v1"
$email = "demo-$(Get-Random)@example.com"
$password = "Demo-Password-123!"

Write-Host "==> Health check"
$health = Invoke-RestMethod "$base/health"
$health | ConvertTo-Json -Compress
if ($health.status -ne "healthy") { throw "health no es healthy" }

Write-Host "==> Registro ($email)"
Invoke-RestMethod -Method Post "$base/auth/register" -ContentType "application/json" -Body (@{ email = $email; password = $password } | ConvertTo-Json) | Out-Null
Write-Host "    201 Created"

Write-Host "==> Token de verificación (logs del contenedor)"
Start-Sleep -Seconds 2
$raw = docker compose logs app --no-log-prefix 2>&1 | Out-String
$clean = $raw -replace "\x1b\[[0-9;]*m", ""
$m = [regex]::Matches($clean, "TOKEN:\s*(\S+)")
if (-not $m) { throw "No se encontró VERIFICATION TOKEN en los logs" }
$token = $m[$m.Count - 1].Groups[1].Value
Write-Host "    token: $token"

Write-Host "==> Verificar email"
Invoke-WebRequest -Method Post "$base/auth/verify-email" -ContentType "application/json" -Body (@{ token = $token } | ConvertTo-Json) -UseBasicParsing | Out-Null
Write-Host "    204 No Content"

Write-Host "==> Login"
$login = Invoke-RestMethod -Method Post "$base/auth/login" -ContentType "application/json" -Body (@{ email = $email; password = $password } | ConvertTo-Json)
Write-Host "    credential obtenida"

Write-Host "==> Crear plan"
$plan = Invoke-RestMethod -Method Post "$base/plans" -ContentType "application/json" -Headers @{ Authorization = "Bearer $($login.credential)" } -Body (@{ name = "Plan de prueba" } | ConvertTo-Json)
Write-Host "    201 Created: $($plan.name) ($($plan.status))"

Write-Host "`nINSTALACIÓN VERIFICADA — todos los pasos OK" -ForegroundColor Green
