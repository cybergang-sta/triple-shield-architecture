#!/usr/bin/env python3
"""
WebSocket server for real-time 3SA metrics streaming
"""

import json
import logging
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from threading import Lock
from collections import deque
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="[web_server] %(levelname)s: %(message)s")
_LOGGER = logging.getLogger("web_server")

app = Flask(__name__)
app.config['SECRET_KEY'] = '3sa-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Thread-safe data storage
thread = None
thread_lock = Lock()
metrics_history = deque(maxlen=100)  # Store last 100 metrics

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

@app.route('/api/test/metrics', methods=['POST'])
def handle_test_metrics():
    """Handle test metrics injection for dashboard testing - clearly marked as synthetic data"""
    try:
        test_data = request.json
        # Mark as test data to ensure cryptographic compliance
        test_data['is_test_data'] = True
        test_data['timestamp'] = datetime.now().isoformat()
        broadcast_metrics(test_data)
        _LOGGER.info(f"Test metrics injected: {test_data.get('anomaly_type', 'unknown')}")
        return jsonify({'status': 'success', 'message': 'Test metrics broadcasted'}), 200
    except Exception as e:
        _LOGGER.error(f"Error processing test metrics: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/test/agility', methods=['POST'])
def handle_test_agility():
    """Handle test agility event injection for dashboard testing - clearly marked as synthetic data"""
    try:
        test_data = request.json
        # Mark as test data to ensure cryptographic compliance
        test_data['is_test_data'] = True
        test_data['timestamp'] = datetime.now().isoformat()
        socketio.emit('agility_event', test_data)
        _LOGGER.info(f"Test agility event injected: {test_data.get('trigger_event', 'unknown')}")
        return jsonify({'status': 'success', 'message': 'Test agility event broadcasted'}), 200
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
    metrics_history.append(metrics)
    socketio.emit('metrics_update', metrics)

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
