"""Analyze pre/post persistence split and synthetic mixing ratio.

Splits the live handshake log into pre-persistence and post-persistence
rows based on rf_raw_probability, and reports the synthetic mix ratio
at the current sample count.

Usage:
    python scripts/analyze_persistence_split.py
"""
import csv
import os

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "datasets", "live_handshake_log.csv")


def main():
    with open(CSV_PATH) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    normal_rows = [r for r in rows if r["label"] == "0"]
    pre_persist = [r for r in normal_rows if float(r["rf_raw_probability"]) > 0.5]
    post_persist = [r for r in normal_rows if float(r["rf_raw_probability"]) <= 0.01]

    print("Normal rows: %d" % len(normal_rows))
    print("  Pre-persistence (rf_raw > 0.5): %d" % len(pre_persist))
    print("  Post-persistence (rf_raw <= 0.01): %d" % len(post_persist))
    print()

    if pre_persist:
        rf_pre = [float(r["rf_raw_probability"]) for r in pre_persist]
        print("Pre-persistence rf_raw: min=%.4f max=%.4f mean=%.4f" % (min(rf_pre), max(rf_pre), sum(rf_pre) / len(rf_pre)))

    if post_persist:
        rf_post = [float(r["rf_raw_probability"]) for r in post_persist]
        lat_post = [float(r["latency_ms"]) for r in post_persist]
        print("Post-persistence rf_raw: min=%.4f max=%.4f mean=%.4f" % (min(rf_post), max(rf_post), sum(rf_post) / len(rf_post)))
        print("Post-persistence latency: min=%.1f max=%.1f mean=%.1f" % (min(lat_post), max(lat_post), sum(lat_post) / len(lat_post)))

    total_live = len(rows) - 1
    n_synth = max(int(total_live * 0.3), 20)
    print()
    print("Synthetic mix at N=%d: %d synthetic (%.0f%%)" % (total_live, n_synth, n_synth / (total_live + n_synth) * 100))


if __name__ == "__main__":
    main()
