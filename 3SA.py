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
from handshake_logger import get_handshake_logger
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
    parser.add_argument(
        "--log-file",
        default=None,
        help="Path to a file to write logs to (optional)",
    )
    parser.add_argument(
        "--dataset-output",
        default=None,
        help="Path to CSV file to append handshake data for anomaly detector training",
    )
    return parser.parse_args()


def apply_test_scenario(metrics: HandshakeMetrics, scenario: Optional[str] = None) -> HandshakeMetrics:
    """Mutate handshake metrics to simulate a specific anomaly scenario."""
    if not scenario or scenario == "normal":
        return metrics

    scenario = scenario.lower()
    if scenario == "high_latency":
        metrics.latency_ms = 50.0
        metrics.success = True
    elif scenario == "size_mismatch":
        metrics.ciphertext_size = 1208
        metrics.public_key_size = 1264
        metrics.success = True
    elif scenario == "failure":
        metrics.latency_ms = 45.0
        metrics.success = False
    elif scenario == "repeated_failure":
        metrics.latency_ms = 40.0
        metrics.success = False

    return metrics


def hybrid_fusion_handshake(kem_algorithm: str, force_real: bool = False, session_id: str = "default", web_dashboard: bool = False, test_scenario: Optional[str] = None, dataset_output: Optional[str] = None):
    """Execute hybrid PQC handshake with anomaly detection and agility.
    
    Args:
        kem_algorithm: KEM algorithm to use
        force_real: Force real oqs backend
        session_id: Session identifier for agility tracking
        dataset_output: Optional CSV path to log handshake data for training
    """
    logger = logging.getLogger("3SA")
    print(f"--- Starting Hybrid PQC Handshake (X25519 + {kem_algorithm}) ---\n")

    # Initialize controllers on first run
    detector = get_detector()
    controller = get_controller()
    if not detector.is_trained:
        if not detector.load_model():
            initialize_detector()
    # Load suite overhead ranges for suite-aware anomaly detection
    detector.load_suite_overhead_ranges()
    detector.set_backend_mode(real=force_real)
    
    # Create session in agility controller
    # Convert kem algorithm name to match policy.json format (ML-KEM-768 -> ML_KEM_768)
    kem_policy_name = kem_algorithm.replace("-", "_")
    session = controller.create_session(session_id, initial_suite=f"TLS_X25519_{kem_policy_name}_WITH_AES_256_GCM_SHA3_256")

    # Measure handshake latency
    start_time = time.perf_counter()
    start_time_ns = time.perf_counter_ns()

    # 1. CLIENT (ALICE) GENERATION
    alice_priv_classic = x25519.X25519PrivateKey.generate()
    alice_pub_classic = alice_priv_classic.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    alice_kem = create_kem(kem_algorithm, force_real=force_real)
    alice_kem_keygen_start_ns = time.perf_counter_ns()
    alice_pub_pq = alice_kem.generate_keypair()
    alice_kem_keygen_ns = time.perf_counter_ns() - alice_kem_keygen_start_ns

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
    bob_encap_start_ns = time.perf_counter_ns()
    ciphertext, shared_pq = bob_kem.encapsulate(alice_pub_pq)
    bob_encap_ns = time.perf_counter_ns() - bob_encap_start_ns

    print(f"[Server] Computed Classical Secret: {shared_classic[:16].hex()}...")
    print(f"[Server] Computed PQ Secret: {shared_pq[:16].hex()}...\n")

    # 3. CLIENT (ALICE) DECAPSULATION
    alice_shared_classic = alice_priv_classic.exchange(
        x25519.X25519PublicKey.from_public_bytes(bob_pub_classic)
    )
    alice_decap_start_ns = time.perf_counter_ns()
    alice_shared_pq = alice_kem.decapsulate(ciphertext)
    alice_decap_ns = time.perf_counter_ns() - alice_decap_start_ns

    # 4. THE HYBRID FUSION (HKDF)
    def derive_final_key(classic_sec, pq_sec):
        return HKDF(
            algorithm=hashes.SHA3_256(),
            length=32,
            salt=b"hybrid-pqc-v1-fusion",  # Fixed salt for security/domain separation
            info=b"hybrid-pqc-v1-fusion",  # Domain separation context matching spec
        ).derive(classic_sec + pq_sec)

    hkdf_start_ns = time.perf_counter_ns()
    alice_final_key = derive_final_key(alice_shared_classic, alice_shared_pq)
    bob_final_key = derive_final_key(shared_classic, shared_pq)
    hkdf_ns = time.perf_counter_ns() - hkdf_start_ns

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    elapsed_ns = time.perf_counter_ns() - start_time_ns

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
    rf_raw = detector.raw_score(metrics)
    anomaly_score = detector.score(metrics)
    print(f"\n[AI Monitor] Anomaly Score: {anomaly_score:.3f} (RF raw: {rf_raw:.4f})")

    # 6. PERSIST HANDSHAKE DATA
    hs_logger = get_handshake_logger(dataset_output)
    if hs_logger is not None:
        # Look up suite-specific anomaly threshold from policy for label derivation
        suite_def = controller.get_suite_definition(session.current_suite)
        suite_anomaly_threshold = suite_def.get("anomaly_threshold", 0.6) if suite_def else 0.6

        hs_logger.log_from_metrics(
            metrics,
            anomaly_score,
            suite=session.current_suite,
            test_scenario=test_scenario,
            latency_ns=elapsed_ns,
            anomaly_threshold=suite_anomaly_threshold,
            rf_raw_probability=rf_raw,
        )
        print(f"[Dataset] Logged handshake data -> {hs_logger.csv_path}")

        # Periodically retrain the anomaly detector on accumulated live data
        if dataset_output:
            detector.retrain_from_live_data(dataset_output)

    # Broadcast metrics to web dashboard if enabled
    if web_dashboard:
        metrics_data = {
            'total_latency_ms': metrics.latency_ms,
            'ciphertext_size_bytes': metrics.ciphertext_size,
            'public_key_size_bytes': metrics.public_key_size,
            'success': metrics.success,
            'encap_variance': metrics.encap_variance,
            'alice_kem_keygen_ns': alice_kem_keygen_ns,
            'bob_encap_ns': bob_encap_ns,
            'alice_decap_ns': alice_decap_ns,
            'hkdf_ns': hkdf_ns,
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
    # Always enable file logging. Use CLI arg or env var, else default to 3sa.log
    log_file = args.log_file or os.environ.get("THREE_SA_LOG_FILE") or os.path.join(os.getcwd(), "3sa.log")
    # Ensure parent directory exists if provided
    log_dir = os.path.dirname(log_file)
    if log_dir:
        try:
            os.makedirs(log_dir, exist_ok=True)
        except Exception:
            pass
    handlers = [logging.StreamHandler(), logging.FileHandler(log_file, encoding="utf-8")]
    logging.basicConfig(level=getattr(logging, log_level, logging.INFO), format="[3SA] %(levelname)s: %(message)s", handlers=handlers)
    
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
            dataset_output=args.dataset_output,
        )
    except RuntimeError as exc:
        print(f"Error: {exc}")
        exit(1)