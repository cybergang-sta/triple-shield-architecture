#!/usr/bin/env python3
"""
Backend verification script to confirm liboqs is being used correctly.
"""

import logging
from oqs_middleware import OqsKEM, oqs_available, supported_kems

logging.basicConfig(level=logging.INFO, format="[verify] %(levelname)s: %(message)s")
_LOGGER = logging.getLogger("verify")

def main():
    _LOGGER.info("=== liboqs Backend Verification ===")
    
    # Check if liboqs is available
    if oqs_available():
        _LOGGER.info("liboqs package is installed and available")
    else:
        _LOGGER.error("liboqs package is NOT installed - using mock backend")
        return False
    
    # List supported KEMs
    kems = supported_kems()
    _LOGGER.info(f"Supported KEM algorithms: {len(kems)}")
    
    # Check for ML-KEM algorithms
    ml_kem_algs = [k for k in kems if "ML-KEM" in k or "Kyber" in k]
    if ml_kem_algs:
        _LOGGER.info(f"ML-KEM algorithms available: {ml_kem_algs[:5]}...")  # Show first 5
    else:
        _LOGGER.warning("No ML-KEM algorithms found in supported list")
    
    # Test real backend with force_real=True
    _LOGGER.info("\n=== Testing Real Backend ===")
    try:
        kem = OqsKEM(algorithm="ML-KEM-768", force_real=True)
        if kem.is_real:
            _LOGGER.info(f"SUCCESS: Using real liboqs backend for {kem.info()}")
            
            # Test key generation
            _LOGGER.info("Testing key generation...")
            pk = kem.generate_keypair()
            _LOGGER.info(f"Public key size: {len(pk)} bytes")
            
            # Test encapsulation
            _LOGGER.info("Testing encapsulation...")
            ct, shared = kem.encapsulate(pk)
            _LOGGER.info(f"Ciphertext size: {len(ct)} bytes")
            _LOGGER.info(f"Shared secret size: {len(shared)} bytes")
            
            # Test decapsulation
            _LOGGER.info("Testing decapsulation...")
            shared2 = kem.decapsulate(ct)
            _LOGGER.info(f"Decapsulated shared secret size: {len(shared2)} bytes")
            
            if shared == shared2:
                _LOGGER.info("SUCCESS: Shared secrets match")
            else:
                _LOGGER.error("ERROR: Shared secrets do not match")
                return False
            
            _LOGGER.info("\n=== All Tests Passed ===")
            _LOGGER.info("liboqs is correctly installed and functional")
            return True
        else:
            _LOGGER.error("ERROR: force_real=True but backend is still mock")
            return False
    except Exception as e:
        _LOGGER.error(f"ERROR: Failed to create real KEM: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
