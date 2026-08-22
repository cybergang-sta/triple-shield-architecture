"""Control test: retrain on unmodified CSV (no seed rows), rerun dense probe.

Tests whether retrain-to-retrain synthetic noise alone causes movement
in the 38-48ms range, or whether the seeding effect is cleanly attributable.

Usage:
    python scripts/test_retrain_control.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["OQS_INSTALL_PATH"] = r"C:\liboqs"

from ai_anomaly_detector import get_detector, HandshakeMetrics

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "datasets", "live", "live_handshake_log.csv")
SUITE = "TLS_X25519_ML_KEM_768_WITH_AES_256_GCM_SHA3_256"


def dense_probe(detector):
    results = []
    for i in range(13):
        lat = 36.0 + i
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
        results.append((lat, raw, score))
    return results


def main():
    detector = get_detector()
    detector.load_model()
    detector.load_suite_overhead_ranges()
    detector.set_backend_mode(real=True)

    # Baseline
    baseline = dense_probe(detector)
    print("BASELINE (loaded from disk)")
    print("-" * 40)
    for lat, raw, score in baseline:
        print("  %.1fms  raw=%.4f" % (lat, raw))
    print()

    # Retrain on the SAME unmodified CSV (no seed rows)
    detector.retrain_from_live_data(CSV_PATH, min_samples=10, mix_synthetic_ratio=0.3)
    print()

    # Probe after retrain
    after = dense_probe(detector)
    print("AFTER RETRAIN (same CSV, no seed rows)")
    print("-" * 40)
    for lat, raw, score in after:
        print("  %.1fms  raw=%.4f" % (lat, raw))
    print()

    # Comparison
    print("COMPARISON (synthetic-noise-only control)")
    print("-" * 60)
    print("%-8s %-12s %-12s %s" % ("Latency", "Before", "After", "Changed?"))
    print("-" * 60)
    for (bl_lat, bl_raw, _), (af_lat, af_raw, _) in zip(baseline, after):
        changed = "YES" if abs(bl_raw - af_raw) > 0.001 else ""
        print("%-8.1f %-12.4f %-12.4f %s" % (bl_lat, bl_raw, af_raw, changed))


if __name__ == "__main__":
    main()
