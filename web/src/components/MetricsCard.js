import React from 'react';
import './MetricsCard.css';

function MetricsCard({ title, value, subtitle, isAnomaly }) {
  return (
    <div className={`metrics-card ${isAnomaly ? 'anomaly' : ''}`}>
      <h3 className="card-title">{title}</h3>
      <div className="card-value">{value}</div>
      <p className="card-subtitle">{subtitle}</p>
    </div>
  );
}

export default MetricsCard;
