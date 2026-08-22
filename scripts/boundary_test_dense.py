"""Dense boundary test: 1ms spacing from 36-48ms to locate the RF transition precisely.

Follow-up to boundary_test.py — probes every 1ms in the transition zone
to characterize where the RF's step function actually sits.

Usage:
    python scripts/boundary_test_dense.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["OQS_INSTALL_PATH"] = r"C:\liboqs"

from ai_anomaly_detector import get_detector, HandshakeMetrics

SUITE = "TLS_X25519_ML_KEM_768_WITH_AES_256_GCM_SHA3_256"


def main():
    detector = get_detector()
    detector.load_model()
    detector.load_suite_overhead_ranges()
    detector.set_backend_mode(real=True)

    probe_latencies = [36.0 + i for i in range(13)]  # 36.0 to 48.0 inclusive

    print("Dense Boundary Test: RF raw probability at 1ms spacing")
    print("=" * 72)
    print("%-8s %s" % ("Latency", "RF Raw"))
    print("-" * 72)

    for lat in probe_latencies:
        m = HandshakeMetrics(
            latency_ms=lat,
            ciphertext_size=1088,
            public_key_size=1184,
            success=True,
            encap_variance=0.0,
            suite=SUITE,
        )
        raw = detector.raw_score(m)
        score = detector.score(m)
        print("%-8.1f raw=%.4f  score=%.4f" % (lat, raw, score))

    print("-" * 72)


if __name__ == "__main__":
    main()
