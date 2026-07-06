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

  const CustomLegend = () => (
    <div className="custom-legend">
      <div className="legend-item">
        <div className="legend-color" style={{ backgroundColor: '#8884d8' }}></div>
        <span className="legend-label">Handshakes/second</span>
        <span className="legend-desc">Throughput rate based on handshake latency</span>
      </div>
    </div>
  );

  return (
    <div className="chart-container">
      <h3 className="chart-title">Handshake Throughput</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="time" stroke="#6b7280" />
          <YAxis stroke="#6b7280" />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: '#1f2937', 
              border: 'none', 
              borderRadius: '8px',
              color: '#fff'
            }}
          />
          <Legend content={<CustomLegend />} />
          <Line 
            type="monotone" 
            dataKey="throughput" 
            stroke="#8884d8" 
            strokeWidth={2}
            dot={{ fill: '#8884d8', strokeWidth: 2, r: 4 }}
            activeDot={{ r: 6 }}
            name="throughput"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default ThroughputChart;
