#!/usr/bin/env python3
"""
WebSocket server for real-time 3SA metrics streaming
"""

import json
import logging
import os
import subprocess
import sys
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from threading import Lock
from collections import deque
from datetime import datetime

SESSION_SUITE_HISTORY = {}

logging.basicConfig(level=logging.INFO, format="[web_server] %(levelname)s: %(message)s")
_LOGGER = logging.getLogger("web_server")

app = Flask(__name__)
app.config['SECRET_KEY'] = '3sa-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Thread-safe data storage
thread = None
thread_lock = Lock()
metrics_history = deque(maxlen=100)  # Store last 100 metrics


def infer_anomaly_type(metrics):
    """Infer a human-readable anomaly type from handshake metrics."""
    if not metrics:
        return 'normal'

    latency = metrics.get('total_latency_ms')
    if latency is not None and float(latency) > 50.0:
        return 'resource_exhaustion'

    if metrics.get('anomaly_type'):
        return metrics.get('anomaly_type')

    if metrics.get('success') is False:
        return 'failure'

    return 'normal'


def build_test_metrics(anomaly_type='normal', base_metrics=None):
    """Create a synthetic metrics payload with the handshake timings the React UI expects."""
    payload = {
        'total_latency_ms': 2.5,
        'ciphertext_size_bytes': 1088,
        'public_key_size_bytes': 1184,
        'success': True,
        'encap_variance': 0.0,
        'suite': 'TLS_X25519_ML_KEM_768_WITH_AES_256_GCM_SHA3_256',
        'anomaly_type': anomaly_type,
        'anomaly_score': 0.15,
        'is_test_data': True,
        'alice_kem_keygen_ns': 1_800_000,
        'bob_encap_ns': 1_400_000,
        'alice_decap_ns': 1_200_000,
        'hkdf_ns': 500_000,
    }

    if anomaly_type == 'high_latency':
        payload.update({
            'total_latency_ms': 18.5,
            'anomaly_score': 0.82,
            'success': True,
        })
    elif anomaly_type == 'size_mismatch':
        payload.update({
            'ciphertext_size_bytes': 1500,
            'public_key_size_bytes': 1400,
            'anomaly_score': 0.91,
            'success': True,
        })
    elif anomaly_type in ('failure', 'repeated_failure'):
        payload.update({
            'total_latency_ms': 22.0,
            'anomaly_score': 0.96,
            'success': False,
        })

    if base_metrics:
        payload.update(base_metrics)

    return payload


@app.route('/')
def index():
    return "3SA WebSocket Server - React frontend should be served separately"

@app.route('/api/metrics', methods=['GET', 'POST'])
def handle_metrics():
    """Handle metrics - GET for history, POST for new metrics"""
    if request.method == 'POST':
        try:
            metrics = request.json
            broadcast_metrics(metrics)
            return jsonify({'status': 'success'}), 200
        except Exception as e:
            _LOGGER.error(f"Error processing metrics: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 400
    else:
        return jsonify({'metrics': list(metrics_history)})

@app.route('/api/agility', methods=['POST'])
def handle_agility():
    """Handle agility events - POST for new agility transitions"""
    try:
        agility_data = request.json
        agility_data['timestamp'] = datetime.now().isoformat()
        socketio.emit('agility_event', agility_data)
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        _LOGGER.error(f"Error processing agility event: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/test/handshake', methods=['POST'])
def handle_test_handshake():
    """Handle test-handshake injection for the React dashboard."""
    try:
        payload = request.json or {}
        anomaly_type = payload.get('anomaly_type', 'normal')
        test_data = build_test_metrics(anomaly_type=anomaly_type)
        test_data['timestamp'] = datetime.now().isoformat()
        broadcast_metrics(test_data)
        _LOGGER.info(f"Test handshake injected: {anomaly_type}")
        return jsonify({'status': 'success', 'message': 'Test handshake broadcasted'}), 200
    except Exception as e:
        _LOGGER.error(f"Error processing test handshake: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400


@app.route('/api/test/metrics', methods=['POST'])
def handle_test_metrics():
    """Handle test metrics injection for dashboard testing - clearly marked as synthetic data"""
    try:
        test_data = request.json or {}
        anomaly_type = test_data.get('anomaly_type', 'normal')
        test_data = build_test_metrics(anomaly_type=anomaly_type, base_metrics=test_data)
        test_data['timestamp'] = datetime.now().isoformat()
        broadcast_metrics(test_data)
        _LOGGER.info(f"Test metrics injected: {anomaly_type}")
        return jsonify({'status': 'success', 'message': 'Test metrics broadcasted'}), 200
    except Exception as e:
        _LOGGER.error(f"Error processing test metrics: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/test/agility', methods=['POST'])
def handle_test_agility():
    """Handle test agility event injection for dashboard testing - clearly marked as synthetic data"""
    try:
        test_data = request.json or {}
        old_suite = test_data.get('old_suite') or test_data.get('from_suite') or test_data.get('suite')
        session_id = test_data.get('session_id', 'default')
        new_suite = test_data.get('new_suite') or get_next_suite(old_suite, session_id=session_id)

        if new_suite:
            test_data['new_suite'] = new_suite
        if old_suite:
            test_data['old_suite'] = old_suite

        test_data['is_test_data'] = True
        test_data['timestamp'] = datetime.now().isoformat()
        test_data['session_keys_preserved'] = True
        test_data['rekey_strategy'] = 'stateful_re_negotiation'
        test_data['stateful_note'] = 'Session keys remain active until the next safe re-negotiation boundary.'
        socketio.emit('agility_event', test_data)
        _LOGGER.info(f"Test agility event injected: {test_data.get('trigger_event', 'unknown')}")
        return jsonify({
            'status': 'success',
            'message': 'Test agility event broadcasted',
            'new_suite': new_suite,
            'session_keys_preserved': True,
            'rekey_strategy': 'stateful_re_negotiation',
        }), 200
    except Exception as e:
        _LOGGER.error(f"Error processing test agility event: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/test/scenarios', methods=['GET'])
def get_test_scenarios():
    """Return predefined test scenarios for dashboard testing - synthetic data only"""
    scenarios = {
        'normal': {
            'description': 'Normal handshake with expected metrics',
            'metrics': {
                'total_latency_ms': 2.5,
                'ciphertext_size_bytes': 1088,
                'public_key_size_bytes': 1184,
                'success': True,
                'encap_variance': 0.0,
                'anomaly_score': 0.15,
                'suite': 'TLS_X25519_ML_KEM_768_WITH_AES_256_GCM_SHA3_256',
                'anomaly_type': 'normal'
            }
        },
        'timing_attack': {
            'description': 'Simulated timing attack with elevated latency',
            'metrics': {
                'total_latency_ms': 15.8,
                'ciphertext_size_bytes': 1088,
                'public_key_size_bytes': 1184,
                'success': True,
                'encap_variance': 0.0,
                'anomaly_score': 0.85,
                'suite': 'TLS_X25519_ML_KEM_768_WITH_AES_256_GCM_SHA3_256',
                'anomaly_type': 'timing_anomaly'
            }
        },
        'size_tampering': {
            'description': 'Simulated size tampering with incorrect key sizes',
            'metrics': {
                'total_latency_ms': 2.5,
                'ciphertext_size_bytes': 1500,
                'public_key_size_bytes': 1400,
                'success': True,
                'encap_variance': 0.0,
                'anomaly_score': 0.92,
                'suite': 'TLS_X25519_ML_KEM_768_WITH_AES_256_GCM_SHA3_256',
                'anomaly_type': 'size_tampering'
            }
        },
        'agility_transition': {
            'description': 'Simulated agility event triggering suite transition',
            'agility': {
                'event_type': 'agility_transition',
                'trigger_event': 'HIGH_ANOMALY_SCORE',
                'old_suite': 'TLS_X25519_ML_KEM_768_WITH_AES_256_GCM_SHA3_256',
                'new_suite': 'TLS_X25519_ML_KEM_1024_WITH_AES_256_GCM_SHA3_256',
                'anomaly_score': 0.88
            }
        }
    }
    return jsonify({'scenarios': scenarios, 'note': 'All scenarios use synthetic test data only'}), 200

@socketio.on('connect')
def handle_connect():
    _LOGGER.info(f"Client connected: {request.sid}")
    emit('connected', {'data': 'Connected to 3SA WebSocket server'})

@socketio.on('disconnect')
def handle_disconnect():
    _LOGGER.info(f"Client disconnected: {request.sid}")

def broadcast_metrics(metrics):
    """Broadcast metrics to all connected clients"""
    metrics['timestamp'] = datetime.now().isoformat()
    metrics['anomaly_type'] = infer_anomaly_type(metrics)
    metrics_history.append(metrics)
    socketio.emit('metrics_update', metrics)

def get_next_suite(current_suite: str | None = None, session_id: str | None = None) -> str | None:
    """Return the next fallback suite for a manual or automated agility transition."""
    try:
        with open(os.path.join(os.path.dirname(__file__), 'policy.json'), 'r', encoding='utf-8') as handle:
            policy = json.load(handle)
    except Exception:
        return current_suite

    fallback_order = policy.get('fallback_order', [])
    if not fallback_order:
        return current_suite
    if not current_suite:
        return fallback_order[0]

    session_key = session_id or 'default'
    visited = SESSION_SUITE_HISTORY.get(session_key, [])

    preferred = None
    for suite in fallback_order:
        if suite == current_suite:
            continue
        if suite in visited:
            continue
        preferred = suite
        break

    if preferred is not None:
        SESSION_SUITE_HISTORY[session_key] = visited + [current_suite] if current_suite not in visited else visited
        SESSION_SUITE_HISTORY[session_key].append(preferred)
        return preferred

    if current_suite in fallback_order:
        try:
            index = fallback_order.index(current_suite)
        except ValueError:
            return fallback_order[0]
        return fallback_order[min(index + 1, len(fallback_order) - 1)]

    return fallback_order[0]


def start_background_thread():
    """Start background thread for metrics broadcasting"""
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_task)

def background_task():
    """Background task for periodic updates"""
    while True:
        socketio.sleep(1)  # Heartbeat
        # Could add periodic summary statistics here

if __name__ == '__main__':
    _LOGGER.info("Starting 3SA WebSocket server on http://localhost:5000")
    start_background_thread()
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
