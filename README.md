# Triple-Shield Architecture (3SA)

A demonstration of a **hybrid post-quantum cryptography (PQC) handshake** combining classical elliptic-curve cryptography (X25519) with post-quantum key encapsulation (ML-KEM-768), fused using HKDF for a unified session key.

## Overview

**3SA.py** implements a simplified handshake protocol between two parties (Alice and Bob):

1. **Alice (Client)** generates X25519 and ML-KEM-768 keypairs and sends public keys to Bob.
2. **Bob (Server)** performs ECDH key exchange with Alice's X25519 public key and KEM encapsulation with her ML-KEM-768 public key.
3. Both parties derive the same session key by combining classical and post-quantum secrets using HKDF.

**Key insight:** By mixing two independent cryptographic primitives, the handshake resists attacks on either classical or post-quantum algorithms individually.

---

## Setup & Installation

### Prerequisites
- **Python 3.10+** (tested on Python 3.13)
- **cryptography** library (for X25519 and HKDF)

### Install Dependencies

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install cryptography
```

---

## Running the Script

### Using the `.venv` virtual environment (recommended):

```powershell
& "c:\Users\WUNNAM\Triple-Shield Architecture\.venv\Scripts\python.exe" "3SA.py"
```

### Using system Python:

```bash
python 3SA.py
```

### Middleware / CLI Usage

```bash
python 3SA.py --list-kems
python 3SA.py --kem ML-KEM-768
python 3SA.py --force-real
python 3SA.py --kem KYBER512 --force-real
```

Use `--list-kems` to see available oqs algorithms. By default, the wrapper falls back to the mock backend when `oqs` is not installed. Use `--force-real` to require the real `oqs` backend.

### Expected Output

```
--- Starting Hybrid PQC Handshake (X25519 + ML-KEM-768) ---

[Client] Sent X25519 Public Key: b27f30460f6c390d5a45d7106a3e4cdf...
[Client] Sent ML-KEM-768 Public Key: a155179d59aca9f349c5c8bf3237adbc...

[Server] Computed Classical Secret: 18a3d73035042cde4ba08de322497ea4...
[Server] Computed PQ Secret: f8c1262dfe405d68d7e49993e3b69e83...

Final Session Key (Alice): f89e396eefd7b040a7cf836c4a182fcead5b929ce82f61875bcee90ef6301c29
Final Session Key (Bob):   f89e396eefd7b040a7cf836c4a182fcead5b929ce82f61875bcee90ef6301c29

Result: SUCCESS. Hybrid keys match and are ready for AES-GCM.
```

---

## How It Works

### Classical Path (X25519 ECDH)
- Alice generates an X25519 private key and sends the public key to Bob.
- Bob generates his own X25519 keypair and performs key exchange with Alice's public key.
- Alice performs key exchange with Bob's public key.
- Both derive a 32-byte classical secret via ECDH.

### Post-Quantum Path (ML-KEM-768)
The script includes a **fallback mock KEM** when `pyoqs` is unavailable:
- Alice generates a mock KEM keypair and sends the public key to Bob.
- Bob encapsulates a shared secret using Alice's PQ public key, receiving:
  - A **ciphertext** (ephemeral random bytes)
  - A **shared secret** (derived from Alice's public key and ephemeral)
- Alice decapsulates the ciphertext to recover the same shared secret.

**Note:** The fallback mock is **insecure by design** and intended only for testing the protocol flow locally. It uses SHA3-256 deterministically and has no actual security properties.

### Key Fusion (HKDF)
- Classical and PQ secrets are concatenated: `classical_secret || pq_secret`
- HKDF-Expand with SHA3-256 derives a final 32-byte session key
- Salt and info parameters provide domain separation

```python
final_key = HKDF(
    algorithm=hashes.SHA3_256(),
    length=32,
    salt=b"hybrid-pqc-handshake-v1",
    info=b"session-key-derivation",
).derive(classical_secret + pq_secret)
```

---

## Using Real liboqs (Optional)

To replace the fallback mock with the real **Open Quantum Safe liboqs** library:

### Option A: Build from Source (Advanced)
1. Clone [liboqs](https://github.com/open-quantum-safe/liboqs)
2. Build the C library on Windows (requires CMake, MSVC)
3. Install Python bindings: `pip install liboqs-python`
4. Remove the fallback code from `3SA.py` (lines 1–38)

### Option B: Use Docker
```bash
docker run -it openquantumsafe/liboqs:latest
# Inside container: pip install liboqs-python
```

### Option C: Pre-built Binaries
Check the [Open Quantum Safe project](https://openquantumsafe.org/) for pre-built Windows binaries.

---

## Code Changes Made

1. **Serialization fix**: X25519 public key export now uses `public_bytes(encoding=..., format=...)` instead of the non-existent `public_bytes_raw()`.
2. **Hex output**: Changed from `binascii.hexlify()` (returns bytes) to `.hex()` for cleaner string output.
3. **Fallback KEM**: Added a mock `oqs.KeyEncapsulation` class for local testing when `pyoqs` is unavailable.

---

## Security Notes

**This is a demonstration, not production-ready code:**
- The fallback KEM mock is deterministic and insecure.
- No authentication or signatures are used.
- Session keys are not persisted or used for encryption in this demo.
- For production, use the real `liboqs` library and add proper error handling, input validation, and protocol constraints.

---

## References

- [Open Quantum Safe Project](https://openquantumsafe.org/)
- [NIST PQC Standardization](https://csrc.nist.gov/projects/post-quantum-cryptography/)
- [RFC 3610: HKDF](https://tools.ietf.org/html/rfc3610)
- [Cryptography Library Docs](https://cryptography.io/)

---

## License

Educational use only. Adapt as needed for your research or learning.
