from fastapi.testclient import TestClient

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
