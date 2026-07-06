import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './ThroughputChart.css';

function ThroughputChart({ metrics }) {
  // Generate sample throughput data based on current metrics
  const data = [
    { time: '0s', throughput: 0 },
    { time: '1s', throughput: metrics.total_latency_ms ? (1000 / metrics.total_latency_ms) : 0 },
    { time: '2s', throughput: metrics.total_latency_ms ? (1000 / metrics.total_latency_ms) * 0.9 : 0 },
    { time: '3s', throughput: metrics.total_latency_ms ? (1000 / metrics.total_latency_ms) * 1.1 : 0 },
    { time: '4s', throughput: metrics.total_latency_ms ? (1000 / metrics.total_latency_ms) * 0.95 : 0 },
    { time: '5s', throughput: metrics.total_latency_ms ? (1000 / metrics.total_latency_ms) : 0 },
  ];

  return (
    <div className="chart-container">
      <h3 className="chart-title">Handshake Throughput</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="throughput" 
            stroke="#8884d8" 
            strokeWidth={2}
            name="Handshakes/second"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default ThroughputChart;
