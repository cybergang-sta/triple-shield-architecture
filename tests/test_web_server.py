import pytest

from web_server import app, metrics_history


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_test_handshake_endpoint_broadcasts_metrics(client):
    metrics_history.clear()

    response = client.post('/api/test/handshake', json={'anomaly_type': 'high_latency'})

    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert len(metrics_history) == 1

    payload = metrics_history[-1]
    assert payload['is_test_data'] is True
    assert payload['anomaly_type'] == 'high_latency'
    assert payload['alice_kem_keygen_ns'] > 0
    assert payload['bob_encap_ns'] > 0
    assert payload['alice_decap_ns'] > 0


def test_test_agility_endpoint_returns_next_suite(client):
    response = client.post('/api/test/agility', json={
        'event_type': 'manual_override',
        'old_suite': 'TLS_X25519_ML_KEM_768_WITH_AES_256_GCM_SHA3_256',
        'anomaly_score': 0.96,
    })

    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert data['new_suite'] == 'TLS_X25519_ML_KEM_1024_WITH_AES_256_GCM_SHA3_256'
    assert data['session_keys_preserved'] is True
    assert data['rekey_strategy'] == 'stateful_re_negotiation'


def test_test_agility_endpoint_does_not_repeat_previous_suite(client):
    first_response = client.post('/api/test/agility', json={
        'event_type': 'manual_override',
        'old_suite': 'TLS_X25519_ML_KEM_768_WITH_AES_256_GCM_SHA3_256',
        'anomaly_score': 0.96,
        'session_id': 'test-session-1',
    })
    second_response = client.post('/api/test/agility', json={
        'event_type': 'manual_override',
        'old_suite': 'TLS_X25519_ML_KEM_768_WITH_AES_256_GCM_SHA3_256',
        'anomaly_score': 0.05,
        'session_id': 'test-session-1',
    })

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    first_suite = first_response.get_json()['new_suite']
    second_suite = second_response.get_json()['new_suite']
    assert first_suite == 'TLS_X25519_ML_KEM_1024_WITH_AES_256_GCM_SHA3_256'
    assert second_suite == 'TLS_X25519_WITH_AES_256_GCM_SHA3_256'


def test_test_metrics_endpoint_labels_resource_exhaustion(client):
    metrics_history.clear()

    response = client.post('/api/test/metrics', json={
        'total_latency_ms': 55.0,
        'success': True,
        'suite': 'TLS_X25519_ML_KEM_768_WITH_AES_256_GCM_SHA3_256',
    })

    assert response.status_code == 200
    payload = metrics_history[-1]
    assert payload['anomaly_type'] == 'resource_exhaustion'
