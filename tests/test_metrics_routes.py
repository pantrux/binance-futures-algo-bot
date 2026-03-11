import apps.api.app.api.routes as api_routes
import apps.api.app.main as app_main
import apps.api.app.observability.metrics as metrics_module
from fastapi.testclient import TestClient
from pydantic import SecretStr

from apps.api.app.core.settings import settings
from apps.api.app.main import create_app
from apps.api.app.observability.metrics import ApiMetricsRegistry


def _isolate_metrics_registry(monkeypatch) -> ApiMetricsRegistry:
    fresh_metrics = ApiMetricsRegistry()
    monkeypatch.setattr(metrics_module, 'api_metrics', fresh_metrics)
    monkeypatch.setattr(app_main, 'api_metrics', fresh_metrics)
    monkeypatch.setattr(api_routes, 'api_metrics', fresh_metrics)
    return fresh_metrics


def test_metrics_endpoint_exposes_runtime_counters(monkeypatch):
    _isolate_metrics_registry(monkeypatch)
    client = TestClient(create_app())

    health = client.get('/health')
    assert health.status_code == 200

    metrics = client.get('/metrics')
    assert metrics.status_code == 200

    payload = metrics.json()
    assert payload['total_requests'] >= 1
    assert '200' in payload['status_codes']
    assert 'GET /health' in payload['routes']
    assert 'latency_ms_avg' in payload
    assert payload['latency_ms_avg'] >= 0


def test_metrics_endpoint_requires_key_when_configured(monkeypatch):
    _isolate_metrics_registry(monkeypatch)
    monkeypatch.setattr(settings, 'metrics_api_key', SecretStr('secret-metrics-key'))
    client = TestClient(create_app())

    unauthorized = client.get('/metrics')
    assert unauthorized.status_code == 401

    authorized = client.get('/metrics', headers={'x-metrics-key': 'secret-metrics-key'})
    assert authorized.status_code == 200


def test_request_id_header_present_on_unhandled_error_response(monkeypatch):
    _isolate_metrics_registry(monkeypatch)
    test_app = create_app()

    @test_app.get('/__boom')
    def _boom():
        raise RuntimeError('boom')

    client = TestClient(test_app)
    response = client.get('/__boom')

    assert response.status_code == 500
    assert response.headers.get('x-request-id')
