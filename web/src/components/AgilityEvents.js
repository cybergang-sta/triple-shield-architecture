import React from 'react';
import './AgilityEvents.css';

function AgilityEvents({ currentEvent, history }) {
  if (!currentEvent && (!history || history.length === 0)) {
    return null;
  }

  const timelineEvents = [currentEvent, ...(history || [])].filter(Boolean);

  const formatTime = (timestamp) => {
    if (!timestamp) {
      return '—';
    }
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  const formatTrigger = (event) => {
    return event?.trigger_event || event?.event_type || event?.trigger || 'manual';
  };

  const formatAnomaly = (event) => {
    if (event?.anomaly_score == null) {
      return 'n/a';
    }
    return event.anomaly_score.toFixed(3);
  };

  const formatBadge = (event) => {
    const trigger = formatTrigger(event);
    if (trigger === 'high_anomaly' || trigger === 'high_latency') {
      return { label: 'Alert', className: 'badge-alert' };
    }
    if (trigger === 'repeated_failure' || trigger === 'failure') {
      return { label: 'Failure', className: 'badge-failure' };
    }
    if (trigger === 'manual_override') {
      return { label: 'Manual', className: 'badge-manual' };
    }
    return { label: 'Transition', className: 'badge-transition' };
  };

  return (
    <div className="agility-events">
      <div className="events-header">
        <div>
          <h3 className="events-title">Cryptographic Agility Timeline</h3>
          <p className="events-subtitle">Recent triggers, scores, and suite transitions</p>
        </div>
        <span className="events-count">{timelineEvents.length} events</span>
      </div>

      <div className="timeline">
        {timelineEvents.map((event, index) => {
          const badge = formatBadge(event);
          const trigger = formatTrigger(event);
          const oldSuite = event?.old_suite || event?.from_suite || '—';
          const newSuite = event?.new_suite || event?.to_suite || '—';
          const anomalyType = event?.anomaly_type || '—';

          return (
            <div key={`${trigger}-${index}`} className={`timeline-item ${index === 0 ? 'timeline-item-active' : ''}`}>
              <div className="timeline-marker">
                <span className={`timeline-dot ${badge.className}`}></span>
              </div>
              <div className="timeline-card">
                <div className="timeline-card-header">
                  <span className={`timeline-badge ${badge.className}`}>{badge.label}</span>
                  <span className="timeline-time">{formatTime(event?.timestamp)}</span>
                </div>
                <div className="timeline-title">{trigger}</div>
                <div className="timeline-grid">
                  <div className="timeline-cell">
                    <span className="timeline-key">From</span>
                    <span className="timeline-value suite-from">{oldSuite}</span>
                  </div>
                  <div className="timeline-cell">
                    <span className="timeline-key">To</span>
                    <span className="timeline-value suite-to">{newSuite}</span>
                  </div>
                  <div className="timeline-cell">
                    <span className="timeline-key">Score</span>
                    <span className="timeline-value">{formatAnomaly(event)}</span>
                  </div>
                  <div className="timeline-cell">
                    <span className="timeline-key">Anomaly</span>
                    <span className="timeline-value">{anomalyType}</span>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default AgilityEvents;
