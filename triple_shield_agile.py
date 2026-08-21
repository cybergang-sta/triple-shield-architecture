"""
Triple Shield Architecture: Threat-Adaptive Cryptographic Agility Prototype
Author: Sulemana Wunnam Yussif
Status: Capstone Research Extension / Empirical Evaluation Component
Dependencies: pip install liboqs cryptography scikit-learn pandas
"""

import oqs
import binascii
import logging
import time
import csv
from datetime import datetime
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import x25519, x448
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from dataclasses import dataclass
from typing import Dict, Tuple

# -----------------------------------------------------------------------------
# 1. CONFIGURATION & LOGGING
# -----------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("TripleShield.Agile")

@dataclass
class CryptoSuite:
    name: str
    classical_curve: str
    pq_kem: str

CRYPTO_SUITES = {
    "baseline": CryptoSuite(name="baseline", classical_curve="X25519", pq_kem="ML-KEM-768"),
    "elevated": CryptoSuite(name="elevated", classical_curve="X448", pq_kem="ML-KEM-1024"),
    "hardened": CryptoSuite(name="hardened", classical_curve="X25519", pq_kem="ML-KEM-1024")
}

# CSV log for empirical data collection (research reproducibility)
LOG_FILE = "triple_shield_agility_logs.csv"
with open(LOG_FILE, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["timestamp", "session_id", "threat_score", "selected_suite", "latency_ms", "key_match"])

# -----------------------------------------------------------------------------
# 2. CRYPTOGRAPHIC FACTORIES
# -----------------------------------------------------------------------------
def get_classical_keypair(curve: str):
    if curve == "X25519":
        priv = x25519.X25519PrivateKey.generate()
        return priv, priv.public_key().public_bytes_raw()
    elif curve == "X448":
        priv = x448.X448PrivateKey.generate()
        return priv, priv.public_key().public_bytes_raw()
    raise ValueError(f"Unsupported classical curve: {curve}")

def compute_classical_shared(priv, peer_pub_bytes, curve: str) -> bytes:
    if curve == "X25519":
        return priv.exchange(x25519.X25519PublicKey.from_public_bytes(peer_pub_bytes))
    elif curve == "X448":
        return priv.exchange(x448.X448PublicKey.from_public_bytes(peer_pub_bytes))
    raise ValueError(f"Unsupported classical curve: {curve}")

# -----------------------------------------------------------------------------
# 3. AI/ANOMALY DETECTION MODULE
# -----------------------------------------------------------------------------
def detect_anomalies(metadata: Dict) -> float:
    """
    Simulates threat scoring for research prototyping.
    REPLACE THIS with your trained scikit-learn model:
      model = joblib.load("pqc_anomaly_detector.pkl")
      score = float(model.predict([features])[0])
    """
    latency_norm = min(metadata["latency_ms"] / 200.0, 1.0)
    variance_norm = min(metadata["size_variance"] / 150.0, 1.0)
    # Weighted heuristic for prototype demonstration
    score = 0.6 * latency_norm + 0.4 * variance_norm
    return round(min(max(score, 0.0), 1.0), 3)

def select_suite_from_score(score: float) -> str:
    if score >= 0.75: return "hardened"
    elif score >= 0.45: return "elevated"
    return "baseline"


# 4. CORE HYBRID HANDSHAKE WITH AGILITY
# This function simulates a single handshake session, measuring latency and logging results for research analysis.
def execute_hybrid_handshake(session_id: int, suite_name: str) -> Tuple[bool, float, float]:
    suite = CRYPTO_SUITES[suite_name]
    start = time.perf_counter()

    # CLIENT
    # Note: In a real implementation, Alice would send her public keys to Bob over the network.
    alice_priv, alice_pub_cls = get_classical_keypair(suite.classical_curve)
    alice_kem = oqs.KeyEncapsulation(suite.pq_kem)
    alice_pub_pq = alice_kem.generate_keypair()

    # SERVER 
    #  Bob receives Alice's public keys and responds with his own public key and the encapsulated ciphertext.
    bob_priv, bob_pub_cls = get_classical_keypair(suite.classical_curve)
    shared_cls_bob = compute_classical_shared(bob_priv, alice_pub_cls, suite.classical_curve)
    
    with oqs.KeyEncapsulation(suite.pq_kem) as bob_kem:
        if hasattr(bob_kem, 'encap_secret'):
            ciphertext, shared_pq_bob = bob_kem.encap_secret(alice_pub_pq)
        else:
            ciphertext, shared_pq_bob = bob_kem.encapsulate(alice_pub_pq)

    # CLIENT DECAPSULATION 
    #  Alice uses her private keys to compute the shared secrets and derive the final session key.
    shared_cls_alice = compute_classical_shared(alice_priv, bob_pub_cls, suite.classical_curve)
    if hasattr(alice_kem, 'decap_secret'):
        shared_pq_alice = alice_kem.decap_secret(ciphertext)
    else:
        shared_pq_alice = alice_kem.decapsulate(ciphertext)
    alice_kem.free()

    # HKDF FUSION 
    # Both parties derive the final session key using HKDF on the combined classical and PQ secrets.
    def fuse(secrets: Tuple[bytes, bytes]) -> bytes:
        return HKDF(
            algorithm=hashes.SHA3_256(), length=32, salt=None,
            info=b"hybrid-pqc-v1-fusion"
        ).derive(secrets[0] + secrets[1])

    alice_key = fuse((shared_cls_alice, shared_pq_alice))
    bob_key = fuse((shared_cls_bob, shared_pq_bob))

    latency = (time.perf_counter() - start) * 1000
    match = alice_key == bob_key

    #  LOGGING 
    # For research analysis, we log the session ID, selected suite, latency, and whether the keys matched.
    metadata = {"latency_ms": latency, "size_variance": 42 + int(session_id * 5)}  # Simulated metadata
    threat_score = detect_anomalies(metadata)
    
    with open(LOG_FILE, "a", newline="") as f:
        csv.writer(f).writerow([datetime.now().isoformat(), session_id, threat_score, suite_name, round(latency, 2), match])

    logger.info(f"Session {session_id} | Suite: {suite_name:8} | Latency: {latency:6.2f}ms | Threat: {threat_score:.3f} | Match: {match}")
    return match, threat_score, latency


# 5. RESEARCH DEMO LOOP
#
if __name__ == "__main__":
    print("=== Triple Shield: Threat-Adaptive Crypto Agility Demo ===\n")
    for i in range(1, 6):
        # Simulate escalating threat environment
        simulated_score = min(0.2 + (i * 0.15), 1.0)
        suite = select_suite_from_score(simulated_score)
        execute_hybrid_handshake(i, suite)
    print(f"\n Empirical logs saved to: {LOG_FILE}")