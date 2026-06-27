"""Agility Controller: manages cryptographic suite transitions and re-negotiation.

This module implements the policy-driven agility layer that:
1. Evaluates anomaly scores against thresholds
2. Manages session state (preserve across re-negotiation)
3. Orchestrates suite transitions per policy rules
4. Logs agility events for audit and debugging
"""

import json
import logging
import os
from typing import Optional, Dict, List, Tuple
from enum import Enum

_LOGGER = logging.getLogger("agility_controller")


class AgilityEvent(Enum):
    """Types of cryptographic agility events."""

    NONE = "none"
    HIGH_ANOMALY = "high_anomaly"
    REPEATED_FAILURE = "repeated_failure"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    MANUAL_OVERRIDE = "manual_override"


class SessionState:
    """Tracks session state for preservation across re-negotiation."""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.current_suite = None
        self.previous_suite = None
        self.handshake_count = 0
        self.failed_handshakes = 0
        self.max_anomaly_score = 0.0
        self.agility_events = []

    def record_handshake(self, success: bool, anomaly_score: float):
        """Record a handshake attempt."""
        self.handshake_count += 1
        if not success:
            self.failed_handshakes += 1
        self.max_anomaly_score = max(self.max_anomaly_score, anomaly_score)

    def record_agility_event(self, event: AgilityEvent, old_suite: str, new_suite: str):
        """Record an agility transition."""
        self.agility_events.append(
            {
                "event": event.value,
                "from_suite": old_suite,
                "to_suite": new_suite,
                "handshake_count": self.handshake_count,
                "failed_count": self.failed_handshakes,
            }
        )
        self.previous_suite = old_suite
        self.current_suite = new_suite

    def to_dict(self) -> Dict:
        """Serialize session state."""
        return {
            "session_id": self.session_id,
            "current_suite": self.current_suite,
            "previous_suite": self.previous_suite,
            "handshake_count": self.handshake_count,
            "failed_handshakes": self.failed_handshakes,
            "max_anomaly_score": self.max_anomaly_score,
            "agility_events": self.agility_events,
        }


class AgilityController:
    """Policy-driven agility controller for cryptographic suite transitions."""

    def __init__(self, policy_path: Optional[str] = None):
        if policy_path is None:
            policy_path = os.path.join(os.path.dirname(__file__), "policy.json")
        self.policy_path = policy_path
        self.policy = self._load_policy()
        self.sessions: Dict[str, SessionState] = {}
        _LOGGER.info("AgilityController initialized with policy: %s", policy_path)

    def _load_policy(self) -> Dict:
        """Load the policy configuration."""
        try:
            with open(self.policy_path, "r", encoding="utf-8") as f:
                policy = json.load(f)
                _LOGGER.info("Policy loaded: %d cipher suites defined", len(policy.get("cipher_suites", {})))
                return policy
        except Exception as e:
            _LOGGER.error("Failed to load policy: %s", e)
            return {}

    def get_default_suite(self) -> str:
        """Get the default cipher suite."""
        return self.policy.get("default_suite", "TLS_X25519_ML_KEM_768_WITH_AES_256_GCM_SHA3_256")

    def get_suite_definition(self, suite_name: str) -> Optional[Dict]:
        """Get the definition of a cipher suite."""
        suites = self.policy.get("cipher_suites", {})
        return suites.get(suite_name)

    def get_fallback_order(self) -> List[str]:
        """Get the fallback order for suite transitions."""
        return self.policy.get("fallback_order", [self.get_default_suite()])

    def create_session(self, session_id: str, initial_suite: Optional[str] = None) -> SessionState:
        """Create a new session with optional initial suite."""
        session = SessionState(session_id)
        session.current_suite = initial_suite or self.get_default_suite()
        self.sessions[session_id] = session
        _LOGGER.info("Session created: %s with suite %s", session_id, session.current_suite)
        return session

    def evaluate_agility(self, session_id: str, anomaly_score: float, success: bool) -> Tuple[AgilityEvent, Optional[str]]:
        """Evaluate whether agility should be triggered.

        Returns:
            (event_type, suggested_suite): The event type and new suite (if applicable).
        """
        session = self.sessions.get(session_id)
        if not session:
            _LOGGER.warning("Session not found: %s", session_id)
            return AgilityEvent.NONE, None

        # Record the handshake
        session.record_handshake(success, anomaly_score)

        # Evaluate rules
        suite_def = self.get_suite_definition(session.current_suite)
        threshold = suite_def.get("anomaly_threshold", 0.6) if suite_def else 0.6

        # Rule 1: High anomaly score
        if anomaly_score > threshold:
            _LOGGER.warning("High anomaly score (%.3f > %.3f) in session %s", anomaly_score, threshold, session_id)
            new_suite = self._get_next_suite(session.current_suite)
            return AgilityEvent.HIGH_ANOMALY, new_suite

        # Rule 2: Repeated failures
        if session.failed_handshakes >= 3:
            _LOGGER.warning("Repeated failures (%d) in session %s", session.failed_handshakes, session_id)
            fallback = self.get_fallback_order()
            new_suite = fallback[0] if fallback else None
            return AgilityEvent.REPEATED_FAILURE, new_suite

        return AgilityEvent.NONE, None

    def _get_next_suite(self, current_suite: str) -> Optional[str]:
        """Get the next suite in fallback order after current_suite."""
        fallback = self.get_fallback_order()
        try:
            idx = fallback.index(current_suite)
            if idx + 1 < len(fallback):
                return fallback[idx + 1]
        except ValueError:
            pass
        return fallback[0] if fallback else None

    def transition_suite(self, session_id: str, old_suite: str, new_suite: str, event: AgilityEvent):
        """Transition a session to a new suite."""
        session = self.sessions.get(session_id)
        if session:
            session.record_agility_event(event, old_suite, new_suite)
            _LOGGER.info("Suite transitioned: %s -> %s (event=%s) in session %s", old_suite, new_suite, event.value, session_id)

    def get_session_state(self, session_id: str) -> Optional[Dict]:
        """Get the state of a session."""
        session = self.sessions.get(session_id)
        return session.to_dict() if session else None


# Global singleton instance
_controller = AgilityController()


def get_controller() -> AgilityController:
    """Get the global agility controller instance."""
    return _controller


def initialize_controller(policy_path: Optional[str] = None):
    """Initialize the agility controller with an optional custom policy."""
    global _controller
    _controller = AgilityController(policy_path)
    _LOGGER.info("Agility controller initialized")
