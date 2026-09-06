from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

_instrumentator: Instrumentator | None = None


def _get_instrumentator() -> Instrumentator:
    global _instrumentator

    if _instrumentator is None:
        _instrumentator = Instrumentator(
            should_group_status_codes=True,
            should_ignore_untemplated=True,
            should_instrument_requests_inprogress=True,
            excluded_handlers=[
                "/metrics",
                "/api/v1/health",
            ],
        )

    return _instrumentator


_instrumented = False


def setup_metrics(app: FastAPI) -> None:
    global _instrumented

    instrumentator = _get_instrumentator()

    if not _instrumented:
        instrumentator.instrument(app)
        _instrumented = True

    instrumentator.expose(
        app,
        endpoint="/metrics",
        include_in_schema=False,
        should_gzip=True,
    )
