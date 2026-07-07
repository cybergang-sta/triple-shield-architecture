import React, { useEffect, useMemo, useState } from 'react';
import './HandshakeProcess.css';

function HandshakeProcess({ metrics }) {
  const [activeStep, setActiveStep] = useState(0);

  const steps = useMemo(() => [
    {
      name: 'Key Generation',
      actor: 'Alice',
      time: metrics.alice_kem_keygen_ns ? (metrics.alice_kem_keygen_ns / 1000000).toFixed(2) : '0.00',
      detail: 'Alice generates X25519 + ML-KEM keys',
      status: 'complete',
    },
    {
      name: 'Encapsulation',
      actor: 'Bob',
      time: metrics.bob_encap_ns ? (metrics.bob_encap_ns / 1000000).toFixed(2) : '0.00',
      detail: 'Bob encapsulates against Alice’s public key',
      status: 'complete',
    },
    {
      name: 'Decapsulation',
      actor: 'Alice',
      time: metrics.alice_decap_ns ? (metrics.alice_decap_ns / 1000000).toFixed(2) : '0.00',
      detail: 'Alice decapsulates Bob’s ciphertext',
      status: 'complete',
    },
    {
      name: 'Key Derivation',
      actor: 'Both',
      time: metrics.hkdf_ns ? (metrics.hkdf_ns / 1000000).toFixed(2) : '0.50',
      detail: 'Both derive the shared session key',
      status: 'complete',
    },
  ], [metrics]);

  useEffect(() => {
    const interval = window.setInterval(() => {
      setActiveStep((current) => (current + 1) % steps.length);
    }, 900);

    return () => window.clearInterval(interval);
  }, [steps.length]);

  return (
    <div className="handshake-process">
      <div className="process-header">
        <div>
          <h3 className="process-title">Handshake Process Flow</h3>
          <p className="process-subtitle">Live Alice/Bob exchange with per-stage latency</p>
        </div>
        <div className="process-badge">Realtime</div>
      </div>

      <div className="process-steps">
        {steps.map((step, index) => {
          const isActive = index === activeStep;
          const isComplete = index < activeStep || metrics?.success;

          return (
            <div key={index} className={`process-step ${isActive ? 'active' : ''} ${isComplete ? 'complete' : ''}`}>
              <div className="step-indicator">
                <div className="step-number">{index + 1}</div>
              </div>
              <div className="step-content">
                <div className="step-actor">{step.actor}</div>
                <h4 className="step-name">{step.name}</h4>
                <p className="step-detail">{step.detail}</p>
                <p className="step-time">{step.time} ms</p>
              </div>
              {index < steps.length - 1 && <div className="step-connector"></div>}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default HandshakeProcess;
