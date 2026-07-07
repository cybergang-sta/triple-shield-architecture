import argparse
import os
import time
import logging
from typing import Optional
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import serialization
from oqs_middleware import create_kem, oqs_available, supported_kems
from ai_anomaly_detector import get_detector, initialize_detector, HandshakeMetrics
from agility_controller import get_controller, initialize_controller, AgilityEvent
import binascii
import requests

def broadcast_metrics(metrics_data, anomaly_score, suite):
    """Broadcast metrics to web dashboard if available"""
    try:
        response = requests.post(
            'http://localhost:5000/api/metrics',
            json={
                **metrics_data,
                'anomaly_score': anomaly_score,
                'suite': suite
            },
            timeout=0.1
        )
    except (requests.exceptions.RequestException, Exception):
        # Silently fail if web server is not running
        pass

def parse_args():
    parser = argparse.ArgumentParser(description="Hybrid PQC handshake demo")
    parser.add_argument(     "--kem",
        default="ML-KEM-768",
        help="KEM algorithm to use (default: ML-KEM-768)",
    )
    parser.add_argument(     "--client-proposals",
        default=None,
        help="Comma-separated client-preferred KEM algorithms for negotiation",
    )
    parser.add_argument(
        "--force-real",
        action="store_true",
        help="Force use of the real oqs backend and fail if not installed",
    )
    parser.add_argument(
        "--list-kems",
        action="store_true",
        help="List enabled oqs KEM algorithms and exit",
    )
    parser.add_argument(
        "--web-dashboard",
        action="store_true",
        help="Enable real-time metrics broadcasting to web dashboard",
    )
    parser.add_argument(
        "--test-scenario",
        choices=["normal", "high_latency", "size_mismatch", "failure", "repeated_failure"],
        default=None,
        help="Inject a synthetic anomaly scenario into the handshake for dashboard testing",
    )
    parser.add_argument(
        "--session-id",
        default="default",
        help="Session identifier used for agility tracking and repeated-failure tests",
    )
    return parser.parse_args()


def apply_test_scenario(metrics: HandshakeMetrics, scenario: Optional[str] = None) -> HandshakeMetrics:
    """Mutate handshake metrics to simulate a specific anomaly scenario."""
    if not scenario or scenario == "normal":
        return metrics

    scenario = scenario.lower()
    if scenario == "high_latency":
        metrics.latency_ms = 18.5
        metrics.success = True
    elif scenario == "size_mismatch":
        metrics.ciphertext_size = 1208
        metrics.public_key_size = 1264
        metrics.success = True
    elif scenario == "failure":
        metrics.latency_ms = 22.0
        metrics.success = False
    elif scenario == "repeated_failure":
        metrics.latency_ms = 20.0
        metrics.success = False

    return metrics


def hybrid_fusion_handshake(kem_algorithm: str, force_real: bool = False, session_id: str = "default", web_dashboard: bool = False, test_scenario: Optional[str] = None):
    """Execute hybrid PQC handshake with anomaly detection and agility.
    
    Args:
        kem_algorithm: KEM algorithm to use
        force_real: Force real oqs backend
        session_id: Session identifier for agility tracking
    """
    logger = logging.getLogger("3SA")
    print(f"--- Starting Hybrid PQC Handshake (X25519 + {kem_algorithm}) ---\n")

    # Initialize controllers on first run
    detector = get_detector()
    controller = get_controller()
    if not detector.is_trained:
        initialize_detector()
    # Load suite overhead ranges for suite-aware anomaly detection
    detector.load_suite_overhead_ranges()
    
    # Create session in agility controller
    # Convert kem algorithm name to match policy.json format (ML-KEM-768 -> ML_KEM_768)
    kem_policy_name = kem_algorithm.replace("-", "_")
    session = controller.create_session(session_id, initial_suite=f"TLS_X25519_{kem_policy_name}_WITH_AES_256_GCM_SHA3_256")

    # Measure handshake latency
    start_time = time.perf_counter()

    # 1. CLIENT (ALICE) GENERATION
    alice_priv_classic = x25519.X25519PrivateKey.generate()
    alice_pub_classic = alice_priv_classic.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    alice_kem = create_kem(kem_algorithm, force_real=force_real)
    alice_pub_pq = alice_kem.generate_keypair()

    print(f"[Client] Selected KEM: {alice_kem.info()}")
    print(f"[Client] Sent X25519 Public Key: {alice_pub_classic[:16].hex()}...")
    print(f"[Client] Sent ML-KEM-768 Public Key: {alice_pub_pq[:16].hex()}...\n")

    # 2. SERVER (BOB) ENCAPSULATION
    bob_priv_classic = x25519.X25519PrivateKey.generate()
    bob_pub_classic = bob_priv_classic.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    peer_pub_alice = x25519.X25519PublicKey.from_public_bytes(alice_pub_classic)
    shared_classic = bob_priv_classic.exchange(peer_pub_alice)

    bob_kem = create_kem(kem_algorithm, force_real=force_real)
    ciphertext, shared_pq = bob_kem.encapsulate(alice_pub_pq)

    print(f"[Server] Computed Classical Secret: {shared_classic[:16].hex()}...")
    print(f"[Server] Computed PQ Secret: {shared_pq[:16].hex()}...\n")

    # 3. CLIENT (ALICE) DECAPSULATION
    alice_shared_classic = alice_priv_classic.exchange(
        x25519.X25519PublicKey.from_public_bytes(bob_pub_classic)
    )
    alice_shared_pq = alice_kem.decapsulate(ciphertext)

    # 4. THE HYBRID FUSION (HKDF)
    def derive_final_key(classic_sec, pq_sec):
        return HKDF(
            algorithm=hashes.SHA3_256(),
            length=32,
            salt=b"hybrid-pqc-v1-fusion",  # Fixed salt for security/domain separation
            info=b"hybrid-pqc-v1-fusion",  # Domain separation context matching spec
        ).derive(classic_sec + pq_sec)

    alice_final_key = derive_final_key(alice_shared_classic, alice_shared_pq)
    bob_final_key = derive_final_key(shared_classic, shared_pq)

    elapsed_ms = (time.perf_counter() - start_time) * 1000

    print(f"Final Session Key (Alice): {alice_final_key.hex()}")
    print(f"Final Session Key (Bob):   {bob_final_key.hex()}")
    
    success = alice_final_key == bob_final_key
    if success:
        print("\nResult: SUCCESS. Hybrid keys match and are ready for AES-GCM.")
    else:
        print("\nResult: FAILURE. Keys do not match.")

    # 5. ANOMALY DETECTION
    metrics = HandshakeMetrics(
        latency_ms=elapsed_ms,
        ciphertext_size=len(ciphertext),
        public_key_size=len(alice_pub_pq),
        success=success,
        encap_variance=0.0,
        suite=session.current_suite,
    )
    metrics = apply_test_scenario(metrics, test_scenario)
    anomaly_score = detector.score(metrics)
    print(f"\n[AI Monitor] Anomaly Score: {anomaly_score:.3f}")

    # Broadcast metrics to web dashboard if enabled
    if web_dashboard:
        metrics_data = {
            'total_latency_ms': metrics.latency_ms,
            'ciphertext_size_bytes': metrics.ciphertext_size,
            'public_key_size_bytes': metrics.public_key_size,
            'success': metrics.success,
            'encap_variance': metrics.encap_variance,
        }
        broadcast_metrics(metrics_data, anomaly_score, session.current_suite)

    # 6. CRYPTOGRAPHIC AGILITY EVALUATION
    event, new_suite = controller.evaluate_agility(session_id, anomaly_score, success)
    if event != AgilityEvent.NONE and new_suite:
        print(f"[Agility] Event triggered: {event.value}")
        print(f"[Agility] Transitioning from {session.current_suite} to {new_suite}")
        controller.transition_suite(session_id, session.current_suite, new_suite, event)
        print(f"[Agility] Session re-negotiation queued for next connection")
        
        # Broadcast agility event to dashboard
        if web_dashboard:
            agility_data = {
                'event_type': 'agility_transition',
                'trigger_event': event.value,
                'old_suite': session.current_suite,
                'new_suite': new_suite,
                'anomaly_score': anomaly_score,
                'timestamp': time.time()
            }
            try:
                requests.post(
                    'http://localhost:5000/api/agility',
                    json=agility_data,
                    timeout=0.1
                )
            except (requests.exceptions.RequestException, Exception):
                pass
    
    # Log session state
    final_state = controller.get_session_state(session_id)
    logger.debug(f"Session state: {final_state}")

if __name__ == "__main__":
    args = parse_args()
    # Configure logging level via environment or default
    import logging
    log_level = os.environ.get("THREE_SA_LOG", "INFO").upper()
    logging.basicConfig(level=getattr(logging, log_level, logging.INFO), format="[3SA] %(levelname)s: %(message)s")
    
    if args.list_kems:
        if oqs_available():
            print("Enabled oqs KEMs:")
            for kem in supported_kems():
                print(f"- {kem}")
        else:
            print("oqs is not available in this environment.")
        exit(0)
    # Negotiation: if client proposals provided, perform simple client/server negotiation
    client_proposals = None
    if args.client_proposals:
        client_proposals = [c.strip() for c in args.client_proposals.split(",") if c.strip()]

    # If user requested explicit negotiate via kem value
    chosen_kem = args.kem
    if args.kem == "negotiate" or client_proposals:
        from oqs_middleware import select_kem, available_kems_for_env
        server_supported = available_kems_for_env()
        chosen_kem = select_kem(client_preference=client_proposals, server_supported=server_supported)
        if not chosen_kem:
            print("Error: no common KEM could be negotiated")
            exit(1)

    try:
        hybrid_fusion_handshake(
            chosen_kem,
            force_real=args.force_real,
            web_dashboard=args.web_dashboard,
            session_id=args.session_id,
            test_scenario=args.test_scenario,
        )
    except RuntimeError as exc:
        print(f"Error: {exc}")
        exit(1)