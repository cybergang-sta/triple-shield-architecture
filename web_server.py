#!/usr/bin/env python3
"""
WebSocket server for real-time 3SA metrics streaming
"""

import json
import logging
import os
import subprocess
import sys
import time
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

@app.route('/api/test/handshake', methods=['POST'])
def handle_test_handshake():
    """Trigger a real 3SA handshake with a synthetic anomaly scenario."""
    try:
        request_body = request.get_json(silent=True) or {}
        anomaly_type = request_body.get('anomaly_type', 'normal')
        session_id = request_body.get('session_id', 'dashboard-test')
        _run_test_handshake(anomaly_type, session_id)
        return jsonify({'status': 'success', 'anomaly_type': anomaly_type}), 200
    except Exception as e:
        _LOGGER.error(f"Error processing test handshake: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/api/test/agility', methods=['POST'])
def handle_test_agility():
    """Emit a synthetic agility transition event for dashboard testing."""
    try:
        agility_data = request.get_json(silent=True) or {}
        agility_data.setdefault('event_type', 'manual_override')
        agility_data.setdefault('old_suite', 'TLS_X25519_ML_KEM_768_WITH_AES_256_GCM_SHA3_256')
        agility_data.setdefault('new_suite', 'TLS_X25519_ML_KEM_768_WITH_AES_256_GCM_SHA3_256')
        agility_data.setdefault('anomaly_score', 0.05)
        agility_data['timestamp'] = datetime.now().isoformat()
        socketio.emit('agility_event', agility_data)
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        _LOGGER.error(f"Error processing test agility event: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 400


def _run_test_handshake(anomaly_type: str, session_id: str):
    """Launch the real 3SA handshake script with a scenario override."""
    script_path = os.path.join(os.path.dirname(__file__), '3SA.py')
    if anomaly_type == 'repeated_failure':
        for _ in range(3):
            subprocess.run(
                [sys.executable, script_path, '--web-dashboard', '--test-scenario', 'failure', '--session-id', session_id],
                cwd=os.path.dirname(__file__),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
            time.sleep(0.2)
        return

    subprocess.Popen(
        [sys.executable, script_path, '--web-dashboard', '--test-scenario', anomaly_type, '--session-id', session_id],
        cwd=os.path.dirname(__file__),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

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
