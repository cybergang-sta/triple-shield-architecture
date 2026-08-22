"""Boundary test: probe the RF's actual belief in the 30-45ms gap.

The guardrail forces score=1.0 for anything above 30ms (ML-KEM-768),
so we bypass the CLI entirely and call raw_score() directly on
HandshakeMetrics constructed at specific latencies.

This tests whether the RF's learned boundary is robust or noisy
in the one region where it actually matters.

Usage:
    python scripts/boundary_test.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["OQS_INSTALL_PATH"] = r"C:\liboqs"

from ai_anomaly_detector import get_detector, HandshakeMetrics

PROBE_LATENCIES = [
    (20.0, "well below boundary (control)"),
    (25.0, "below boundary"),
    (28.0, "just below gap"),
    (32.0, "just above 30ms threshold (inside gap)"),
    (35.0, "mid-gap"),
    (38.0, "mid-gap"),
    (41.0, "mid-gap"),
    (44.0, "approaching anomaly cluster"),
    (48.0, "near anomaly cluster"),
    (55.0, "inside anomaly cluster (control)"),
    (70.0, "deep anomaly cluster (control)"),
]

SUITE = "TLS_X25519_ML_KEM_768_WITH_AES_256_GCM_SHA3_256"


def main():
    detector = get_detector()
    detector.load_model()
    detector.load_suite_overhead_ranges()
    detector.set_backend_mode(real=True)

    print("Boundary Test: RF raw probability across the 30-45ms gap")
    print("=" * 72)
    print("%-8s %-40s %s" % ("Latency", "Context", "RF Raw"))
    print("-" * 72)

    for lat, ctx in PROBE_LATENCIES:
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
        print("%-8.1f %-40s raw=%.4f  score=%.4f" % (lat, ctx, raw, score))

    print("-" * 72)
    print("Guardrail threshold for ML-KEM-768: 30ms")
    print("Anything above 30ms gets score=1.0 from the guardrail (not the RF).")
    print("RF raw is the only honest read of the model's belief in the gap.")


if __name__ == "__main__":
    main()
