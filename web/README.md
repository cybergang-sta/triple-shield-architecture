# 3SA Real-time Dashboard

A React-based real-time dashboard for visualizing the Triple-Shield Architecture (3SA) process, including throughput metrics, overhead analysis, and anomaly detection.

## Features

- **Real-time Metrics**: Live updates of handshake latency, key sizes, and anomaly scores
- **Throughput Visualization**: Line charts showing handshake throughput over time
- **Overhead Comparison**: Bar charts comparing key sizes across different cipher suites
- **Process Flow**: Visual representation of the handshake process steps
- **Anomaly Alerts**: Real-time alerts when anomalies are detected by the AI system
- **Connection Status**: Live WebSocket connection indicator

## Architecture

### Backend (Flask + WebSocket)
- `web_server.py`: Flask server with SocketIO for real-time data streaming
- Accepts metrics via POST endpoint `/api/metrics`
- Broadcasts metrics to connected clients via WebSocket
- Stores last 100 metrics in memory for historical data

### Frontend (React)
- React 18 with modern hooks
- Socket.io-client for WebSocket communication
- Recharts for data visualization
- Responsive design with CSS Grid and Flexbox

## Installation

### Prerequisites
- Node.js 16+ and npm
- Python 3.10+
- pip

### Backend Setup

1. Install Python dependencies:
```bash
cd ..
pip install -r requirements.txt
```

2. Start the WebSocket server:
```bash
python web_server.py
```

The server will start on `http://localhost:5000`

### Frontend Setup

1. Navigate to the web directory:
```bash
cd web
```

2. Install Node.js dependencies:
```bash
npm install
```

3. Start the React development server:
```bash
npm start
```

The dashboard will be available at `http://localhost:3000`

## Usage

### Running 3SA with Dashboard Integration

1. Start the WebSocket server:
```bash
python web_server.py
```

2. Start the React dashboard (in a separate terminal):
```bash
cd web
npm start
```

3. Run 3SA with web dashboard enabled:
```bash
python 3SA.py --kem ML-KEM-768 --web-dashboard
```

The dashboard will now receive real-time metrics from each handshake.

### Dashboard Components

**Metrics Cards**
- Total Latency: Handshake completion time in milliseconds
- Public Key Size: Size of the post-quantum public key in bytes
- Ciphertext Size: Size of the encapsulated key material in bytes
- Anomaly Score: AI detection confidence (0.0 = normal, 1.0 = anomalous)

**Charts**
- Throughput Chart: Line chart showing handshakes per second over time
- Overhead Chart: Bar chart comparing key sizes across cipher suites

**Process Flow**
- Visual representation of handshake steps with timing information

**Anomaly Alerts**
- Red alert banner when anomaly score exceeds 0.6 threshold
- Shows anomaly type and score

## Data Flow

```
3SA.py (with --web-dashboard)
  ↓ HTTP POST
web_server.py (/api/metrics)
  ↓ WebSocket
React Dashboard (real-time updates)
```

## Customization

### Adding New Metrics

1. Add metric to `3SA.py` in the `broadcast_metrics()` function
2. Update the `HandshakeMetrics` component to display the new metric
3. Add corresponding visualization if needed

### Styling

All styles are in component-specific CSS files:
- `App.css`: Main application styles
- `MetricsCard.css`: Metric card styling
- `ThroughputChart.css`: Chart container styling
- `OverheadChart.css`: Chart container styling
- `HandshakeProcess.css`: Process flow styling
- `AnomalyAlert.css`: Alert banner styling

## Troubleshooting

**WebSocket Connection Issues**
- Ensure `web_server.py` is running on port 5000
- Check browser console for WebSocket errors
- Verify CORS settings in `web_server.py`

**No Data Displayed**
- Ensure 3SA is running with `--web-dashboard` flag
- Check that metrics are being sent to `/api/metrics`
- Verify WebSocket connection status in dashboard header

**React Build Errors**
- Ensure all dependencies are installed: `npm install`
- Check Node.js version (requires 16+)
- Clear cache: `npm start -- --reset-cache`

## Production Deployment

For production deployment:

1. Build the React application:
```bash
cd web
npm run build
```

2. Serve the built files with the Flask server by updating `web_server.py`:
```python
@app.route('/')
def index():
    return send_from_directory('web/build', 'index.html')
```

3. Use a production WSGI server like Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 web_server:app
```

## Technical Details

### WebSocket Events
- `connect`: Client connects to server
- `disconnect`: Client disconnects from server
- `metrics_update`: Server broadcasts new metrics to all clients

### API Endpoints
- `GET /api/metrics`: Returns historical metrics
- `POST /api/metrics`: Accepts new metrics for broadcasting

### Metrics Schema
```json
{
  "total_latency_ms": 2.5,
  "ciphertext_size_bytes": 1088,
  "public_key_size_bytes": 1184,
  "success": true,
  "encap_variance": 0.0,
  "anomaly_score": 0.15,
  "suite": "TLS_X25519_ML_KEM_768_WITH_AES_256_GCM_SHA3_256",
  "timestamp": "2026-07-01T02:45:00.000000"
}
```

## License

This dashboard is part of the Triple-Shield Architecture project.
