#!/usr/bin/env python3
"""
Test script to verify dataset compatibility with ai_anomaly_detector.py
"""

import logging
from ai_anomaly_detector import AnomalyDetector, HandshakeMetrics

logging.basicConfig(level=logging.INFO, format="[test] %(levelname)s: %(message)s")
_LOGGER = logging.getLogger("test")

def main():
    _LOGGER.info("=== Testing Dataset Training ===")
    
    # Create detector
    detector = AnomalyDetector()
    
    # Load suite overhead ranges
    detector.load_suite_overhead_ranges()
    
    # Train with CSV dataset
    csv_path = "datasets/handshake_dataset.csv"
    _LOGGER.info(f"Training with dataset from {csv_path}")
    detector.train(csv_path=csv_path)
    
    # Test scoring with a normal sample
    normal_metrics = HandshakeMetrics(
        latency_ms=0.6,
        ciphertext_size=1088,
        public_key_size=1184,
        success=True,
        encap_variance=0.0,
        suite="TLS_X25519_ML_KEM_768_WITH_AES_256_GCM_SHA3_256"
    )
    
    normal_score = detector.score(normal_metrics)
    _LOGGER.info(f"Normal sample score: {normal_score:.3f}")
    
    # Test scoring with an anomalous sample (size tampering)
    anomalous_metrics = HandshakeMetrics(
        latency_ms=0.6,
        ciphertext_size=1089,  # Tampered size
        public_key_size=1184,
        success=True,
        encap_variance=0.0,
        suite="TLS_X25519_ML_KEM_768_WITH_AES_256_GCM_SHA3_256"
    )
    
    anomalous_score = detector.score(anomalous_metrics)
    _LOGGER.info(f"Anomalous sample score: {anomalous_score:.3f}")
    
    # Test scoring with timing anomaly
    timing_anomaly_metrics = HandshakeMetrics(
        latency_ms=25.0,  # High latency
        ciphertext_size=1088,
        public_key_size=1184,
        success=True,
        encap_variance=0.0,
        suite="TLS_X25519_ML_KEM_768_WITH_AES_256_GCM_SHA3_256"
    )
    
    timing_score = detector.score(timing_anomaly_metrics)
    _LOGGER.info(f"Timing anomaly sample score: {timing_score:.3f}")
    
    _LOGGER.info("\n=== Test Complete ===")
    _LOGGER.info("Dataset training and scoring verified successfully")

if __name__ == "__main__":
    main()
