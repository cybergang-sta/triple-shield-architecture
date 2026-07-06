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

  return (
    <div className="chart-container">
      <h3 className="chart-title">Key Size Overhead Comparison</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="overhead" fill="#8884d8" name="Current (bytes)" />
          <Bar dataKey="baseline" fill="#82ca9d" name="Baseline (bytes)" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default OverheadChart;
