import React, { useState, useEffect } from 'react';
import io from 'socket.io-client';
import Dashboard from './pages/Dashboard';
import './App.css';

const socket = io('http://localhost:5000');

function App() {
  const [isConnected, setIsConnected] = useState(false);
  const [metrics, setMetrics] = useState(null);

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

    return () => {
      socket.off('connect');
      socket.off('disconnect');
      socket.off('metrics_update');
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
        <Dashboard metrics={metrics} isConnected={isConnected} />
      </main>
    </div>
  );
}

export default App;
