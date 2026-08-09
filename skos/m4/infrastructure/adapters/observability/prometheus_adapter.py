"""PrometheusMetricsAdapter — Infrastructure Adapter for M4.10."""
from __future__ import annotations
from typing import Any
from skos.m4.infrastructure.ports.metrics_port import MetricsPort

class PrometheusMetricsAdapter(MetricsPort):
    def __init__(self) -> None:
        self._prometheus_available = False
        self._registry = None
        self._prom_counters: dict[str, Any] = {}
        self._prom_gauges: dict[str, Any] = {}
        self._prom_histograms: dict[str, Any] = {}
        self._counters: dict[str, dict[frozenset, float]] = {}
        self._gauges: dict[str, dict[frozenset, float]] = {}
        self._histograms: dict[str, dict[frozenset, list[float]]] = {}
        try:
            from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest
            self._prometheus_available = True
            self._registry = CollectorRegistry()
            self._Counter = Counter
            self._Gauge = Gauge
            self._Histogram = Histogram
            self._generate_latest = generate_latest
        except ImportError:
            self._Counter = None
            self._Gauge = None
            self._Histogram = None
            self._generate_latest = None

    def _key(self, labels: dict[str, str] | None) -> frozenset:
        return frozenset((labels or {}).items())

    def counter(self, name: str, value: float = 1.0, labels: dict[str, str] | None = None) -> None:
        key = self._key(labels)
        if self._prometheus_available:
            if name not in self._prom_counters:
                label_names = list(labels.keys()) if labels else []
                self._prom_counters[name] = self._Counter(
                    name, f"Counter {name}", label_names, registry=self._registry
                )
            if labels:
                self._prom_counters[name].labels(**labels).inc(value)
            else:
                self._prom_counters[name].inc(value)
        else:
            self._counters.setdefault(name, {})[key] = self._counters.get(name, {}).get(key, 0.0) + value

    def gauge(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        key = self._key(labels)
        if self._prometheus_available:
            if name not in self._prom_gauges:
                label_names = list(labels.keys()) if labels else []
                self._prom_gauges[name] = self._Gauge(
                    name, f"Gauge {name}", label_names, registry=self._registry
                )
            if labels:
                self._prom_gauges[name].labels(**labels).set(value)
            else:
                self._prom_gauges[name].set(value)
        else:
            self._gauges.setdefault(name, {})[key] = value

    def histogram(self, name: str, value: float, labels: dict[str, str] | None = None) -> None:
        key = self._key(labels)
        if self._prometheus_available:
            if name not in self._prom_histograms:
                label_names = list(labels.keys()) if labels else []
                self._prom_histograms[name] = self._Histogram(
                    name, f"Histogram {name}", label_names, registry=self._registry
                )
            if labels:
                self._prom_histograms[name].labels(**labels).observe(value)
            else:
                self._prom_histograms[name].observe(value)
        else:
            self._histograms.setdefault(name, {}).setdefault(key, []).append(value)

    def render(self) -> str:
        if self._prometheus_available and self._generate_latest and self._registry:
            rendered = self._generate_latest(self._registry).decode("utf-8")
            if rendered.strip():
                return rendered
        lines: list[str] = []
        for name, data in self._counters.items():
            for key, value in data.items():
                label_str = ",".join(f'{k}="{v}"' for k, v in sorted(key))
                lines.append(f"{name}{{{label_str}}} {value}")
        for name, data in self._gauges.items():
            for key, value in data.items():
                label_str = ",".join(f'{k}="{v}"' for k, v in sorted(key))
                lines.append(f"{name}{{{label_str}}} {value}")
        for name, data in self._histograms.items():
            for key, values in data.items():
                label_str = ",".join(f'{k}="{v}"' for k, v in sorted(key))
                for value in values:
                    lines.append(f'{name}_bucket{{{label_str},le="+Inf"}} {value}')
        return "\n".join(lines) if lines else "# No metrics collected yet\n"

    def health(self) -> bool:
        return True
