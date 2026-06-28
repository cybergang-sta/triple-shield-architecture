"""Middleware wrapper for liboqs / oqs usage.

This module provides a thin wrapper around the Python `oqs` package and
falls back to a local mock implementation when `oqs` is unavailable.
It centralizes KEM creation and provides a consistent interface for
calling code.
"""

import hashlib
import json
import logging
import os
from typing import Tuple, List, Optional

try:
    import oqs
    _OQS_AVAILABLE = True
except ImportError:
    oqs = None
    _OQS_AVAILABLE = False


class OqsKEM:
    def __init__(self, algorithm: str = "ML-KEM-768", force_mock: bool = False, force_real: bool = False):
        self.algorithm = algorithm
        self._force_real = force_real
        self._force_mock = force_mock or (force_real and not _OQS_AVAILABLE)
        if self._force_real and not _OQS_AVAILABLE:
            raise RuntimeError("Cannot force real oqs backend: oqs package not installed")
        self._use_mock = self._force_mock or not _OQS_AVAILABLE
        if self._use_mock:
            self._backend = _MockKEM(algorithm)
        else:
            self._backend = oqs.KeyEncapsulation(algorithm)
        # Log backend details
        try:
            if self.is_real:
                oqs_version = getattr(oqs, "__version__", "<unknown>")
                _LOGGER.info("Using real oqs backend: %s (version=%s)", algorithm, oqs_version)
            else:
                _LOGGER.info("Using mock oqs backend: %s", algorithm)
        except Exception:
            _LOGGER.debug("Unable to log backend version info")

    def generate_keypair(self) -> bytes:
        return self._backend.generate_keypair()

    def encapsulate(self, peer_public: bytes) -> Tuple[bytes, bytes]:
        return self._backend.encapsulate(peer_public)

    def decapsulate(self, ciphertext: bytes) -> bytes:
        return self._backend.decapsulate(ciphertext)

    @property
    def is_real(self) -> bool:
        return not self._use_mock and _OQS_AVAILABLE

    def info(self) -> str:
        backend = "oqs" if self.is_real else "mock"
        return f"{backend} KEM({self.algorithm})"


class _MockKEM:
    """Minimal insecure KEM mock for local testing only."""

    def __init__(self, algorithm: str):
        self.algorithm = algorithm
        self._priv = os.urandom(32)
        # Generate exact sizes based on literature specifications
        if "1024" in algorithm:
            self._pk_size = 1568  # ML-KEM-1024: exact 1568 bytes (public key)
            self._ct_size = 1568  # ML-KEM-1024: exact 1568 bytes (ciphertext)
        elif "768" in algorithm:
            self._pk_size = 1184  # ML-KEM-768: exact 1184 bytes (public key)
            self._ct_size = 1088  # ML-KEM-768: exact 1088 bytes (ciphertext)
        else:
            self._pk_size = 32  # Classical X25519: exact 32 bytes
            self._ct_size = 32  # Classical fallback
        # Generate deterministic public key of exact size
        self._pub = hashlib.sha3_256(self._priv).digest()
        # Extend to required size by repeating the hash
        while len(self._pub) < self._pk_size:
            self._pub += hashlib.sha3_256(self._pub).digest()
        self._pub = self._pub[:self._pk_size]

    def generate_keypair(self) -> bytes:
        # Return deterministic realistic-sized public key for testing
        return self._pub

    def encapsulate(self, peer_public: bytes) -> Tuple[bytes, bytes]:
        # Generate deterministic ciphertext of correct size
        ephemeral = hashlib.sha3_256(peer_public + self._priv).digest()
        while len(ephemeral) < self._ct_size:
            ephemeral += hashlib.sha3_256(ephemeral).digest()
        ephemeral = ephemeral[:self._ct_size]
        shared = hashlib.sha3_256(peer_public + ephemeral).digest()
        return ephemeral, shared

    def decapsulate(self, ciphertext: bytes) -> bytes:
        return hashlib.sha3_256(self._pub + ciphertext).digest()


def create_kem(algorithm: str = "ML-KEM-768", force_mock: bool = False, force_real: bool = False) -> OqsKEM:
    """Create a KEM instance with the requested algorithm."""
    return OqsKEM(algorithm, force_mock=force_mock, force_real=force_real)


def oqs_available() -> bool:
    return _OQS_AVAILABLE


def supported_kems() -> list[str]:
    if _OQS_AVAILABLE:
        try:
            return list(oqs.get_enabled_KEMs())
        except AttributeError:
            return []
    return []


# Policy loading and negotiation helpers
_POLICY_PATH = os.path.join(os.path.dirname(__file__), "policy.json")
_POLICY = {}
try:
    with open(_POLICY_PATH, "r", encoding="utf-8") as f:
        _POLICY = json.load(f)
except Exception:
    _POLICY = {}

_LOGGER = logging.getLogger("oqs_middleware")
if not _LOGGER.handlers:
    # basic config for library-style logging
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[oqs_middleware] %(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    _LOGGER.addHandler(handler)
    _LOGGER.setLevel(logging.INFO)


def get_policy() -> dict:
    return _POLICY.copy()


def select_kem(client_preference: Optional[List[str]] = None, server_supported: Optional[List[str]] = None) -> Optional[str]:
    """Select a KEM algorithm given client preference list and server-supported list.

    Selection order:
    1. If client_preference contains algorithm that server supports and appears in policy fallback_order, pick first matching.
    2. Else choose first algorithm from policy.fallback_order that is supported by server.
    3. Else return None.
    """
    policy = get_policy()
    fallback = policy.get("fallback_order", [])
    server = server_supported or supported_kems() or fallback
    client = client_preference or []

    _LOGGER.debug("Negotiation: client=%s server=%s fallback=%s", client, server, fallback)

    # try client preference first
    for alg in client:
        if alg in server:
            _LOGGER.info("Negotiation result: selected %s from client preference", alg)
            return alg

    # then try policy fallback order
    for alg in fallback:
        if alg in server:
            _LOGGER.info("Negotiation result: selected %s from policy fallback", alg)
            return alg

    # as a last resort pick first server-supported
    if server:
        _LOGGER.info("Negotiation fallback: selected first available %s", server[0])
        return server[0]

    _LOGGER.warning("No KEM algorithms available for negotiation")
    return None


def available_kems_for_env() -> List[str]:
    """Return a list of available KEMs; if oqs is not present fall back to policy list."""
    kems = supported_kems()
    if kems:
        return kems
    # fallback to policy list as mock
    return _POLICY.get("fallback_order", [])
