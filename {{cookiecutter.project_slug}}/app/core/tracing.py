from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
    OTLPSpanExporter,
)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import (
    SQLAlchemyInstrumentor,
)
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SpanExporter,
)
from opentelemetry.semconv.resource import ResourceAttributes
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.config import Settings

_provider: TracerProvider | None = None


def setup_tracing(settings: Settings) -> TracerProvider:
    global _provider

    if _provider is not None:
        return _provider

    resource = Resource.create(
        {
            ResourceAttributes.SERVICE_NAME: settings.app_name,
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: settings.app_env,
        },
    )

    provider = TracerProvider(resource=resource)

    if settings.otlp_endpoint:
        exporter: SpanExporter | None = OTLPSpanExporter(
            endpoint=settings.otlp_endpoint,
        )
    elif settings.app_env == "test":
        exporter = None
    else:
        exporter = ConsoleSpanExporter()

    if exporter is not None:
        provider.add_span_processor(
            BatchSpanProcessor(exporter),
        )

    trace.set_tracer_provider(provider)

    _provider = provider

    return provider


def instrument_app(
    app: FastAPI,
    engine: AsyncEngine,
) -> None:
    _patch_route_details_for_lazy_routers()

    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls="health,metrics",
    )

    SQLAlchemyInstrumentor().instrument(
        engine=engine.sync_engine,
    )

    RedisInstrumentor().instrument()


def _patch_route_details_for_lazy_routers() -> None:
    from typing import Any

    import opentelemetry.instrumentation.fastapi as otel_fastapi

    original = otel_fastapi._get_route_details

    def safe_get_route_details(
        scope: dict[str, Any],
    ) -> object:
        try:
            return original(scope)  # type: ignore[no-untyped-call]
        except AttributeError:
            return scope.get("path")

    otel_fastapi._get_route_details = safe_get_route_details
