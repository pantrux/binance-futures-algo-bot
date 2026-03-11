from fastapi.testclient import TestClient

from apps.api.app.core.settings import settings
from apps.api.app.main import app
from apps.api.app.observability.metrics import api_metrics


def test_metrics_endpoint_exposes_runtime_counters():
    api_metrics.reset()
    client = TestClient(app)

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


def test_metrics_endpoint_requires_key_when_configured():
    api_metrics.reset()
    previous_key = settings.metrics_api_key
    settings.metrics_api_key = 'secret-metrics-key'
    client = TestClient(app)

    try:
        unauthorized = client.get('/metrics')
        assert unauthorized.status_code == 401

        authorized = client.get('/metrics', headers={'x-metrics-key': 'secret-metrics-key'})
        assert authorized.status_code == 200
    finally:
        settings.metrics_api_key = previous_key


def test_request_id_header_present_on_unhandled_error_response():
    if not any(route.path == '/__boom' for route in app.router.routes):
        @app.get('/__boom')
        def _boom():
            raise RuntimeError('boom')

    client = TestClient(app)
    response = client.get('/__boom')

    assert response.status_code == 500
    assert response.headers.get('x-request-id')
