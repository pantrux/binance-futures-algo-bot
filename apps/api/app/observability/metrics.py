from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class ApiMetricsRegistry:
    """Registro in-memory de métricas operativas del API.

    Nota: se mantiene una API síncrona para reutilizarla desde rutas FastAPI (`def`) y
    desde tests. En middleware async se invoca vía `asyncio.to_thread(...)` para evitar
    bloquear el event loop durante la sección crítica del lock.
    """
    _lock: Lock = field(default_factory=Lock, init=False, repr=False)
    _total_requests: int = 0
    _total_errors: int = 0
    _status_codes: Counter[str] = field(default_factory=Counter)
    _routes: Counter[str] = field(default_factory=Counter)
    _latency_ms_total: float = 0.0
    _latency_ms_max: float = 0.0

    def record(self, *, method: str, path: str, status_code: int, latency_ms: float) -> None:
        route_key = f"{method.upper()} {path}"
        status_key = str(status_code)

        with self._lock:
            self._total_requests += 1
            if status_code >= 500:
                self._total_errors += 1
            self._status_codes[status_key] += 1
            self._routes[route_key] += 1
            self._latency_ms_total += latency_ms
            self._latency_ms_max = max(self._latency_ms_max, latency_ms)

    def snapshot(self) -> dict:
        with self._lock:
            avg_latency_ms = self._latency_ms_total / self._total_requests if self._total_requests else 0.0
            return {
                "total_requests": self._total_requests,
                "total_errors": self._total_errors,
                "error_rate_pct": round((self._total_errors / self._total_requests) * 100.0, 4)
                if self._total_requests
                else 0.0,
                "latency_ms_avg": round(avg_latency_ms, 4),
                "latency_ms_max": round(self._latency_ms_max, 4),
                "status_codes": dict(self._status_codes),
                "routes": dict(self._routes),
            }

    def reset(self) -> None:
        with self._lock:
            self._total_requests = 0
            self._total_errors = 0
            self._status_codes.clear()
            self._routes.clear()
            self._latency_ms_total = 0.0
            self._latency_ms_max = 0.0


api_metrics = ApiMetricsRegistry()
