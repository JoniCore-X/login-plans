import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import (
    InMemorySpanExporter,
)

from app.infrastructure.tracing import trace_span


@pytest.fixture
def span_exporter() -> InMemorySpanExporter:
    from app.core.config import get_settings
    from app.core.tracing import setup_tracing

    exporter = InMemorySpanExporter()

    provider = setup_tracing(get_settings())

    provider.add_span_processor(
        SimpleSpanProcessor(exporter),
    )

    return exporter


@pytest.mark.asyncio
async def test_trace_span_creates_span_for_async(
    span_exporter: InMemorySpanExporter,
) -> None:
    @trace_span("test.async_operation")
    async def async_func() -> int:
        return 42

    result = await async_func()

    assert result == 42

    spans = span_exporter.get_finished_spans()
    assert any(span.name == "test.async_operation" for span in spans)


def test_trace_span_creates_span_for_sync(
    span_exporter: InMemorySpanExporter,
) -> None:
    @trace_span("test.sync_operation")
    def sync_func() -> int:
        return 42

    result = sync_func()

    assert result == 42

    spans = span_exporter.get_finished_spans()
    assert any(span.name == "test.sync_operation" for span in spans)


@pytest.mark.asyncio
async def test_trace_span_records_exception(
    span_exporter: InMemorySpanExporter,
) -> None:
    @trace_span("test.failing_operation")
    async def failing() -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError):
        await failing()

    spans = span_exporter.get_finished_spans()
    span = next(s for s in spans if s.name == "test.failing_operation")

    assert span.status.status_code == trace.StatusCode.ERROR
