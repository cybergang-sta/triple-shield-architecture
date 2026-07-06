import React from 'react';
import './AnomalyAlert.css';

function AnomalyAlert({ score, type }) {
  return (
    <div className="anomaly-alert">
      <div className="alert-icon">⚠️</div>
      <div className="alert-content">
        <h3 className="alert-title">Anomaly Detected</h3>
        <p className="alert-score">Anomaly Score: {score.toFixed(3)}</p>
        <p className="alert-type">Type: {type || 'Unknown'}</p>
      </div>
    </div>
  );
}

export default AnomalyAlert;
