import React from 'react';
import './AnomalyAlert.css';

function AnomalyAlert({ score, type }) {
  const isAnomalous = Number(score || 0) > 0.6;
  const normalizedType = (type || '').toLowerCase();
  const displayType = normalizedType === 'resource_exhaustion'
    ? 'Resource Exhaustion'
    : (type || (isAnomalous ? 'Unknown' : 'Normal'));

  return (
    <div className={`anomaly-alert ${isAnomalous ? 'anomaly-alert-active' : 'anomaly-alert-clear'}`}>
      <div className="alert-icon">{isAnomalous ? '⚠️' : '✅'}</div>
      <div className="alert-content">
        <h3 className="alert-title">{isAnomalous ? 'Anomaly Detected' : 'Anomaly Status'}</h3>
        <p className="alert-score">Anomaly Score: {(Number(score || 0)).toFixed(3)}</p>
        <p className="alert-type">Type: {displayType}</p>
      </div>
    </div>
  );
}

export default AnomalyAlert;
