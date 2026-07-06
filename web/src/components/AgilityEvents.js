import React from 'react';
import './AgilityEvents.css';

function AgilityEvents({ currentEvent, history }) {
  if (!currentEvent && (!history || history.length === 0)) {
    return null;
  }

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  return (
    <div className="agility-events">
      <h3 className="events-title">Cryptographic Agility Events</h3>
      
      {currentEvent && (
        <div className="current-event">
          <div className="event-header">
            <span className="event-icon">⚡</span>
            <span className="event-label">Latest Transition</span>
          </div>
          <div className="event-details">
            <div className="event-row">
              <span className="event-key">Trigger:</span>
              <span className="event-value">{currentEvent.trigger_event}</span>
            </div>
            <div className="event-row">
              <span className="event-key">From:</span>
              <span className="event-value old-suite">{currentEvent.old_suite}</span>
            </div>
            <div className="event-row">
              <span className="event-key">To:</span>
              <span className="event-value new-suite">{currentEvent.new_suite}</span>
            </div>
            <div className="event-row">
              <span className="event-key">Anomaly Score:</span>
              <span className="event-value">{currentEvent.anomaly_score?.toFixed(3)}</span>
            </div>
          </div>
        </div>
      )}

      {history && history.length > 1 && (
        <div className="event-history">
          <h4 className="history-title">Recent Transitions</h4>
          <div className="history-list">
            {history.slice(1).map((event, index) => (
              <div key={index} className="history-item">
                <span className="history-time">{formatTime(event.timestamp)}</span>
                <span className="history-trigger">{event.trigger_event}</span>
                <span className="history-arrow">→</span>
                <span className="history-suite">{event.new_suite}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default AgilityEvents;
