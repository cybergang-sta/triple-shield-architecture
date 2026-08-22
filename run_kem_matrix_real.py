#!/usr/bin/env python3
"""Run 3SA.py for each enabled oqs KEM reported by `oqs_middleware.available_kems_for_env()`.

Usage: python run_kem_matrix_real.py
"""
import os
import subprocess
import sys
import time
import argparse
from oqs_middleware import available_kems_for_env


def safe_name(alg: str) -> str:
    name = alg.replace('/', '_').replace(' ', '_').replace('-', '_').replace('+', 'plus')
    return name


def main():
    parser = argparse.ArgumentParser(description="Run 3SA.py across enabled oqs KEMs")
    parser.add_argument("--force-real", action="store_true", help="Pass --force-real to 3SA.py to force real oqs backend")
    args = parser.parse_args()

    kems = available_kems_for_env()
    print("Server available kems:", kems)
    results = []
    for alg in kems:
        print(f"\n--- Testing KEM {alg} ---")
        out_file = os.path.join("datasets", "per-kem-tests", f"test_dataset_{safe_name(alg)}.csv")
        cmd = [sys.executable, "3SA.py", "--kem", alg, "--dataset-output", out_file]
        if args.force_real:
            cmd.append("--force-real")
        start = time.time()
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
        elapsed = time.time() - start
        ok = proc.returncode == 0
        # Print outputs (stdout first, then stderr)
        if proc.stdout:
            print(proc.stdout)
        if proc.stderr:
            print(proc.stderr, file=sys.stderr)
        results.append((alg, "ok" if ok else f"error (rc={proc.returncode})", elapsed, proc.returncode))

    print("\nSummary:")
    for r in results:
        print(r)


if __name__ == "__main__":
    main()
