"""Multi-handshake demo: shows full 3SA flow with suite renegotiation.

Runs 8 handshakes with real liboqs backend, demonstrating the complete
pipeline: key exchange, fusion, anomaly scoring, and agility-driven
suite transitions.

Usage:
    python scripts/demo_multi_handshake.py
"""
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["OQS_INSTALL_PATH"] = r"C:\liboqs"

import oqs
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from ai_anomaly_detector import initialize_detector, get_detector, HandshakeMetrics
from agility_controller import initialize_controller, get_controller, AgilityEvent


def fuse(s1, s2):
    return HKDF(algorithm=hashes.SHA3_256(), length=32, salt=None, info=b"hybrid-pqc-v1-fusion").derive(s1 + s2)


def main():
    initialize_detector()
    detector = get_detector()
    detector.load_suite_overhead_ranges()
    detector.set_backend_mode(real=True)

    initialize_controller()
    controller = get_controller()

    session_id = "multi_test"
    session = controller.create_session(session_id, initial_suite="TLS_X25519_ML_KEM_768_WITH_AES_256_GCM_SHA3_256")
    print("=== 3SA Multi-Handshake Agility Demo ===")
    print("Starting suite: %s" % session.current_suite)
    print("Fallback order: %s" % [s.split("TLS_X25519_")[1][:25] for s in controller.get_fallback_order()])
    print("Transition cooldown: %d handshakes" % session.transition_cooldown)
    print()

    for i in range(8):
        start = time.perf_counter()

        alice_priv = x25519.X25519PrivateKey.generate()
        alice_pub = alice_priv.public_key().public_bytes_raw()

        ml_part = session.current_suite.split("_ML_")[1].split("_WITH")[0] if "_ML_" in session.current_suite else None
        kem_name = "ML-" + ml_part.replace("_", "-") if ml_part else None

        if kem_name:
            kem = oqs.KeyEncapsulation(kem_name)
            pq_pub = kem.generate_keypair()
        else:
            pq_pub = None

        bob_priv = x25519.X25519PrivateKey.generate()
        bob_pub = bob_priv.public_key().public_bytes_raw()
        cls_secret_bob = bob_priv.exchange(x25519.X25519PublicKey.from_public_bytes(alice_pub))
        cls_secret_alice = alice_priv.exchange(x25519.X25519PublicKey.from_public_bytes(bob_pub))

        if kem_name:
            ciphertext, pq_secret_bob = kem.encap_secret(pq_pub)
            pq_secret_alice = kem.decap_secret(ciphertext)
            kem.free()
        else:
            ciphertext = b""
            pq_secret_bob = b"\x00" * 32
            pq_secret_alice = b"\x00" * 32

        alice_key = fuse(cls_secret_alice, pq_secret_alice)
        bob_key = fuse(cls_secret_bob, pq_secret_bob)

        elapsed_ms = (time.perf_counter() - start) * 1000
        match = alice_key == bob_key

        metrics = HandshakeMetrics(
            latency_ms=elapsed_ms,
            ciphertext_size=len(ciphertext) if ciphertext else 0,
            public_key_size=len(pq_pub) if pq_pub else 0,
            success=match,
            encap_variance=0.0,
            suite=session.current_suite,
        )
        score = detector.score(metrics)

        event, new_suite = controller.evaluate_agility(session_id, score, match)

        status = "OK"
        transition = ""
        if event != AgilityEvent.NONE and new_suite:
            controller.transition_suite(session_id, session.current_suite, new_suite, event)
            short_old = session.current_suite.split("TLS_X25519_")[1].split("_WITH")[0]
            short_new = new_suite.split("TLS_X25519_")[1].split("_WITH")[0]
            transition = "  >>> RENEGOTIATE: %s -> %s (event: %s)" % (short_old, short_new, event.value)
            status = "AGILITY TRIGGERED"

        short = session.current_suite.split("TLS_X25519_")[1].split("_WITH")[0]
        print("Handshake %d: %6.2fms | score=%.3f | key=%s | suite=%s" % (
            i + 1, elapsed_ms, score, "match" if match else "MISMATCH", short))

        if transition:
            print(transition)
        print("  -> %s" % status)

    print()
    print("=== Session Summary ===")
    print("Final suite: %s" % session.current_suite.split("TLS_X25519_")[1].split("_WITH")[0])
    print("Total handshakes: %d" % session.handshake_count)
    print("Agility events: %d" % len(session.agility_events))
    for e in session.agility_events:
        old = e["old_suite"].split("TLS_X25519_")[1].split("_WITH")[0]
        new = e["new_suite"].split("TLS_X25519_")[1].split("_WITH")[0]
        print("  %s: %s -> %s" % (e["event"], old, new))


if __name__ == "__main__":
    main()
