"""Validate CSV integrity: check for label contamination and rf_raw stats.

Reads the live handshake log and verifies:
- All label=1 rows have latency above the ML-KEM-768 threshold (30ms)
- rf_raw_probability distribution for normal rows
- Total counts and contamination check

Usage:
    python scripts/validate_csv_integrity.py
"""
import csv
import os

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "datasets", "live_handshake_log.csv")


def main():
    with open(CSV_PATH) as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total = len(rows)
    normal_rows = [r for r in rows if r["label"] == "0"]
    anomalous_rows = [r for r in rows if r["label"] == "1"]

    print("Total:", total)
    print("Normal (label=0):", len(normal_rows))
    print("Anomalous (label=1):", len(anomalous_rows))
    print()
    print("Anomalous rows (all should have latency >30ms):")
    for r in anomalous_rows:
        lat = float(r["latency_ms"])
        print("  latency=%.1fms  type=%s  rf_raw=%s" % (lat, r["anomaly_type"], r["rf_raw_probability"]))

    contaminated = [r for r in anomalous_rows if float(r["latency_ms"]) <= 30.0]
    print()
    print("Contaminated (label=1 with latency <= 30ms):", len(contaminated))
    if contaminated:
        for r in contaminated:
            print("  CONTAMINATION: latency=%.1fms label=1" % float(r["latency_ms"]))
    else:
        print("  None - file is clean")

    rf_vals = [float(r["rf_raw_probability"]) for r in normal_rows]
    print()
    print("rf_raw stats for normal rows:")
    print("  min=%.4f  max=%.4f  mean=%.4f" % (min(rf_vals), max(rf_vals), sum(rf_vals) / len(rf_vals)))


if __name__ == "__main__":
    main()
