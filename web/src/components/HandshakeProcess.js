import React from 'react';
import './HandshakeProcess.css';

function HandshakeProcess({ metrics }) {
  const steps = [
    { name: 'Key Generation', status: 'complete', time: metrics.alice_kem_keygen_ns ? (metrics.alice_kem_keygen_ns / 1000000).toFixed(2) : '0.00' },
    { name: 'Encapsulation', status: 'complete', time: metrics.bob_encap_ns ? (metrics.bob_encap_ns / 1000000).toFixed(2) : '0.00' },
    { name: 'Decapsulation', status: 'complete', time: metrics.alice_decap_ns ? (metrics.alice_decap_ns / 1000000).toFixed(2) : '0.00' },
    { name: 'Key Derivation', status: 'complete', time: '0.50' },
  ];

  return (
    <div className="handshake-process">
      <h3 className="process-title">Handshake Process Flow</h3>
      <div className="process-steps">
        {steps.map((step, index) => (
          <div key={index} className="process-step">
            <div className="step-indicator">
              <div className="step-number">{index + 1}</div>
            </div>
            <div className="step-content">
              <h4 className="step-name">{step.name}</h4>
              <p className="step-time">{step.time} ms</p>
            </div>
            {index < steps.length - 1 && <div className="step-connector"></div>}
          </div>
        ))}
      </div>
    </div>
  );
}

export default HandshakeProcess;
