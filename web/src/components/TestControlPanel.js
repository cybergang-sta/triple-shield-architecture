import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './TestControlPanel.css';

function TestControlPanel() {
  const [scenarios, setScenarios] = useState(null);
  const [customMetrics, setCustomMetrics] = useState({
    total_latency_ms: 2.5,
    ciphertext_size_bytes: 1088,
    public_key_size_bytes: 1184,
    success: true,
    encap_variance: 0.0,
    anomaly_score: 0.15,
    suite: 'TLS_X25519_ML_KEM_768_WITH_AES_256_GCM_SHA3_256',
    anomaly_type: 'normal'
  });
  const [customAgility, setCustomAgility] = useState({
    trigger_event: 'HIGH_ANOMALY_SCORE',
    old_suite: 'TLS_X25519_ML_KEM_768_WITH_AES_256_GCM_SHA3_256',
    new_suite: 'TLS_X25519_ML_KEM_1024_WITH_AES_256_GCM_SHA3_256',
    anomaly_score: 0.88
  });
  const [status, setStatus] = useState('');

  useEffect(() => {
    fetchScenarios();
  }, []);

  const fetchScenarios = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/test/scenarios');
      setScenarios(response.data.scenarios);
    } catch (error) {
      console.error('Error fetching scenarios:', error);
    }
  };

  const injectScenario = async (scenarioKey) => {
    try {
      const scenario = scenarios[scenarioKey];
      setStatus(`Injecting ${scenarioKey} scenario...`);
      
      if (scenario.metrics) {
        await axios.post('http://localhost:5000/api/test/metrics', scenario.metrics);
      }
      if (scenario.agility) {
        await axios.post('http://localhost:5000/api/test/agility', scenario.agility);
      }
      
      setStatus(`${scenarioKey} scenario injected successfully`);
      setTimeout(() => setStatus(''), 3000);
    } catch (error) {
      console.error('Error injecting scenario:', error);
      setStatus(`Error: ${error.message}`);
    }
  };

  const injectCustomMetrics = async () => {
    try {
      setStatus('Injecting custom metrics...');
      await axios.post('http://localhost:5000/api/test/metrics', customMetrics);
      setStatus('Custom metrics injected successfully');
      setTimeout(() => setStatus(''), 3000);
    } catch (error) {
      console.error('Error injecting custom metrics:', error);
      setStatus(`Error: ${error.message}`);
    }
  };

  const injectCustomAgility = async () => {
    try {
      setStatus('Injecting custom agility event...');
      await axios.post('http://localhost:5000/api/test/agility', customAgility);
      setStatus('Custom agility event injected successfully');
      setTimeout(() => setStatus(''), 3000);
    } catch (error) {
      console.error('Error injecting custom agility event:', error);
      setStatus(`Error: ${error.message}`);
    }
  };

  return (
    <div className="test-control-panel">
      <div className="panel-header">
        <h3 className="panel-title">🧪 Test Control Panel</h3>
        <span className="panel-badge">Synthetic Data Only</span>
      </div>

      {status && (
        <div className={`status-message ${status.includes('Error') ? 'error' : 'success'}`}>
          {status}
        </div>
      )}

      <div className="panel-section">
        <h4 className="section-title">Preset Scenarios</h4>
        <div className="scenario-buttons">
          {scenarios ? (
            Object.entries(scenarios).map(([key, scenario]) => (
              <button
                key={key}
                className="scenario-btn"
                onClick={() => injectScenario(key)}
                title={scenario.description}
              >
                {key.replace('_', ' ').toUpperCase()}
              </button>
            ))
          ) : (
            <p>Loading scenarios...</p>
          )}
        </div>
      </div>

      <div className="panel-section">
        <h4 className="section-title">Custom Metrics</h4>
        <div className="form-grid">
          <div className="form-group">
            <label>Latency (ms)</label>
            <input
              type="number"
              step="0.1"
              value={customMetrics.total_latency_ms}
              onChange={(e) => setCustomMetrics({...customMetrics, total_latency_ms: parseFloat(e.target.value)})}
            />
          </div>
          <div className="form-group">
            <label>Public Key Size (bytes)</label>
            <input
              type="number"
              value={customMetrics.public_key_size_bytes}
              onChange={(e) => setCustomMetrics({...customMetrics, public_key_size_bytes: parseInt(e.target.value)})}
            />
          </div>
          <div className="form-group">
            <label>Ciphertext Size (bytes)</label>
            <input
              type="number"
              value={customMetrics.ciphertext_size_bytes}
              onChange={(e) => setCustomMetrics({...customMetrics, ciphertext_size_bytes: parseInt(e.target.value)})}
            />
          </div>
          <div className="form-group">
            <label>Anomaly Score</label>
            <input
              type="number"
              step="0.01"
              min="0"
              max="1"
              value={customMetrics.anomaly_score}
              onChange={(e) => setCustomMetrics({...customMetrics, anomaly_score: parseFloat(e.target.value)})}
            />
          </div>
          <div className="form-group">
            <label>Anomaly Type</label>
            <select
              value={customMetrics.anomaly_type}
              onChange={(e) => setCustomMetrics({...customMetrics, anomaly_type: e.target.value})}
            >
              <option value="normal">Normal</option>
              <option value="timing_anomaly">Timing Anomaly</option>
              <option value="size_tampering">Size Tampering</option>
            </select>
          </div>
        </div>
        <button className="inject-btn" onClick={injectCustomMetrics}>
          Inject Custom Metrics
        </button>
      </div>

      <div className="panel-section">
        <h4 className="section-title">Custom Agility Event</h4>
        <div className="form-grid">
          <div className="form-group">
            <label>Trigger Event</label>
            <select
              value={customAgility.trigger_event}
              onChange={(e) => setCustomAgility({...customAgility, trigger_event: e.target.value})}
            >
              <option value="HIGH_ANOMALY_SCORE">High Anomaly Score</option>
              <option value="REPEATED_FAILURE">Repeated Failure</option>
              <option value="MANUAL_OVERRIDE">Manual Override</option>
            </select>
          </div>
          <div className="form-group">
            <label>Old Suite</label>
            <input
              type="text"
              value={customAgility.old_suite}
              onChange={(e) => setCustomAgility({...customAgility, old_suite: e.target.value})}
            />
          </div>
          <div className="form-group">
            <label>New Suite</label>
            <input
              type="text"
              value={customAgility.new_suite}
              onChange={(e) => setCustomAgility({...customAgility, new_suite: e.target.value})}
            />
          </div>
          <div className="form-group">
            <label>Anomaly Score</label>
            <input
              type="number"
              step="0.01"
              min="0"
              max="1"
              value={customAgility.anomaly_score}
              onChange={(e) => setCustomAgility({...customAgility, anomaly_score: parseFloat(e.target.value)})}
            />
          </div>
        </div>
        <button className="inject-btn" onClick={injectCustomAgility}>
          Inject Agility Event
        </button>
      </div>

      <div className="panel-notice">
        <p>⚠️ All test data is synthetic and does not affect real cryptographic operations.</p>
        <p>Test data is clearly marked with <code>is_test_data: true</code> flag.</p>
      </div>
    </div>
  );
}

export default TestControlPanel;
