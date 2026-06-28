
# Triple-Shield Architecture (3SA): A Multi-layered Hybrid Quantum-Safe Cryptographic Framework with Crypto Agility

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

## Docker Deployment

### Prerequisites
- Docker Desktop installed on your system
- Docker Compose (included with Docker Desktop)

### Build and Run with Docker

#### Build the Docker image:
```bash
docker build -t 3sa:latest .
```

#### Run the main application:
```bash
docker run --rm 3sa:latest
```

#### Run with specific KEM algorithm:
```bash
docker run --rm 3sa:latest python3 3SA.py --kem ML-KEM-1024
```

#### Run with environment variables:
```bash
docker run --rm -e THREE_SA_LOG=DEBUG 3sa:latest
```

### Using Docker Compose

#### Start all services:
```bash
docker-compose up
```

#### Start specific service:
```bash
docker-compose up 3sa
docker-compose up benchmark
docker-compose up 3sa-1024
docker-compose up 3sa-classical
```

#### Run in detached mode:
```bash
docker-compose up -d
```

#### View logs:
```bash
docker-compose logs -f
```

#### Stop all services:
```bash
docker-compose down
```

### Docker Services

The docker-compose.yml includes multiple services for testing different configurations:

- **3sa**: Main service with ML-KEM-768 (default)
- **benchmark**: Performance benchmarking service
- **3sa-1024**: ML-KEM-1024 variant
- **3sa-classical**: Classical X25519 fallback

### Benefits of Containerization

- **Isolated Environment**: Eliminates background system noise for accurate latency measurements
- **Reproducible Results**: Consistent Python environment and dependencies
- **Easy Deployment**: Single command to run the entire stack
- **Scalability**: Easy to run multiple instances for load testing

---

## Network Emulation for Stress Testing

### Overview

The 3SA framework supports real-world network emulation using Linux tc netem (Traffic Control) within Docker containers. This leverages WSL 2 on Windows to provide native Linux network emulation capabilities without requiring Windows-specific tools.

### Literature-Based Parameters

Based on empirical studies of post-quantum cryptography validation:
- **WAN Latency**: 40ms Round-Trip Time (RTT)
- **Jitter**: ±5ms (normal distribution)
- **Purpose**: Validate AI anomaly detector can differentiate between side-channel attacks and natural network jitter

### Prerequisites

- Docker Desktop with WSL 2 backend (default on Windows)
- Docker Compose
- Network emulator service requires CAP_NET_ADMIN privileges

### Using Network Emulation

#### Start the network emulator service:
```bash
docker-compose up -d network-emulator
```

#### Apply WAN emulation (40ms RTT, ±5ms jitter):
```bash
docker exec -it 3sa-network-emulator sudo /home/app/3sa/scripts/setup_network_emulation.sh
```

#### Run 3SA with network emulation:
```bash
docker-compose up 3sa
```

#### Remove network emulation:
```bash
docker exec -it 3sa-network-emulator sudo /home/app/3sa/scripts/cleanup_network_emulation.sh
```

#### Stop network emulator:
```bash
docker-compose down network-emulator
```

### Manual Network Emulation

If you prefer to run network emulation manually inside a container:

```bash
# Start a container with network capabilities
docker run --rm --cap-add=NET_ADMIN --privileged --network host 3sa:latest

# Inside the container, apply emulation
sudo tc qdisc add dev eth0 root netem delay 40ms 5ms distribution normal

# Run your tests
python3 3SA.py --kem ML-KEM-768

# Clean up
sudo tc qdisc del dev eth0 root
```

### Verification

To verify network emulation is active:
```bash
docker exec -it 3sa-network-emulator tc qdisc show dev eth0
```

Expected output:
```
qdisc netem 1: root refcnt 2 limit 1000 delay 40ms 5ms
```

### Benefits of Network Emulation

- **Realistic Testing**: Validates AI detector under WAN conditions
- **Side-Channel Detection**: Ensures cryptographic processing time isolation from network latency
- **Literature Alignment**: Uses exact parameters from PQC validation studies
- **WSL 2 Integration**: Native Linux networking on Windows without additional tools

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
