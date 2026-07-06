import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
import Dashboard from './pages/Dashboard';
import './App.css';

const socket = io('http://localhost:5000');

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [metrics, setMetrics] = useState(null);
  const [agilityEvent, setAgilityEvent] = useState(null);
  const [agilityHistory, setAgilityHistory] = useState([]);

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
