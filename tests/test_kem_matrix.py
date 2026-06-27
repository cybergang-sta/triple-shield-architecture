"""Feature test: exercise multiple KEM algorithms and negotiation.

Run this script from the project root with the virtualenv active:

    python tests/test_kem_matrix.py

It will try configured policy algorithms and verify the handshake succeeds
using the middleware (which may use the mock backend if `oqs` is not installed).
"""
import sys
import os
import time
import subprocess

# Add parent directory to path to find project modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from oqs_middleware import get_policy, available_kems_for_env


def run_matrix():
    policy = get_policy()
    fallback = policy.get("fallback_order", [])
    server_kems = available_kems_for_env()
    print("Policy fallback order:", fallback)
    print("Server available kems:", server_kems)

    candidates = fallback or server_kems
    results = []
    for alg in candidates:
        print(f"\n--- Testing KEM {alg} ---")
        try:
            start = time.time()
            # invoke the script as a subprocess to avoid import-name issues
            proc = subprocess.run([sys.executable, "3SA.py", "--kem", alg], check=False, capture_output=True, text=True)
            elapsed = time.time() - start
            ok = proc.returncode == 0
            out = proc.stdout + proc.stderr
            status = "ok" if ok else f"error (rc={proc.returncode})"
            print(out)
            results.append((alg, status, elapsed))
        except Exception as e:
            results.append((alg, f"error: {e}", None))

    print("\nSummary:")
    for r in results:
        print(r)


if __name__ == "__main__":
    run_matrix()
