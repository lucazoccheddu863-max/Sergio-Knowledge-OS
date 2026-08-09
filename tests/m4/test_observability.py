"""Tests for M4.10 — Observability & Operations Adapter."""
from __future__ import annotations

import io
import json
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from skos.m4.infrastructure.ports.metrics_port import MetricsPort
from skos.m4.infrastructure.ports.tracing_port import TracingPort
from skos.m4.infrastructure.ports.logging_port import LoggingPort
from skos.m4.infrastructure.adapters.observability.prometheus_adapter import PrometheusMetricsAdapter
from skos.m4.infrastructure.adapters.observability.opentelemetry_adapter import OpenTelemetryTracerAdapter
from skos.m4.infrastructure.adapters.observability.structured_logging_adapter import StructuredLoggingAdapter
from skos.m4.infrastructure.adapters.api.fastapi_adapter import FastAPIAdapter
from skos.m4.infrastructure.ports.query_orchestrator_port import QueryOrchestratorPort
from skos.m4.infrastructure.ports.config_port import ConfigurationPort


# ── Port Tests ──────────────────────────────────────────────────────────────────

class TestMetricsPort:
    def test_metrics_port_is_abc(self) -> None:
        assert hasattr(MetricsPort, "__abstractmethods__")
        assert "counter" in MetricsPort.__abstractmethods__

class TestTracingPort:
    def test_tracing_port_is_abc(self) -> None:
        assert hasattr(TracingPort, "__abstractmethods__")
        assert "start_span" in TracingPort.__abstractmethods__

class TestLoggingPort:
    def test_logging_port_is_abc(self) -> None:
        assert hasattr(LoggingPort, "__abstractmethods__")
        assert "info" in LoggingPort.__abstractmethods__


# ── PrometheusMetricsAdapter Tests ────────────────────────────────────────────

class TestPrometheusMetricsAdapter:
    def test_counter_increments(self) -> None:
        adapter = PrometheusMetricsAdapter()
        adapter.counter("requests", value=1.0, labels={"method": "GET"})
        adapter.counter("requests", value=2.0, labels={"method": "GET"})
        render = adapter.render()
        assert "requests" in render

    def test_gauge_sets(self) -> None:
        adapter = PrometheusMetricsAdapter()
        adapter.gauge("memory", value=42.0, labels={"host": "localhost"})
        render = adapter.render()
        assert "memory" in render
        assert "42.0" in render

    def test_histogram_observes(self) -> None:
        adapter = PrometheusMetricsAdapter()
        adapter.histogram("latency", value=0.1)
        adapter.histogram("latency", value=0.2)
        render = adapter.render()
        assert "latency" in render

    def test_health_returns_true(self) -> None:
        adapter = PrometheusMetricsAdapter()
        assert adapter.health() is True

    def test_render_empty(self) -> None:
        adapter = PrometheusMetricsAdapter()
        render = adapter.render()
        assert "No metrics" in render or "#" in render


# ── OpenTelemetryTracerAdapter Tests ──────────────────────────────────────────

class TestOpenTelemetryTracerAdapter:
    def test_start_span_returns_handle(self) -> None:
        adapter = OpenTelemetryTracerAdapter(service_name="test")
        span = adapter.start_span("test_span")
        assert span is not None
        adapter.end_span(span)

    def test_record_exception_no_error(self) -> None:
        adapter = OpenTelemetryTracerAdapter(service_name="test")
        span = adapter.start_span("test_span")
        adapter.record_exception(span, ValueError("test"))
        adapter.end_span(span)

    def test_health_returns_true(self) -> None:
        adapter = OpenTelemetryTracerAdapter(service_name="test")
        assert adapter.health() is True


# ── StructuredLoggingAdapter Tests ────────────────────────────────────────────

class TestStructuredLoggingAdapter:
    def test_info_outputs_json(self) -> None:
        buf = io.StringIO()
        adapter = StructuredLoggingAdapter(service_name="test", output=buf)
        adapter.info("hello", user="alice")
        buf.seek(0)
        entry = json.loads(buf.readline())
        assert entry["level"] == "INFO"
        assert entry["message"] == "hello"
        assert entry["user"] == "alice"
        assert "timestamp" in entry

    def test_error_outputs_json(self) -> None:
        buf = io.StringIO()
        adapter = StructuredLoggingAdapter(service_name="test", output=buf)
        adapter.error("boom", code=500)
        buf.seek(0)
        entry = json.loads(buf.readline())
        assert entry["level"] == "ERROR"
        assert entry["message"] == "boom"
        assert entry["code"] == 500

    def test_debug_outputs_json(self) -> None:
        buf = io.StringIO()
        adapter = StructuredLoggingAdapter(service_name="test", output=buf)
        adapter.debug("debug msg")
        buf.seek(0)
        entry = json.loads(buf.readline())
        assert entry["level"] == "DEBUG"

    def test_warning_outputs_json(self) -> None:
        buf = io.StringIO()
        adapter = StructuredLoggingAdapter(service_name="test", output=buf)
        adapter.warning("warn msg")
        buf.seek(0)
        entry = json.loads(buf.readline())
        assert entry["level"] == "WARNING"

    def test_health_returns_true(self) -> None:
        adapter = StructuredLoggingAdapter(service_name="test")
        assert adapter.health() is True


# ── FastAPIAdapter Observability Integration ──────────────────────────────────

@pytest.fixture
def mock_orchestrator() -> Mock:
    return Mock(spec=QueryOrchestratorPort)

@pytest.fixture
def mock_config() -> Mock:
    return Mock(spec=ConfigurationPort)

class TestMetricsEndpoint:
    def test_metrics_endpoint_exists(self, mock_orchestrator: Mock, mock_config: Mock) -> None:
        metrics = PrometheusMetricsAdapter()
        adapter = FastAPIAdapter(orchestrator=mock_orchestrator, config=mock_config, metrics=metrics)
        client = TestClient(adapter.app)
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

    def test_metrics_endpoint_returns_prometheus_format(self, mock_orchestrator: Mock, mock_config: Mock) -> None:
        metrics = PrometheusMetricsAdapter()
        metrics.counter("test_counter", value=5.0)
        adapter = FastAPIAdapter(orchestrator=mock_orchestrator, config=mock_config, metrics=metrics)
        client = TestClient(adapter.app)
        response = client.get("/metrics")
        assert "test_counter" in response.text

    def test_metrics_endpoint_without_metrics(self, mock_orchestrator: Mock, mock_config: Mock) -> None:
        adapter = FastAPIAdapter(orchestrator=mock_orchestrator, config=mock_config)
        client = TestClient(adapter.app)
        response = client.get("/metrics")
        assert response.status_code == 200

class TestHealthWithObservability:
    def test_health_includes_metrics_status(self, mock_orchestrator: Mock, mock_config: Mock) -> None:
        mock_orchestrator.health_check.return_value = True
        metrics = PrometheusMetricsAdapter()
        adapter = FastAPIAdapter(orchestrator=mock_orchestrator, config=mock_config, metrics=metrics)
        client = TestClient(adapter.app)
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["engines"]["metrics"] is True

    def test_health_includes_tracing_status(self, mock_orchestrator: Mock, mock_config: Mock) -> None:
        mock_orchestrator.health_check.return_value = True
        tracer = OpenTelemetryTracerAdapter(service_name="test")
        adapter = FastAPIAdapter(orchestrator=mock_orchestrator, config=mock_config, tracer=tracer)
        client = TestClient(adapter.app)
        response = client.get("/api/v1/health")
        data = response.json()
        assert data["engines"]["tracing"] is True

    def test_health_includes_logging_status(self, mock_orchestrator: Mock, mock_config: Mock) -> None:
        mock_orchestrator.health_check.return_value = True
        logger = StructuredLoggingAdapter(service_name="test")
        adapter = FastAPIAdapter(orchestrator=mock_orchestrator, config=mock_config, logger=logger)
        client = TestClient(adapter.app)
        response = client.get("/api/v1/health")
        data = response.json()
        assert data["engines"]["logging"] is True

    def test_health_without_observability(self, mock_orchestrator: Mock, mock_config: Mock) -> None:
        mock_orchestrator.health_check.return_value = True
        adapter = FastAPIAdapter(orchestrator=mock_orchestrator, config=mock_config)
        client = TestClient(adapter.app)
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "metrics" not in data["engines"]
        assert "tracing" not in data["engines"]
        assert "logging" not in data["engines"]

class TestObservabilityIntegration:
    def test_status_returns_m4_10(self, mock_orchestrator: Mock, mock_config: Mock) -> None:
        adapter = FastAPIAdapter(orchestrator=mock_orchestrator, config=mock_config)
        client = TestClient(adapter.app)
        response = client.get("/api/v1/status")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "0.4.0-alpha13"
        assert data["milestone"] == "M4.11"

    def test_admin_status_returns_m4_10(self, mock_orchestrator: Mock, mock_config: Mock) -> None:
        adapter = FastAPIAdapter(orchestrator=mock_orchestrator, config=mock_config)
        client = TestClient(adapter.app)
        response = client.get("/api/v1/admin/status")
        assert response.status_code == 200
        data = response.json()
        assert data["milestone"] == "M4.11"
