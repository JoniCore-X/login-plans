import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

_REQUEST_ID_HEADER = "X-Request-ID"

logger = structlog.get_logger("http.requests")


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get(_REQUEST_ID_HEADER) or uuid.uuid4().hex

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=(
                request.client.host if request.client is not None else "unknown"
            ),
        )

        started_at = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - started_at) * 1000

            await logger.aexception(
                "request_failed",
                duration_ms=round(duration_ms, 2),
            )

            raise
        finally:
            structlog.contextvars.clear_contextvars()

        duration_ms = (time.perf_counter() - started_at) * 1000

        await logger.ainfo(
            "request_completed",
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        response.headers[_REQUEST_ID_HEADER] = request_id

        return response
