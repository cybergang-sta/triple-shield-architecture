"""Observe model behavior across multiple iterations.

Runs 20 handshakes in a single process, logging rf_raw_probability and
anomaly_score to a CSV after each one. Shows how the RF's raw belief
evolves as live data accumulates within a single process run.

Usage:
    python scripts/observe_model_iterations.py
"""
import sys, os, time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["OQS_INSTALL_PATH"] = r"C:\liboqs"

import oqs
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from ai_anomaly_detector import initialize_detector, get_detector, HandshakeMetrics
from agility_controller import initialize_controller, get_controller, AgilityEvent
from handshake_logger import HandshakeLogger

CSV_PATH = os.path.join(os.path.dirname(__file__), "..", "datasets", "live_handshake_log.csv")


def fuse(s1, s2):
    return HKDF(algorithm=hashes.SHA3_256(), length=32, salt=None, info=b"hybrid-pqc-v1-fusion").derive(s1 + s2)


def main():
    initialize_detector()
    detector = get_detector()
    detector.load_suite_overhead_ranges()
    detector.set_backend_mode(real=True)

    initialize_controller()
    controller = get_controller()

    session_id = "observe"
    session = controller.create_session(session_id, initial_suite="TLS_X25519_ML_KEM_768_WITH_AES_256_GCM_SHA3_256")

    logger = HandshakeLogger(CSV_PATH)

    existing = 0
    if os.path.isfile(CSV_PATH):
        with open(CSV_PATH) as f:
            existing = sum(1 for _ in f) - 1

    print("=" * 90)
    print("3SA MODEL OBSERVATION RUN")
    print("=" * 90)
    print("  Existing live samples : %d" % existing)
    print("  Iterations to run    : 20")
    print("  Starting suite        : ML-KEM-768")
    print("  Retrain min_samples   : 10")
    print("  Synthetic mix ratio   : 30%%" )
    print("=" * 90)
    print()
    print("%4s %8s %7s %7s %5s %5s %14s %s" % ("Iter", "Latency", "RF Raw", "Score", "Label", "Key", "Suite", "Action"))
    print("-" * 90)

    for i in range(1, 21):
        start = time.perf_counter()

        alice_priv = x25519.X25519PrivateKey.generate()
        alice_pub = alice_priv.public_key().public_bytes_raw()

        kem = oqs.KeyEncapsulation("ML-KEM-768")
        pq_pub = kem.generate_keypair()

        bob_priv = x25519.X25519PrivateKey.generate()
        bob_pub = bob_priv.public_key().public_bytes_raw()
        cls_secret_bob = bob_priv.exchange(x25519.X25519PublicKey.from_public_bytes(alice_pub))
        cls_secret_alice = alice_priv.exchange(x25519.X25519PublicKey.from_public_bytes(bob_pub))

        ciphertext, pq_secret_bob = kem.encap_secret(pq_pub)
        pq_secret_alice = kem.decap_secret(ciphertext)
        kem.free()

        alice_key = fuse(cls_secret_alice, pq_secret_alice)
        bob_key = fuse(cls_secret_bob, pq_secret_bob)
        elapsed_ms = (time.perf_counter() - start) * 1000
        match = alice_key == bob_key

        metrics = HandshakeMetrics(
            latency_ms=elapsed_ms,
            ciphertext_size=len(ciphertext),
            public_key_size=len(pq_pub),
            success=match,
            encap_variance=0.0,
            suite=session.current_suite,
        )

        rf_raw = detector.raw_score(metrics)
        score = detector.score(metrics)

        suite_def = controller.get_suite_definition(session.current_suite)
        threshold = suite_def.get("anomaly_threshold", 0.6) if suite_def else 0.6
        label = 1 if score > threshold else 0

        logger.log(
            latency_ms=elapsed_ms,
            latency_ns=int(elapsed_ms * 1_000_000),
            ciphertext_size=len(ciphertext),
            public_key_size=len(pq_pub),
            success=match,
            encap_variance=0.0,
            suite=session.current_suite,
            label=label,
            anomaly_type="normal",
            rf_raw_probability=rf_raw,
            anomaly_score=score,
        )

        event, new_suite = controller.evaluate_agility(session_id, score, match)
        action = ""
        if event != AgilityEvent.NONE and new_suite:
            controller.transition_suite(session_id, session.current_suite, new_suite, event)
            action = "RENEGOTIATE -> %s" % new_suite.split("_ML_")[1].split("_WITH")[0].replace("_", "-")

        total = existing + i
        retrained = False
        if total >= 10:
            retrained = detector.retrain_from_live_data(CSV_PATH, min_samples=10, mix_synthetic_ratio=0.3)

        action_str = action if action else ("RETRAINED" if retrained else "")
        print("%4d %7.2fms %7.4f %7.4f %5d %5s %14s %s" % (i, elapsed_ms, rf_raw, score, label, "OK" if match else "FAIL", "ML-KEM-768", action_str))

    print()
    print("=" * 90)
    print("OBSERVATION COMPLETE")
    print("  Total live samples now : %d" % (existing + 20))
    print("  Model retrained        : every iteration (after iter 1, when >= 10 samples)")
    print("  F1 should stabilize    : as RF trains on more real latency data")
    print("=" * 90)


if __name__ == "__main__":
    main()
