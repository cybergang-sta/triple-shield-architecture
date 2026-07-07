import React from 'react';
import MetricsCard from '../components/MetricsCard';
import ThroughputChart from '../components/ThroughputChart';
import OverheadChart from '../components/OverheadChart';
import HandshakeProcess from '../components/HandshakeProcess';
import AnomalyAlert from '../components/AnomalyAlert';
import SuiteStatus from '../components/SuiteStatus';
import AgilityEvents from '../components/AgilityEvents';

function Dashboard({ metrics, isConnected, agilityEvent, agilityHistory }) {
  if (!metrics) {
    return (
      <div className="dashboard-container">
        <div className="no-data">
          <h2>Waiting for metrics data...</h2>
          <p>Start the 3SA process to begin streaming live metrics.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-container">
      <div className="metrics-grid">
        <MetricsCard 
          title="Total Latency" 
          value={`${metrics.total_latency_ms?.toFixed(3) || 0} ms`}
          subtitle="Handshake completion time"
        />
        <MetricsCard 
          title="Public Key Size" 
          value={`${metrics.public_key_size_bytes || 0} bytes`}
          subtitle="Post-quantum key exchange"
        />
        <MetricsCard 
          title="Ciphertext Size" 
          value={`${metrics.ciphertext_size_bytes || 0} bytes`}
          subtitle="Encapsulated key material"
        />
        <MetricsCard 
          title="Anomaly Score" 
          value={metrics.anomaly_score?.toFixed(3) || 0}
          subtitle="AI detection confidence"
          isAnomaly={metrics.anomaly_score > 0.6}
        />
      </div>

      <div className="status-grid">
        <SuiteStatus suite={metrics.suite} />
        <AnomalyAlert score={metrics.anomaly_score} type={metrics.anomaly_type} />
      </div>

      <HandshakeProcess metrics={metrics} />

      {agilityEvent && (
        <AgilityEvents currentEvent={agilityEvent} history={agilityHistory} />
      )}

      <div className="charts-section">
        <ThroughputChart metrics={metrics} />
        <OverheadChart metrics={metrics} />
      </div>
    </div>
  );
}

export default Dashboard;
