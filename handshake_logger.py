"""Handshake data logger for anomaly detector training.

Appends structured CSV rows after each handshake so that real (and mock)
runs accumulate into a training dataset.  The column layout matches the
existing ``datasets/handshake_dataset.csv`` produced by
``generate_dataset.py`` so the file can be fed directly into
``AnomalyDetector.load_training_data_from_csv()``.
"""

import csv
import logging
import os
import threading
import time
from typing import Optional

_LOGGER = logging.getLogger("handshake_logger")

CSV_HEADER = [
    "iteration",
    "suite",
    "latency_ms",
    "latency_ns",
    "ciphertext_size",
    "public_key_size",
    "success",
    "encap_variance",
    "label",
    "anomaly_type",
]


class HandshakeLogger:
    """Thread-safe CSV logger that accumulates handshake records."""

    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self._lock = threading.Lock()
        self._iteration = 0
        self._ensure_file()

    def _ensure_file(self):
        """Create the CSV with a header row if it does not yet exist."""
        needs_header = not os.path.isfile(self.csv_path) or os.path.getsize(self.csv_path) == 0
        if needs_header:
            with self._lock:
                with open(self.csv_path, "w", newline="", encoding="utf-8") as fh:
                    csv.writer(fh).writerow(CSV_HEADER)
            _LOGGER.info("Created handshake log: %s", self.csv_path)

    def log(
        self,
        *,
        latency_ms: float,
        latency_ns: int,
        ciphertext_size: int,
        public_key_size: int,
        success: bool,
        encap_variance: float,
        suite: str,
        label: int = 0,
        anomaly_type: str = "normal",
    ):
        """Append one handshake record to the CSV."""
        self._iteration += 1
        row = [
            self._iteration,
            suite,
            latency_ms,
            latency_ns,
            ciphertext_size,
            public_key_size,
            success,
            encap_variance,
            label,
            anomaly_type,
        ]
        with self._lock:
            with open(self.csv_path, "a", newline="", encoding="utf-8") as fh:
                csv.writer(fh).writerow(row)
        _LOGGER.debug("Logged handshake #%d to %s", self._iteration, self.csv_path)

    def log_from_metrics(self, metrics, anomaly_score: float, suite: Optional[str] = None, test_scenario: Optional[str] = None, latency_ns: int = 0, anomaly_threshold: float = 0.5):
        """Convenience wrapper that derives label and anomaly_type from context.

        Parameters
        ----------
        metrics : HandshakeMetrics
            The metrics object from the current handshake.
        anomaly_score : float
            Score returned by ``AnomalyDetector.score()``.
        suite : str, optional
            Suite name override (e.g. from agility controller).
        test_scenario : str or None
            If a ``--test-scenario`` was injected, this is its name.
        latency_ns : int
            High-resolution nanosecond timing (from ``time.perf_counter_ns``).
        anomaly_threshold : float
            Suite-specific threshold from policy.json (e.g. 0.6 for ML-KEM-768).
            Labels are derived using this threshold, not a flat 0.5, so that
            training labels match the agility controller's decision boundary.
        """
        suite_name = suite or getattr(metrics, "suite", "unknown") or "unknown"

        # Derive label from anomaly score using suite-specific threshold
        label = 1 if anomaly_score > anomaly_threshold else 0

        # Derive anomaly_type
        if test_scenario and test_scenario != "normal":
            anomaly_type = test_scenario
        elif not metrics.success:
            anomaly_type = "implicit_rejection"
        elif label == 1:
            anomaly_type = "anomaly_detected"
        else:
            anomaly_type = "normal"

        self.log(
            latency_ms=metrics.latency_ms,
            latency_ns=latency_ns,
            ciphertext_size=metrics.ciphertext_size,
            public_key_size=metrics.public_key_size,
            success=metrics.success,
            encap_variance=metrics.encap_variance,
            suite=suite_name,
            label=label,
            anomaly_type=anomaly_type,
        )


# Global singleton
_logger_instance: Optional[HandshakeLogger] = None


def get_handshake_logger(csv_path: Optional[str] = None) -> Optional[HandshakeLogger]:
    """Get or create the global handshake logger.

    Returns ``None`` if no *csv_path* has been set yet (i.e. logging is
    disabled for this run).
    """
    global _logger_instance
    if csv_path is not None and _logger_instance is None:
        _logger_instance = HandshakeLogger(csv_path)
    return _logger_instance


def reset_handshake_logger():
    """Reset the global singleton (used in tests)."""
    global _logger_instance
    _logger_instance = None
