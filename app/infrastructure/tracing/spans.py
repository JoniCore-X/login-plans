import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

F = TypeVar("F", bound=Callable[..., Any])


def trace_span(name: str) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(
                *args: Any,
                **kwargs: Any,
            ) -> Any:
                tracer = trace.get_tracer(func.__module__)

                with tracer.start_as_current_span(name) as span:
                    try:
                        return await func(*args, **kwargs)
                    except Exception as exc:
                        span.record_exception(exc)
                        span.set_status(
                            Status(StatusCode.ERROR, str(exc)),
                        )
                        raise

            return async_wrapper  # type: ignore[return-value]

        @wraps(func)
        def sync_wrapper(
            *args: Any,
            **kwargs: Any,
        ) -> Any:
            tracer = trace.get_tracer(func.__module__)

            with tracer.start_as_current_span(name) as span:
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    span.record_exception(exc)
                    span.set_status(
                        Status(StatusCode.ERROR, str(exc)),
                    )
                    raise

        return sync_wrapper  # type: ignore[return-value]

    return decorator
