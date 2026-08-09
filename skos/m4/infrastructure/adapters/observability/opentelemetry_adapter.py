"""OpenTelemetryTracerAdapter — Infrastructure Adapter for M4.10."""
from __future__ import annotations
from typing import Any
from skos.m4.infrastructure.ports.tracing_port import TracingPort

class _NoOpSpan:
    pass

class OpenTelemetryTracerAdapter(TracingPort):
    def __init__(self, service_name: str = "skos") -> None:
        self._service_name = service_name
        self._tracer = None
        try:
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.sdk.resources import Resource
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            resource = Resource.create({"service.name": service_name})
            provider = TracerProvider(resource=resource)
            processor = BatchSpanProcessor(OTLPSpanExporter())
            provider.add_span_processor(processor)
            trace.set_tracer_provider(provider)
            self._tracer = trace.get_tracer(service_name)
        except ImportError:
            self._tracer = None

    def start_span(self, name: str, context: dict[str, Any] | None = None) -> Any:
        if self._tracer:
            return self._tracer.start_span(name)
        return _NoOpSpan()

    def end_span(self, span: Any) -> None:
        if hasattr(span, "end"):
            span.end()

    def record_exception(self, span: Any, exception: Exception) -> None:
        if hasattr(span, "record_exception"):
            span.record_exception(exception)

    def health(self) -> bool:
        return True
