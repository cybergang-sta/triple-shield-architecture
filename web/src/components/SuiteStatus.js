import React from 'react';
import './SuiteStatus.css';

function SuiteStatus({ suite }) {
  if (!suite) {
    return null;
  }

  // Parse suite name for display
  const suiteName = suite.replace(/_/g, ' ').replace(/TLS/g, '').trim();
  
  return (
    <div className="suite-status">
      <div className="suite-icon">🔐</div>
      <div className="suite-info">
        <h3 className="suite-title">Current Cipher Suite</h3>
        <p className="suite-name">{suiteName}</p>
        <p className="suite-full">{suite}</p>
      </div>
    </div>
  );
}

export default SuiteStatus;
