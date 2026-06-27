"""Performance profiling harness for hybrid PQC handshakes.

Benchmarks and compares:
- Classical X25519-only handshakes
- Hybrid X25519 + ML-KEM-768 handshakes
- Measures latency, throughput, and overhead

Generates performance dataset for statistical analysis and validates
the ≤20% overhead target.
"""

import time
import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization
from oqs_middleware import create_kem

_LOGGER = logging.getLogger("benchmark")


class PerformanceBenchmark:
    """Benchmark harness for cryptographic operations."""

    def __init__(self, iterations: int = 100):
        self.iterations = iterations
        self.results = []

    def benchmark_x25519_only(self) -> Dict[str, float]:
        """Benchmark classical X25519-only ECDH."""
        _LOGGER.info("Benchmarking X25519-only (classical)...")
        latencies = []

        for _ in range(self.iterations):
            # Alice generates keypair and public key
            start = time.perf_counter()
            alice_priv = x25519.X25519PrivateKey.generate()
            alice_pub = alice_priv.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )

            # Bob generates keypair and performs exchange
            bob_priv = x25519.X25519PrivateKey.generate()
            bob_pub = bob_priv.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )

            # Key exchanges
            alice_shared = alice_priv.exchange(x25519.X25519PublicKey.from_public_bytes(bob_pub))
            bob_shared = bob_priv.exchange(x25519.X25519PublicKey.from_public_bytes(alice_pub))

            elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
            latencies.append(elapsed)

        return {
            "mean_latency_ms": float(np.mean(latencies)),
            "std_latency_ms": float(np.std(latencies)),
            "min_latency_ms": float(np.min(latencies)),
            "max_latency_ms": float(np.max(latencies)),
            "p50_latency_ms": float(np.percentile(latencies, 50)),
            "p95_latency_ms": float(np.percentile(latencies, 95)),
        }

    def benchmark_hybrid_handshake(self) -> Dict[str, float]:
        """Benchmark hybrid X25519 + ML-KEM-768."""
        _LOGGER.info("Benchmarking hybrid X25519 + ML-KEM-768...")
        latencies = []

        for _ in range(self.iterations):
            start = time.perf_counter()

            # Alice generates X25519 keypair
            alice_priv_classic = x25519.X25519PrivateKey.generate()
            alice_pub_classic = alice_priv_classic.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )

            # Alice generates ML-KEM-768 keypair
            alice_kem = create_kem("ML-KEM-768", force_real=False)
            alice_pub_pq = alice_kem.generate_keypair()

            # Bob generates X25519 keypair
            bob_priv_classic = x25519.X25519PrivateKey.generate()
            bob_pub_classic = bob_priv_classic.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )

            # Bob performs ECDH
            peer_pub_alice = x25519.X25519PublicKey.from_public_bytes(alice_pub_classic)
            shared_classic = bob_priv_classic.exchange(peer_pub_alice)

            # Bob performs KEM encapsulation
            bob_kem = create_kem("ML-KEM-768", force_real=False)
            ciphertext, shared_pq = bob_kem.encapsulate(alice_pub_pq)

            # Alice performs ECDH
            alice_shared_classic = alice_priv_classic.exchange(
                x25519.X25519PublicKey.from_public_bytes(bob_pub_classic)
            )

            # Alice performs KEM decapsulation
            alice_shared_pq = alice_kem.decapsulate(ciphertext)

            elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
            latencies.append(elapsed)

        return {
            "mean_latency_ms": float(np.mean(latencies)),
            "std_latency_ms": float(np.std(latencies)),
            "min_latency_ms": float(np.min(latencies)),
            "max_latency_ms": float(np.max(latencies)),
            "p50_latency_ms": float(np.percentile(latencies, 50)),
            "p95_latency_ms": float(np.percentile(latencies, 95)),
        }

    def run_comparison(self) -> pd.DataFrame:
        """Run full performance comparison."""
        _LOGGER.info("Running performance comparison (%d iterations each)...", self.iterations)

        classical = self.benchmark_x25519_only()
        hybrid = self.benchmark_hybrid_handshake()

        # Calculate overhead
        classical_mean = classical["mean_latency_ms"]
        hybrid_mean = hybrid["mean_latency_ms"]
        overhead_pct = ((hybrid_mean - classical_mean) / classical_mean) * 100

        result = {
            "Configuration": ["X25519 (Classical)", "X25519 + ML-KEM-768 (Hybrid)"],
            "Mean Latency (ms)": [classical["mean_latency_ms"], hybrid["mean_latency_ms"]],
            "Std Dev (ms)": [classical["std_latency_ms"], hybrid["std_latency_ms"]],
            "Min (ms)": [classical["min_latency_ms"], hybrid["min_latency_ms"]],
            "Max (ms)": [classical["max_latency_ms"], hybrid["max_latency_ms"]],
            "P50 (ms)": [classical["p50_latency_ms"], hybrid["p50_latency_ms"]],
            "P95 (ms)": [classical["p95_latency_ms"], hybrid["p95_latency_ms"]],
        }

        df = pd.DataFrame(result)

        _LOGGER.info("\n=== Performance Comparison ===")
        _LOGGER.info("\n%s", df.to_string(index=False))
        _LOGGER.info("\nOverhead: %.1f%% (target: ≤20%%)", overhead_pct)
        _LOGGER.info("Result: %s", "PASS" if overhead_pct <= 20.0 else "FAIL")

        return df, overhead_pct

    def generate_detailed_report(self) -> str:
        """Generate a detailed performance report."""
        df, overhead_pct = self.run_comparison()

        report = f"""
=== Triple Shield Architecture (3SA) Performance Report ===

Test Parameters:
- Iterations per configuration: {self.iterations}
- Backend: {'real oqs' if False else 'mock KEM (for testing)'}

Results:
{df.to_string(index=False)}

Performance Analysis:
- Classical X25519 baseline: {df.loc[0, 'Mean Latency (ms)']:.3f} ms
- Hybrid X25519 + ML-KEM-768: {df.loc[1, 'Mean Latency (ms)']:.3f} ms
- Overhead: {overhead_pct:.1f}%

Success Criteria Validation:
- Target Overhead: ≤20%
- Achieved Overhead: {overhead_pct:.1f}%
- Status: {"✓ PASS" if overhead_pct <= 20.0 else "✗ FAIL"}

Interpretation:
The hybrid handshake {"meets" if overhead_pct <= 20.0 else "exceeds"} the target overhead threshold.
This indicates that the integration of post-quantum cryptography
{"is operationally feasible" if overhead_pct <= 20.0 else "requires optimization"}.
"""
        return report


def run_benchmark(iterations: int = 100) -> Tuple[pd.DataFrame, float, str]:
    """Run the full benchmark suite."""
    logging.basicConfig(level=logging.INFO, format="[benchmark] %(levelname)s: %(message)s")
    benchmark = PerformanceBenchmark(iterations=iterations)
    df, overhead_pct = benchmark.run_comparison()
    report = benchmark.generate_detailed_report()
    return df, overhead_pct, report


if __name__ == "__main__":
    df, overhead_pct, report = run_benchmark(iterations=50)
    print(report)
