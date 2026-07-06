import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import './OverheadChart.css';

function OverheadChart({ metrics }) {
  const data = [
    {
      name: 'Classical',
      overhead: 32,
      baseline: 32
    },
    {
      name: 'ML-KEM-768',
      overhead: metrics.public_key_size_bytes || 1184,
      baseline: 1184
    },
    {
      name: 'ML-KEM-1024',
      overhead: 1568,
      baseline: 1568
    }
  ];

  const CustomLegend = () => (
    <div className="custom-legend">
      <div className="legend-item">
        <div className="legend-color" style={{ backgroundColor: '#8884d8' }}></div>
        <span className="legend-label">Current (bytes)</span>
        <span className="legend-desc">Actual key size from current handshake</span>
      </div>
      <div className="legend-item">
        <div className="legend-color" style={{ backgroundColor: '#82ca9d' }}></div>
        <span className="legend-label">Baseline (bytes)</span>
        <span className="legend-desc">Expected size from literature/specification</span>
      </div>
    </div>
  );

  return (
    <div className="chart-container">
      <h3 className="chart-title">Key Size Overhead Comparison</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis dataKey="name" stroke="#6b7280" />
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
          <Bar dataKey="overhead" fill="#8884d8" name="overhead" radius={[4, 4, 0, 0]} />
          <Bar dataKey="baseline" fill="#82ca9d" name="baseline" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default OverheadChart;
