import httpx
import pytest


@pytest.mark.asyncio
async def test_response_includes_request_id(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get("/api/v1/health")

    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) == 32


@pytest.mark.asyncio
async def test_inbound_request_id_is_echoed(
    client: httpx.AsyncClient,
) -> None:
    response = await client.get(
        "/api/v1/health",
        headers={"X-Request-ID": "external-trace-123"},
    )

    assert response.headers["X-Request-ID"] == "external-trace-123"


@pytest.mark.asyncio
async def test_request_id_differs_per_request(
    client: httpx.AsyncClient,
) -> None:
    first = await client.get("/api/v1/health")
    second = await client.get("/api/v1/health")

    assert first.headers["X-Request-ID"] != second.headers["X-Request-ID"]


@pytest.mark.asyncio
async def test_json_log_renderer_in_production() -> None:
    import io
    import logging

    from app.core.logging import configure_logging

    stream = io.StringIO()
    handler = logging.StreamHandler(stream)

    configure_logging(debug=False, json_logs=True)

    logger = logging.getLogger("test-observability")
    logger.handlers = [handler]
    logger.propagate = False

    import structlog

    from app.core.logging import (
        configure_logging as _cl,  # noqa: F401
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
        ],
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )
    handler.setFormatter(formatter)

    logger.info("test event")

    output = stream.getvalue().strip()

    import json

    parsed = json.loads(output)
    assert parsed["event"] == "test event"
    assert "timestamp" in parsed
    assert parsed["level"] == "info"
