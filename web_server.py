#!/usr/bin/env python3
"""
WebSocket server for real-time 3SA metrics streaming
"""

import json
import logging
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
