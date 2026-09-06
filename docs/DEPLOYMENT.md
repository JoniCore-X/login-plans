# Guía de Despliegue en Producción

Checklist para llevar esta plantilla a producción real. Nada de esto es
opcional si vas a exponer datos de usuarios.

## 1. Secrets — nunca `.env` en producción

- **AWS Secrets Manager / Vault / variables del orquestador** para:
  `DATABASE_URL`, `REDIS_URL`, `RESEND_API_KEY`, `EMAIL_FROM`,
  `OTLP_ENDPOINT`, `CORS_ORIGINS`.
- La app lee `Settings` vía `pydantic-settings` — cualquier variable de
  entorno funciona sin cambios de código.

## 2. Base de datos

- Postgres gestionado (RDS, Supabase, Neon, Cloud SQL).
- Aplicar migraciones como paso de deploy: `alembic upgrade head` con la
  `DATABASE_URL` de producción.
- **Backups**: `pg_dump` programado + retención (7 diarios / 4 semanales /
  12 mensuales) + restore testeado.

## 3. Redis

- Gestionado (ElastiCache, Upstash, MemoryDB).
- Sin `REDIS_URL` la app cae a rate limiting in-memory — **no usar ese
  fallback con más de una instancia**: cada proceso contaría por separado
  y el límite se multiplicaría por N instancias.
- El limiter es fail-closed: si Redis cae, login devuelve 500 — decide si
  ese es tu comportamiento deseado y documéntalo.

## 4. TLS

Reverse proxy delante de la app (nginx/Caddy/ALB) con certificado
Let's Encrypt. La app ya emite security headers
(`SecurityHeadersMiddleware`, incluye HSTS en producción) y sanitiza
errores 500.

```nginx
location / {
    proxy_pass http://app:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

## 5. Email

- `RESEND_API_KEY` + `EMAIL_FROM` con dominio verificado.
- `EMAIL_VERIFY_BASE_URL` apuntando al frontend que hace el POST a
  `/api/v1/auth/verify-email`.
- Sin provider configurado la app usa `ConsoleEmailSender` — aceptable en
  desarrollo, **inaceptable en producción** (los tokens van a los logs).
  En producción el token se enmascara (`***`) pero nadie puede verificar
  su email.

## 6. Observabilidad

- `APP_ENV=production` → logs JSON estructurados a stdout → collector
  (Loki/ELK/CloudWatch).
- `OTLP_ENDPOINT` → Jaeger/Tempo para traces.
- `/metrics` → Prometheus. Protege el endpoint (network rule o auth) —
  hoy es público.
- Alertas mínimas recomendadas:

```yaml
groups:
- name: login_plans
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 2m
  - alert: HighLatencyP95
    expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
    for: 5m
  - alert: AuditFailures
    expr: increase(audit_failures_total[10m]) > 0
  - alert: RateLimitSpike
    expr: rate(rate_limit_hits_total[10m]) > 1
```

## 7. Rate limiting en el borde

Cloudflare/WAF/ALB rules per-IP además del limiter interno (el interno
protege la lógica; el externo protege el ancho de banda).

## 8. Hardening residual del código

- `redis_client.aclose()` en lifespan shutdown (deuda conocida).
- Health endpoint de Redis además del de Postgres si lo necesitas.
- Revisa `docker-compose.yml`: es desarrollo (passwords en claro, tags
  `latest`, puertos expuestos). Para prod usa tu orquestador con secrets.

## Checklist final

- [ ] Secrets en secrets manager
- [ ] DB gestionada + migraciones + backups verificados
- [ ] Redis gestionado (`REDIS_URL` si multi-instancia)
- [ ] TLS terminado en proxy, HTTP→HTTPS redirect
- [ ] `RESEND_API_KEY` + dominio verificado
- [ ] `CORS_ORIGINS` con solo tus orígenes reales
- [ ] `OTLP_ENDPOINT` + collector de logs
- [ ] `/metrics` protegido o en red interna
- [ ] Alertas activas (5xx, p95, audit_failures)
- [ ] Pentest / OWASP ZAP antes de datos reales
- [ ] `docker-compose.yml` NO usado en producción como tal

## Post-deploy

```bash
curl https://api.tudominio.com/api/v1/health
# {"status":"healthy","components":{"database":"connected"}}

curl -X POST https://api.tudominio.com/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"ops@tudominio.com","password":"ChangeMe-1234!"}'
# → verificar que el email llega por el provider real
```
