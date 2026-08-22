"""Extrapolation-artifact test: seed boundary-zone examples, retrain, rerun dense probe.

Tests whether the three-plateau structure (0.0 / 0.65 / 0.87) shifts
after the model sees training examples in the 28-50ms gap.

Usage:
    python scripts/test_extrapolation_artifact.py
"""
import sys
import os
import csv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["OQS_INSTALL_PATH"] = r"C:\liboqs"

from ai_anomaly_detector import get_detector, HandshakeMetrics

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "datasets", "live_handshake_log.csv")
SUITE = "TLS_X25519_ML_KEM_768_WITH_AES_256_GCM_SHA3_256"


def dense_probe(detector, label):
    """Run the dense probe and return results as list of (latency, raw, score)."""
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


def print_results(results, label):
    print("%s" % label)
    print("-" * 40)
    for lat, raw, score in results:
        print("  %.1fms  raw=%.4f  score=%.4f" % (lat, raw, score))
    print()


def main():
    detector = get_detector()
    detector.load_model()
    detector.load_suite_overhead_ranges()
    detector.set_backend_mode(real=True)

    # Baseline: dense probe before seeding
    baseline = dense_probe(detector, "BASELINE (before seeding)")
    print_results(baseline, "BASELINE (before seeding)")

    # Seed 3 examples at boundary-zone latencies, labeled as normal
    # These are synthetic handshakes with latencies in the gap
    seed_rows = [
        # iteration, suite, latency_ms, latency_ns, ct_size, pk_size, success, variance, label, anomaly_type, rf_raw, score
        [999, SUITE, 32.0, 32000000, 1088, 1184, True, 0.0, 0, "seed_normal", 0.0, 0.0],
        [1000, SUITE, 38.0, 38000000, 1088, 1184, True, 0.0, 0, "seed_normal", 0.0, 0.0],
        [1001, SUITE, 44.0, 44000000, 1088, 1184, True, 0.0, 0, "seed_normal", 0.0, 0.0],
    ]

    with open(CSV_PATH, "a", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        for row in seed_rows:
            writer.writerow(row)

    print("Seeded 3 examples at 32ms, 38ms, 44ms (label=0, normal)")
    print()

    # Retrain
    detector.retrain_from_live_data(CSV_PATH, min_samples=10, mix_synthetic_ratio=0.3)
    print()

    # Dense probe after seeding
    after = dense_probe(detector, "AFTER SEEDING (32/38/44ms examples added)")
    print_results(after, "AFTER SEEDING (32/38/44ms examples added)")

    # Comparison
    print("COMPARISON")
    print("-" * 60)
    print("%-8s %-12s %-12s %s" % ("Latency", "Before", "After", "Changed?"))
    print("-" * 60)
    for (bl_lat, bl_raw, _), (af_lat, af_raw, _) in zip(baseline, after):
        changed = "YES" if abs(bl_raw - af_raw) > 0.001 else ""
        print("%-8.1f %-12.4f %-12.4f %s" % (bl_lat, bl_raw, af_raw, changed))


if __name__ == "__main__":
    main()
