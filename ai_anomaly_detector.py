"""AI-driven anomaly detection for hybrid PQC handshakes.

This module provides feature extraction, classifier training, and real-time
anomaly scoring for detecting implementation flaws, resource exhaustion, or
side-channel patterns in hybrid key exchange handshakes.

Features extracted from handshake metadata:
- Handshake latency (milliseconds)
- Ciphertext size (bytes)
- Public key size (bytes)
- Success/failure indicator
- Encapsulation time variance (simulated)
"""

import logging
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from typing import Tuple, List, Dict, Optional

_LOGGER = logging.getLogger("ai_anomaly_detector")


class HandshakeMetrics:
    """Container for handshake metadata used for anomaly detection."""

    def __init__(
        self,
        latency_ms: float,
        ciphertext_size: int,
        public_key_size: int,
        success: bool,
        encap_variance: float = 0.0,
        suite: Optional[str] = None,
    ):
        self.latency_ms = latency_ms
        self.ciphertext_size = ciphertext_size
        self.public_key_size = public_key_size
        self.success = success
        self.encap_variance = encap_variance
        self.suite = suite

    def to_feature_vector(self) -> np.ndarray:
        """Convert metrics to a feature vector for classification."""
        return np.array(
            [
                self.latency_ms,
                self.ciphertext_size,
                self.public_key_size,
                float(self.success),
                self.encap_variance,
            ],
            dtype=np.float32,
        )


class AnomalyDetector:
    """AI-based anomaly detector using scikit-learn RandomForest."""

    def __init__(self):
        self.classifier = None
        self.scaler = None
        self.is_trained = False
        self.suite_overhead_ranges = {}

    def load_suite_overhead_ranges(self, policy_path: Optional[str] = None):
        """Load expected overhead ranges from policy configuration."""
        import json
        import os

        if policy_path is None:
            policy_path = os.path.join(os.path.dirname(__file__), "policy.json")

        try:
            with open(policy_path, "r", encoding="utf-8") as f:
                policy = json.load(f)
                suites = policy.get("cipher_suites", {})
                for suite_name, suite_def in suites.items():
                    self.suite_overhead_ranges[suite_name] = suite_def.get("expected_overhead", {})
                _LOGGER.info("Loaded overhead ranges for %d cipher suites", len(self.suite_overhead_ranges))
        except Exception as e:
            _LOGGER.warning("Failed to load overhead ranges from policy: %s", e)

    def generate_synthetic_training_data(self, n_samples: int = 500) -> Tuple[pd.DataFrame, np.ndarray]:
        """Generate synthetic training data with normal and anomalous handshakes.

        Returns:
            (feature_df, labels): feature DataFrame and binary labels (0=normal, 1=anomalous).
        """
        _LOGGER.info("Generating synthetic training data: %d samples", n_samples)
        features = []
        labels = []

        # Normal handshakes (70% of data)
        for _ in range(int(n_samples * 0.7)):
            latency = np.random.normal(5.0, 0.5)  # mean 5ms, std 0.5
            ct_size = np.random.normal(1088, 50)  # ML-KEM-768 ciphertext ~1088 bytes
            pk_size = np.random.normal(1184, 50)  # ML-KEM-768 public key ~1184 bytes
            success = True
            variance = np.random.normal(0.1, 0.05)
            features.append([latency, ct_size, pk_size, float(success), variance])
            labels.append(0)

        # Anomalous handshakes (30% of data)
        # Simulated anomalies: high latency, failed operations, high variance
        for _ in range(int(n_samples * 0.3)):
            anomaly_type = np.random.choice(["high_latency", "failure", "variance"])
            if anomaly_type == "high_latency":
                latency = np.random.normal(15.0, 2.0)  # 3x normal latency
            else:
                latency = np.random.normal(5.0, 0.5)
            ct_size = np.random.normal(1088, 100)
            pk_size = np.random.normal(1184, 100)
            success = anomaly_type != "failure"
            variance = np.random.normal(0.5, 0.15) if anomaly_type == "variance" else np.random.normal(0.1, 0.05)
            features.append([latency, ct_size, pk_size, float(success), variance])
            labels.append(1)

        df = pd.DataFrame(
            features,
            columns=["latency_ms", "ciphertext_size", "public_key_size", "success", "encap_variance"],
        )
        _LOGGER.info("Generated %d normal and %d anomalous samples", int(n_samples * 0.7), int(n_samples * 0.3))
        return df, np.array(labels)

    def train(self, feature_df: Optional[pd.DataFrame] = None, labels: Optional[np.ndarray] = None):
        """Train the classifier on provided data or generate synthetic data if not provided."""
        if feature_df is None or labels is None:
            feature_df, labels = self.generate_synthetic_training_data()

        X_train, X_test, y_train, y_test = train_test_split(feature_df, labels, test_size=0.2, random_state=42)

        self.classifier = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=10)
        self.classifier.fit(X_train, y_train)

        y_pred = self.classifier.predict(X_test)
        f1 = f1_score(y_test, y_pred)

        _LOGGER.info("Model trained. F1-score on test set: %.3f", f1)
        _LOGGER.debug("Classification report:\n%s", classification_report(y_test, y_pred))

        self.is_trained = True

    def score(self, metrics: HandshakeMetrics) -> float:
        """Return anomaly score (0.0 = normal, 1.0 = anomalous)."""
        if not self.is_trained:
            _LOGGER.warning("Classifier not trained; returning neutral score")
            return 0.5

        features = metrics.to_feature_vector().reshape(1, -1)
        # Get probability of anomalous class (class 1)
        proba = self.classifier.predict_proba(features)
        anomaly_prob = proba[0][1]

        # Apply suite-aware adjustment if suite is specified and overhead ranges are available
        if metrics.suite and metrics.suite in self.suite_overhead_ranges:
            overhead = self.suite_overhead_ranges[metrics.suite]
            if overhead:
                # Check if metrics are within expected range for this suite
                ct_min = overhead.get("ciphertext_size_min", 0)
                ct_max = overhead.get("ciphertext_size_max", float('inf'))
                pk_min = overhead.get("public_key_size_min", 0)
                pk_max = overhead.get("public_key_size_max", float('inf'))
                lat_min = overhead.get("latency_ms_min", 0)
                lat_max = overhead.get("latency_ms_max", float('inf'))

                # If all metrics are within expected range, reduce anomaly score
                # This prevents false positives from natural overhead of higher-security suites
                if (ct_min <= metrics.ciphertext_size <= ct_max and
                    pk_min <= metrics.public_key_size <= pk_max and
                    lat_min <= metrics.latency_ms <= lat_max):
                    # Reduce anomaly score by 50% if within expected range
                    adjusted_prob = anomaly_prob * 0.5
                    _LOGGER.debug("Suite-aware adjustment: %.3f -> %.3f (within expected range for %s)",
                                 anomaly_prob, adjusted_prob, metrics.suite)
                    return adjusted_prob
                else:
                    _LOGGER.debug("Metrics outside expected range for %s: ct=%d (exp %d-%d), pk=%d (exp %d-%d), lat=%.1f (exp %.1f-%.1f)",
                                 metrics.suite, metrics.ciphertext_size, ct_min, ct_max,
                                 metrics.public_key_size, pk_min, pk_max,
                                 metrics.latency_ms, lat_min, lat_max)

        _LOGGER.debug("Anomaly score: %.3f for latency=%.1fms", anomaly_prob, metrics.latency_ms)
        return anomaly_prob


# Global singleton instance
_detector = AnomalyDetector()


def get_detector() -> AnomalyDetector:
    """Get the global anomaly detector instance."""
    return _detector


def initialize_detector():
    """Initialize and train the detector with synthetic data."""
    _LOGGER.info("Initializing anomaly detector...")
    _detector.train()
    _LOGGER.info("Anomaly detector ready")
