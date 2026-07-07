import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
import axios from 'axios';
import Dashboard from './pages/Dashboard';
import './App.css';

const socket = io('http://localhost:5000');

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [agilityEvent, setAgilityEvent] = useState(null);
  const [agilityHistory, setAgilityHistory] = useState([]);

  const sendTestHandshake = async (anomalyType) => {
    try {
      await axios.post('/api/test/handshake', { anomaly_type: anomalyType });
    } catch (error) {
      console.error('Test handshake request failed:', error);
    }
  };

  const sendTestAgility = async () => {
    try {
      await axios.post('/api/test/agility', {
        event_type: 'manual_override',
        old_suite: metrics?.suite || 'TLS_X25519_ML_KEM_768_WITH_AES_256_GCM_SHA3_256',
        new_suite: 'TLS_X25519_ML_KEM_768_WITH_AES_256_GCM_SHA3_256',
        anomaly_score: metrics?.anomaly_score || 0.05,
      });
    } catch (error) {
      console.error('Test agility request failed:', error);
    }
  };

  useEffect(() => {
    socket.on('connect', () => {
      setIsConnected(true);
      console.log('Connected to WebSocket server');
    });

    socket.on('disconnect', () => {
      setIsConnected(false);
      console.log('Disconnected from WebSocket server');
    });

    socket.on('metrics_update', (data) => {
      setMetrics(data);
    });

    socket.on('agility_event', (data) => {
      setAgilityEvent(data);
      setAgilityHistory(prev => [data, ...prev].slice(0, 10)); // Keep last 10 events
    });

    return () => {
      socket.off('connect');
      socket.off('disconnect');
      socket.off('metrics_update');
      socket.off('agility_event');
    };
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <h1>Triple-Shield Architecture Dashboard</h1>
        <div className="connection-status">
          <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}></span>
          {isConnected ? 'Connected' : 'Disconnected'}
        </div>
      </header>
      <main>
        <section className="control-panel">
          <h2>Manual Test Controls</h2>
          <div className="control-row">
            <button className="control-button" onClick={() => sendTestHandshake('normal')}>
              Normal Handshake
            </button>
            <button className="control-button" onClick={() => sendTestHandshake('high_latency')}>
              High Latency Anomaly
            </button>
            <button className="control-button" onClick={() => sendTestHandshake('size_mismatch')}>
              Size Mismatch Anomaly
            </button>
            <button className="control-button" onClick={() => sendTestHandshake('failure')}>
              Failure Anomaly
            </button>
            <button className="control-button" onClick={() => sendTestHandshake('repeated_failure')}>
              Repeated Failure
            </button>
          </div>
          <div className="control-row">
            <button className="control-button" onClick={sendTestAgility}>
              Emit Manual Agility Event
            </button>
          </div>
        </section>
        <Dashboard 
          metrics={metrics} 
          isConnected={isConnected} 
          agilityEvent={agilityEvent}
          agilityHistory={agilityHistory}
        />
      </main>
    </div>
  );
}

export default App;
