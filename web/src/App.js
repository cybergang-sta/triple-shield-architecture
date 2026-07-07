import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
import axios from 'axios';
import Dashboard from './pages/Dashboard';
import './App.css';

const socket = io('http://localhost:5000');

const fallbackSuites = [
  'TLS_X25519_ML_KEM_768_WITH_AES_256_GCM_SHA3_256',
  'TLS_X25519_ML_KEM_1024_WITH_AES_256_GCM_SHA3_256',
  'TLS_X25519_WITH_AES_256_GCM_SHA3_256',
];

function getNextSuite(currentSuite) {
  if (!currentSuite) {
    return fallbackSuites[0];
  }

  const index = fallbackSuites.indexOf(currentSuite);
  if (index === -1) {
    return fallbackSuites[0];
  }

  return fallbackSuites[Math.min(index + 1, fallbackSuites.length - 1)];
}

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
      const currentSuite = metrics?.suite || fallbackSuites[0];
      const nextSuite = getNextSuite(currentSuite);

      await axios.post('/api/test/agility', {
        event_type: 'manual_override',
        old_suite: currentSuite,
        new_suite: nextSuite,
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

      const nextSuite = data?.new_suite || data?.to_suite;
      if (nextSuite) {
        setMetrics(prev => prev ? { ...prev, suite: nextSuite } : prev);
      }
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
        <div className="header-spacer" />
        <h1>Triple-Shield Architecture Dashboard</h1>
        <div className="connection-status">
          <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}></span>
          {isConnected ? 'Connected' : 'Disconnected'}
        </div>
      </header>
      <main>
        <section className="control-panel" aria-label="Manual test controls">
          <h2>Manual Trigger Panel</h2>
          <p className="control-subtitle">For manual demo actions only</p>
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
