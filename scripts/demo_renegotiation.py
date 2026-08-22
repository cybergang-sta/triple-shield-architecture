"""Forced renegotiation demo: injects anomaly spike to trigger suite transition.

Runs 10 handshakes with artificial anomaly injection on handshakes 5 and 6
to demonstrate the agility controller's suite renegotiation mechanism.
Shows ML-KEM-768 transitioning to ML-KEM-1024 under anomaly pressure.

Usage:
    python scripts/demo_renegotiation.py
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


SUITE_SHORT = {
    "ML_KEM_768_WITH_AES_256_GCM_SHA3_256": "ML-KEM-768",
    "ML_KEM_1024_WITH_AES_256_GCM_SHA3_256": "ML-KEM-1024",
    "WITH_AES_256_GCM_SHA3_256": "Classical-only",
}


def short_suite(full):
    key = full.split("TLS_X25519_")[1]
    return SUITE_SHORT.get(key, key[:20])


def main():
    initialize_detector()
    detector = get_detector()
    detector.load_suite_overhead_ranges()
    detector.set_backend_mode(real=True)

    initialize_controller()
    controller = get_controller()

    session_id = "agility_demo"
    session = controller.create_session(session_id, initial_suite="TLS_X25519_ML_KEM_768_WITH_AES_256_GCM_SHA3_256")

    print("=" * 70)
    print("3SA CRYPTOGRAPHIC AGILITY DEMO")
    print("=" * 70)
    print("  Starting suite : ML-KEM-768 (NIST Level 3)")
    print("  Fallback order : ML-KEM-768 -> ML-KEM-1024 -> Classical")
    print("  Cooldown       : %d handshakes between transitions" % session.transition_cooldown)
    print("  Anomaly thresh : 0.6 (score > 0.6 triggers renegotiation)")
    print("=" * 70)
    print()

    for i in range(10):
        start = time.perf_counter()

        ml_part = session.current_suite.split("_ML_")[1].split("_WITH")[0] if "_ML_" in session.current_suite else None
        kem_name = "ML-" + ml_part.replace("_", "-") if ml_part else None

        alice_priv = x25519.X25519PrivateKey.generate()
        alice_pub = alice_priv.public_key().public_bytes_raw()

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

        injected = False
        if i in (4, 5):
            score = 0.85
            injected = True

        event, new_suite = controller.evaluate_agility(session_id, score, match)

        tag = ""
        transition_line = ""
        if event != AgilityEvent.NONE and new_suite:
            controller.transition_suite(session_id, session.current_suite, new_suite, event)
            old_s = short_suite(session.current_suite)
            new_s = short_suite(new_suite)
            transition_line = "     *** SUITE RENEGOTIATED: %s -> %s (%s) ***" % (old_s, new_s, event.value)
            tag = "RENEGOTIATED"

        suite_str = short_suite(session.current_suite)
        print("  [%2d] %6.2fms  score=%.3f  key=%s  suite=%-14s  %s" % (
            i + 1, elapsed_ms, score, "OK" if match else "FAIL", suite_str,
            "INJECTED ANOMALY" if injected else ""))
        if transition_line:
            print(transition_line)
        print()

    print("=" * 70)
    print("SESSION SUMMARY")
    print("=" * 70)
    print("  Final suite      : %s" % short_suite(session.current_suite))
    print("  Total handshakes : %d" % session.handshake_count)
    print("  Agility events   : %d" % len(session.agility_events))
    for e in session.agility_events:
        print("    [%s]  %s -> %s" % (e["event"], short_suite(e["old_suite"]), short_suite(e["new_suite"])))
    print("=" * 70)


if __name__ == "__main__":
    main()
