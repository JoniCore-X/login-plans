# Guía de Customización

Cómo adaptar esta plantilla a tu proyecto. Todos los ejemplos usan la
estructura real del repo — verifica contra `AGENTS.md` antes de extender.

## 1. Configurar Email Real

Por defecto el sistema usa `ConsoleEmailSender`
(`app/infrastructure/email/console_sender.py`), que imprime el token de
verificación en los logs de la app. Para producción, necesitas un proveedor
real.

El puerto ya está definido en `app/application/ports/email_sender.py`:

```python
class EmailSender(ABC):
    @abstractmethod
    async def send_verification_email(
        self,
        to: str,
        token: str,
    ) -> None: ...
```

### Opción A: Resend (ya implementado)

Ventajas: 3.000 emails/mes gratis, API REST simple, dashboard moderno.

1. Regístrate en [resend.com](https://resend.com)
2. Verifica tu dominio
3. Genera API key en Dashboard → API Keys
4. Agrega a `.env`:

   ```env
   RESEND_API_KEY=re_xxxxxxxxxxxxx
   EMAIL_FROM=noreply@tudominio.com
   EMAIL_VERIFY_BASE_URL=https://tudominio.com/verify
   ```

5. Reinicia: `docker compose up -d --build app`

El adaptador está en `app/infrastructure/email/resend_sender.py` con tests
en `tests/infrastructure/test_resend_sender.py`. El container lo selecciona
automáticamente cuando `RESEND_API_KEY` está presente
(`app/bootstrap/container.py`).

Nota: `EMAIL_VERIFY_BASE_URL` debe apuntar a tu frontend (el endpoint
`/api/v1/auth/verify-email` es POST con JSON `{"token": "..."}`; el link del
email debe dirigir a una página que haga ese POST).

### Opción B: SendGrid (ejercicio guiado)

1. Regístrate, verifica dominio, genera API key.
2. Crea `app/infrastructure/email/sendgrid_sender.py` implementando el
   puerto `EmailSender` contra la API v3 de SendGrid (mismo patrón que
   `ResendEmailSender`: httpx, `Authorization: Bearer`, `raise_for_status`).
3. Agrega `sendgrid_api_key: str | None = None` a `Settings`.
4. En `app/bootstrap/container.py`, añade la rama condicional
   `settings.sendgrid_api_key → SendGridEmailSender`.
5. Replica los tests de `test_resend_sender.py` adaptados al payload de
   SendGrid.

### Opción C: AWS SES

Mismo patrón con `boto3` (`client('ses').send_email`). Requiere salir del
sandbox mode para enviar a direcciones no verificadas.

## 2. Agregar un Nuevo Agregado

Sigue la receta de 10 pasos de `AGENTS.md` Sección 4 (ejemplo: `Project`).
Puntos críticos:

- Las invariantes viven en la entidad del dominio, no en el servicio.
- Los repositorios son puertos en `app/domain/repositories/`; la
  implementación SQLAlchemy va en `app/infrastructure/persistence/` con un
  mapper separado (`persistence/mappers/`).
- Los eventos se recolectan con `unit_of_work.collect_event(...)` — el
  audit trail con `request_id` es automático.
- Los tests de arquitectura verificarán que no importes `infrastructure`
  desde `application` o `domain`.

## 3. Emitir un Nuevo Evento de Dominio

1. Define el evento en `app/domain/events/` (dataclass frozen con
   `occurred_at` y campos del dominio).
2. Emítelo dentro del aggregate: `self.register_event(MiEvento(...))`.
3. En el servicio: `for event in aggregate.pull_events(): unit_of_work.collect_event(event)`.
4. `AuditLogDispatcher` lo persiste automáticamente en `audit_logs` con el
   `request_id` del contexto — sin trabajo adicional.
5. Si quieres métrica: añade un Counter en `app/application/metrics.py` y
   `.inc()` en el servicio.

## 4. Modificar la Password Policy

La política vive en `PlainPassword`
(`app/domain/users/value_objects.py`): longitud mínima, mezcla de
caracteres y rechazo de contraseñas comunes. Cambia las invariantes ahí —
todos los tests de política apuntan a ese VO.

## 5. Rate Limiting

Los límites actuales están en `app/bootstrap/container.py`
(`LOGIN_RATE_LIMIT = 10`, `LOGIN_RATE_LIMIT_WINDOW = 5 min`).

Para exponerlos como configuración: añade campos a `Settings`
(`app/core/config.py`) y pásalos al constructor del limiter en el
container — mismo patrón que `redis_url`.

## 6. Agregar un Middleware

1. Crea `app/api/middleware/tu_middleware.py` extendiendo
   `BaseHTTPMiddleware` (ver `request_id.py` como referencia).
2. Regístralo en `app/bootstrap/application.py` con
   `application.add_middleware(...)`. Orden: los últimos registrados corren
   más afuera (primero en recibir el request).
3. Testéalo con el `client` fixture de `tests/conftest.py`.

## Contribuir

Si mejoras la plantilla:

```bash
git checkout -b feature/tu-feature
# ... cambios + tests ...
pytest -q && mypy app && ruff check . && ruff format --check .
git commit -m "feat: descripción"
git push origin feature/tu-feature
# Abrir Pull Request
```

Requisitos para PR: todos los tests passing, mypy/ruff limpios,
documentación actualizada.
