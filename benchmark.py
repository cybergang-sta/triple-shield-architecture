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
from typing import Dict, List, Tuple, Optional
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from oqs_middleware import create_kem
import json

_LOGGER = logging.getLogger("benchmark")


class PerformanceBenchmark:
    """Benchmark harness for cryptographic operations with high-resolution logging."""

    def __init__(self, iterations: int = 100, log_detailed: bool = True):
        self.iterations = iterations
        self.results = []
        self.log_detailed = log_detailed
        self.detailed_logs = []

    def benchmark_x25519_only(self) -> Dict[str, float]:
        """Benchmark classical X25519-only ECDH with high-resolution logging."""
        _LOGGER.info("Benchmarking X25519-only (classical)...")
        latencies = []
        operation_times = []

        for i in range(self.iterations):
            iteration_log = {
                "iteration": i,
                "configuration": "X25519-classical",
                "public_key_size_bytes": 32,
                "ciphertext_size_bytes": 0,
                "oqs_error": None
            }

            # Alice generates keypair and public key
            start_ns = time.perf_counter_ns()
            alice_priv = x25519.X25519PrivateKey.generate()
            alice_pub = alice_priv.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
            alice_keygen_ns = time.perf_counter_ns() - start_ns

            # Bob generates keypair and performs exchange
            bob_priv = x25519.X25519PrivateKey.generate()
            bob_pub = bob_priv.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )

            # Key exchanges
            start_ns = time.perf_counter_ns()
            alice_shared = alice_priv.exchange(x25519.X25519PublicKey.from_public_bytes(bob_pub))
            bob_shared = bob_priv.exchange(x25519.X25519PublicKey.from_public_bytes(alice_pub))
            key_exchange_ns = time.perf_counter_ns() - start_ns

            elapsed_ms = (alice_keygen_ns + key_exchange_ns) / 1_000_000
            latencies.append(elapsed_ms)

            if self.log_detailed:
                iteration_log.update({
                    "alice_keygen_ns": alice_keygen_ns,
                    "key_exchange_ns": key_exchange_ns,
                    "total_latency_ns": alice_keygen_ns + key_exchange_ns,
                    "total_latency_ms": elapsed_ms
                })
                self.detailed_logs.append(iteration_log)

        return {
            "mean_latency_ms": float(np.mean(latencies)),
            "std_latency_ms": float(np.std(latencies)),
            "min_latency_ms": float(np.min(latencies)),
            "max_latency_ms": float(np.max(latencies)),
            "p50_latency_ms": float(np.percentile(latencies, 50)),
            "p95_latency_ms": float(np.percentile(latencies, 95)),
            "mean_latency_ns": float(np.mean([log["total_latency_ns"] for log in self.detailed_logs if log["configuration"] == "X25519-classical"])),
        }

    def benchmark_hybrid_handshake(self) -> Dict[str, float]:
        """Benchmark hybrid X25519 + ML-KEM-768 with high-resolution logging."""
        _LOGGER.info("Benchmarking hybrid X25519 + ML-KEM-768...")
        latencies = []

        for i in range(self.iterations):
            iteration_log = {
                "iteration": i,
                "configuration": "X25519-ML-KEM-768",
                "oqs_error": None
            }

            # Alice generates X25519 keypair
            start_ns = time.perf_counter_ns()
            alice_priv_classic = x25519.X25519PrivateKey.generate()
            alice_pub_classic = alice_priv_classic.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
            alice_x25519_keygen_ns = time.perf_counter_ns() - start_ns

            # Alice generates ML-KEM-768 keypair
            start_ns = time.perf_counter_ns()
            alice_kem = create_kem("ML-KEM-768", force_real=False)
            alice_pub_pq = alice_kem.generate_keypair()
            alice_kem_keygen_ns = time.perf_counter_ns() - start_ns
            iteration_log["public_key_size_bytes"] = len(alice_pub_pq)

            # Bob generates X25519 keypair
            start_ns = time.perf_counter_ns()
            bob_priv_classic = x25519.X25519PrivateKey.generate()
            bob_pub_classic = bob_priv_classic.public_key().public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw,
            )
            bob_x25519_keygen_ns = time.perf_counter_ns() - start_ns

            # Bob performs ECDH
            start_ns = time.perf_counter_ns()
            peer_pub_alice = x25519.X25519PublicKey.from_public_bytes(alice_pub_classic)
            shared_classic = bob_priv_classic.exchange(peer_pub_alice)
            bob_ecdh_ns = time.perf_counter_ns() - start_ns

            # Bob performs KEM encapsulation
            start_ns = time.perf_counter_ns()
            bob_kem = create_kem("ML-KEM-768", force_real=False)
            ciphertext, shared_pq = bob_kem.encapsulate(alice_pub_pq)
            bob_encap_ns = time.perf_counter_ns() - start_ns
            iteration_log["ciphertext_size_bytes"] = len(ciphertext)

            # Alice performs ECDH
            start_ns = time.perf_counter_ns()
            alice_shared_classic = alice_priv_classic.exchange(
                x25519.X25519PublicKey.from_public_bytes(bob_pub_classic)
            )
            alice_ecdh_ns = time.perf_counter_ns() - start_ns

            # Alice performs KEM decapsulation
            start_ns = time.perf_counter_ns()
            alice_shared_pq = alice_kem.decapsulate(ciphertext)
            alice_decap_ns = time.perf_counter_ns() - start_ns

            # HKDF-SHA3-256 secret fusion
            start_ns = time.perf_counter_ns()
            hkdf = HKDF(
                algorithm=hashes.SHA3_256(),
                length=32,
                salt=b"hybrid-pqc-v1-fusion",
                info=b"hybrid-pqc-v1-fusion",
            )
            final_key = hkdf.derive(shared_classic + alice_shared_pq)
            hkdf_ns = time.perf_counter_ns() - start_ns

            total_ns = (alice_x25519_keygen_ns + alice_kem_keygen_ns + 
                       bob_x25519_keygen_ns + bob_ecdh_ns + 
                       bob_encap_ns + alice_ecdh_ns + alice_decap_ns + hkdf_ns)
            elapsed_ms = total_ns / 1_000_000
            latencies.append(elapsed_ms)

            if self.log_detailed:
                iteration_log.update({
                    "alice_x25519_keygen_ns": alice_x25519_keygen_ns,
                    "alice_kem_keygen_ns": alice_kem_keygen_ns,
                    "bob_x25519_keygen_ns": bob_x25519_keygen_ns,
                    "bob_ecdh_ns": bob_ecdh_ns,
                    "bob_encap_ns": bob_encap_ns,
                    "alice_ecdh_ns": alice_ecdh_ns,
                    "alice_decap_ns": alice_decap_ns,
                    "hkdf_ns": hkdf_ns,
                    "total_latency_ns": total_ns,
                    "total_latency_ms": elapsed_ms
                })
                self.detailed_logs.append(iteration_log)

        return {
            "mean_latency_ms": float(np.mean(latencies)),
            "std_latency_ms": float(np.std(latencies)),
            "min_latency_ms": float(np.min(latencies)),
            "max_latency_ms": float(np.max(latencies)),
            "p50_latency_ms": float(np.percentile(latencies, 50)),
            "p95_latency_ms": float(np.percentile(latencies, 95)),
            "mean_latency_ns": float(np.mean([log["total_latency_ns"] for log in self.detailed_logs if log["configuration"] == "X25519-ML-KEM-768"])),
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
        """Generate a detailed performance report with operation-level metrics."""
        df, overhead_pct = self.run_comparison()

        # Calculate operation-level statistics for hybrid
        hybrid_logs = [log for log in self.detailed_logs if log["configuration"] == "X25519-ML-KEM-768"]
        if hybrid_logs:
            encap_times = [log["bob_encap_ns"] for log in hybrid_logs]
            decap_times = [log["alice_decap_ns"] for log in hybrid_logs]
            hkdf_times = [log["hkdf_ns"] for log in hybrid_logs]
            pk_sizes = [log["public_key_size_bytes"] for log in hybrid_logs]
            ct_sizes = [log["ciphertext_size_bytes"] for log in hybrid_logs]

        report = f"""
=== Triple Shield Architecture (3SA) Performance Report ===

Test Parameters:
- Iterations per configuration: {self.iterations}
- Backend: {'real oqs' if False else 'mock KEM (for testing)'}
- High-Resolution Logging: {'enabled' if self.log_detailed else 'disabled'}

Results:
{df.to_string(index=False)}

Performance Analysis:
- Classical X25519 baseline: {df.loc[0, 'Mean Latency (ms)']:.3f} ms
- Hybrid X25519 + ML-KEM-768: {df.loc[1, 'Mean Latency (ms)']:.3f} ms
- Overhead: {overhead_pct:.1f}%

"""
        if hybrid_logs:
            report += f"""
Operation-Level Metrics (Hybrid):
- ML-KEM Encapsulation: {np.mean(encap_times) / 1_000_000:.3f} ms (mean)
- ML-KEM Decapsulation: {np.mean(decap_times) / 1_000_000:.3f} ms (mean)
- HKDF-SHA3-256 Fusion: {np.mean(hkdf_times) / 1_000_000:.3f} ms (mean)
- Public Key Size: {np.mean(pk_sizes):.0f} bytes (exact: {pk_sizes[0]})
- Ciphertext Size: {np.mean(ct_sizes):.0f} bytes (exact: {ct_sizes[0]})

"""
        report += f"""
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

    def export_detailed_logs(self, filename: str = "benchmark_detailed_logs.json") -> None:
        """Export detailed logs to JSON file for analysis."""
        if not self.detailed_logs:
            _LOGGER.warning("No detailed logs to export")
            return
        
        with open(filename, "w") as f:
            json.dump(self.detailed_logs, f, indent=2)
        _LOGGER.info("Detailed logs exported to %s", filename)


def run_benchmark(iterations: int = 100, log_detailed: bool = True) -> Tuple[pd.DataFrame, float, str]:
    """Run the full benchmark suite with high-resolution logging."""
    logging.basicConfig(level=logging.INFO, format="[benchmark] %(levelname)s: %(message)s")
    benchmark = PerformanceBenchmark(iterations=iterations, log_detailed=log_detailed)
    df, overhead_pct = benchmark.run_comparison()
    report = benchmark.generate_detailed_report()
    
    if log_detailed:
        benchmark.export_detailed_logs()
    
    return df, overhead_pct, report


if __name__ == "__main__":
    df, overhead_pct, report = run_benchmark(iterations=50, log_detailed=True)
    print(report)
