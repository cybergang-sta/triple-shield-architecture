
# Triple-Shield Architecture (3SA): An Intelligent Hybrid Post-Quantum Key Exchange Protocol with Crypto Agility

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
- **C compiler** (for building liboqs from source)
  - **Windows**: MSVC Build Tools (Visual Studio 2022). Install via [Visual Studio Installer](https://visualstudio.microsoft.com/visual-cpp-build-tools/) — select the "Desktop development with C++" workload.
  - **Linux**: `sudo apt-get install -y build-essential cmake ninja-build`
  - **macOS**: Xcode Command Line Tools (`xcode-select --install`)
- **CMake 3.15+**
- **Git**

### liboqs Backend

The project ships with a **mock KEM backend** for development and testing. The mock provides:

- **Exact byte sizes** from PQC literature:
  - ML-KEM-768: 1184 bytes public key, 1088 bytes ciphertext
  - ML-KEM-1024: 1568 bytes public key, 1568 bytes ciphertext
  - Classical X25519: 32 bytes public key, 32 bytes ciphertext
- **Deterministic output** for reproducible AI training
- **Literature-based parameters** for rigorous validation

The `oqs_middleware.py` module automatically detects if the real `oqs` module is importable and falls back to the mock implementation when it is not. Use `--force-real` on the CLI to require the real backend (raises `RuntimeError` if unavailable).

### Install Dependencies

```bash
pip install -r requirements.txt
```

This installs `liboqs-python` from PyPI along with the other project dependencies.

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
python 3SA.py --web-dashboard  # Enable real-time metrics to web dashboard
```

Use `--list-kems` to see available oqs algorithms. By default, the wrapper falls back to the mock backend when `liboqs-python` is not installed or `oqs.dll`/`liboqs.so` is not on the library path. Use `--force-real` to require the real `oqs` backend (raises an error if unavailable).

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
The script includes a **fallback mock KEM** when `liboqs-python` is unavailable:
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

## Using Real liboqs

The project defaults to the mock backend. To use the real **Open Quantum Safe liboqs** library for production-grade KEM operations:

### Windows (MSVC)

**1. Install MSVC Build Tools** (if not already installed):

Download the [Build Tools for Visual Studio](https://visualstudio.microsoft.com/visual-cpp-build-tools/) and select the **"Desktop development with C++"** workload during installation.

**2. Build liboqs from source**:

Open a **Developer Command Prompt for VS** (or a terminal where `vcvarsall.bat` has been sourced):

```powershell
git clone --depth=1 https://github.com/open-quantum-safe/liboqs C:\liboqs-src
cd C:\liboqs-src
cmake -S . -B build -G Ninja -DBUILD_SHARED_LIBS=ON -DCMAKE_WINDOWS_EXPORT_ALL_SYMBOLS=TRUE -DCMAKE_INSTALL_PREFIX=C:\liboqs
cmake --build build --parallel 8
cmake --install build
```

**3. Add `oqs.dll` to PATH**:

```powershell
# Current session
$env:PATH = "C:\liboqs\bin;$env:PATH"

# Persist for future sessions (User PATH)
$currentPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
[System.Environment]::SetEnvironmentVariable("Path", "C:\liboqs\bin;$currentPath", "User")
[System.Environment]::SetEnvironmentVariable("OQS_INSTALL_PATH", "C:\liboqs", "User")
```

**4. Install Python bindings**:

```bash
pip install liboqs-python
```

### Linux / macOS

```bash
# Install build dependencies
sudo apt-get install -y cmake ninja-build libssl-dev git   # Debian/Ubuntu
# brew install cmake ninja openssl                           # macOS

# Build and install liboqs
git clone --depth=1 https://github.com/open-quantum-safe/liboqs
cmake -S liboqs -B liboqs/build -DBUILD_SHARED_LIBS=ON
cmake --build liboqs/build --parallel $(nproc)
sudo cmake --build liboqs/build --target install
sudo ldconfig                                              # Linux only

# Set library path (if needed)
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib    # Linux
# export DYLD_LIBRARY_PATH=$DYLD_LIBRARY_PATH:/usr/local/lib  # macOS

# Install Python bindings
pip install liboqs-python
```

### Verify the Installation

```bash
python 3SA.py --list-kems
```

If the real backend is installed, this prints all enabled KEM algorithms (e.g., `ML-KEM-768`, `ML-KEM-1024`, `Kyber768`, ...). If not, it reports "oqs is not available" and the mock backend is used.

```bash
python 3SA.py --kem ML-KEM-768 --force-real
```

`--force-real` forces the real `oqs` backend and raises `RuntimeError` if the library is not importable.

### Docker

```bash
docker run -it openquantumsafe/liboqs:latest
# Inside container: pip install liboqs-python
```

---

## Real-time Web Dashboard

The project includes a React-based real-time dashboard for visualizing the 3SA process.

### Features

- **Real-time Metrics**: Live updates of handshake latency, key sizes, and anomaly scores
- **Throughput Visualization**: Line charts showing handshake throughput over time
- **Overhead Comparison**: Bar charts comparing key sizes across cipher suites
- **Process Flow**: Visual representation of handshake steps with timing
- **Anomaly Alerts**: Real-time alerts when anomalies are detected

### Quick Start

1. **Start the WebSocket server**:
```bash
python web_server.py
```

2. **Start the React dashboard** (in a separate terminal):
```bash
cd web
npm install
npm start
```

3. **Run 3SA with dashboard integration**:
```bash
python 3SA.py --kem ML-KEM-768 --web-dashboard
```

The dashboard will be available at `http://localhost:3000`

### Detailed Setup

See [web/README.md](web/README.md) for complete setup instructions, customization options, and troubleshooting.

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

#### Apply WAN emulation on WSL 2 host (recommended for Windows):
```bash
# Open WSL 2 terminal
wsl

# Apply 40ms RTT with ±5ms jitter
sudo tc qdisc add dev eth0 root netem delay 40ms 5ms distribution normal

# Verify emulation
tc qdisc show dev eth0
```

#### Run 3SA with network emulation:
```bash
docker-compose up 3sa
```

#### Remove network emulation:
```bash
sudo tc qdisc del dev eth0 root
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

## Dataset Generation for AI Anomaly Detector

### Overview

The 3SA framework includes a high-resolution dataset generation script for training the AI anomaly detector. The script generates synthetic handshake data based on literature parameters for post-quantum cryptography validation.

### Literature-Based Parameters

The dataset generation uses exact byte sizes and timing parameters from PQC literature:
- **ML-KEM-768**: 1184 bytes public key, 1088 bytes ciphertext, 0.5-0.7ms latency
- **ML-KEM-1024**: 1568 bytes public key, 1568 bytes ciphertext, 0.5-0.7ms latency
- **Classical**: 32 bytes public key, 32 bytes ciphertext, 0.1-0.5ms latency

### Generating the Dataset

#### Run the dataset generation script:
```bash
python generate_dataset.py
```

This will create:
- `datasets/handshake_dataset.csv` - Training data with labels
- `datasets/dataset_statistics.json` - Dataset statistics

### Dataset Composition

The generated dataset includes:
- **Normal handshakes** (72.8%): Within expected size and latency parameters
- **Timing anomalies**: Latency exceeding literature thresholds (side-channel attacks)
- **Size anomalies**: Ciphertext or public key tampering
- **Implicit rejections**: Silent failures from ciphertext manipulation

### Training the AI Anomaly Detector

#### Train with the generated dataset:
```python
from ai_anomaly_detector import AnomalyDetector

detector = AnomalyDetector()
detector.load_suite_overhead_ranges()
detector.train(csv_path="datasets/handshake_dataset.csv")
```

#### Test the trained detector:
```bash
python test_dataset_training.py
```

### Dataset Features

Each sample includes:
- `latency_ms` - Handshake latency in milliseconds
- `latency_ns` - Handshake latency in nanoseconds (high-resolution)
- `ciphertext_size` - Ciphertext size in bytes
- `public_key_size` - Public key size in bytes
- `success` - Boolean indicating handshake success
- `encap_variance` - Encapsulation time variance
- `label` - 0 for normal, 1 for anomalous
- `anomaly_type` - Type of anomaly (normal, timing_moderate, ciphertext_tampering, etc.)

### Benefits of High-Resolution Dataset

- **Literature Alignment**: Uses exact sizes and timing from PQC validation studies
- **Nanosecond Precision**: High-resolution timing for accurate anomaly detection
- **Multiple Anomaly Types**: Covers timing attacks, size tampering, and implicit rejections
- **Suite-Aware Training**: Includes data for ML-KEM-768, ML-KEM-1024, and classical suites

---

## Code Changes Made

1. **Serialization fix**: X25519 public key export now uses `public_bytes(encoding=..., format=...)` instead of the non-existent `public_bytes_raw()`.
2. **Hex output**: Changed from `binascii.hexlify()` (returns bytes) to `.hex()` for cleaner string output.
3. **Fallback KEM**: Added a mock `oqs.KeyEncapsulation` class for local testing when `liboqs-python` is unavailable.
4. **liboqs-python API compatibility**: `oqs_middleware.py` handles both the 0.16.0 API (`encap_secret`/`decap_secret`, `get_enabled_kem_mechanisms`) and older APIs (`encapsulate`/`decapsulate`, `get_enabled_KEMs`) via runtime detection.
5. **Anomaly detector backend awareness**: `ai_anomaly_detector.py` now accepts a `use_real_backend` flag via `set_backend_mode(real=True)`. When the real oqs backend is active, suite-aware latency checks use `latency_threshold_ms` (tuned for real liboqs overhead, ~2ms). When using the mock backend, the much higher `latency_threshold_ms_mock` (200ms) is preferred.
6. **Real vs mock threshold wiring**: `3SA.py` passes `force_real` to the anomaly detector after loading suite overhead ranges, so the correct threshold key is used during scoring.

---

## Security Notes

**This is a demonstration, not production-ready code:**
- The fallback KEM mock is deterministic and insecure — use `--force-real` for real cryptographic operations.
- No authentication or signatures are used.
- Session keys are not persisted or used for encryption in this demo.
- When using the real liboqs backend, re-run `benchmark.py` to calibrate the AI anomaly detector's latency thresholds, as real liboqs calls may differ from the literature-based assumptions used in the mock.
- For production, add proper error handling, input validation, protocol constraints, and use a validated liboqs build.

---

## References

- [Open Quantum Safe Project](https://openquantumsafe.org/)
- [NIST PQC Standardization](https://csrc.nist.gov/projects/post-quantum-cryptography/)
- [RFC 3610: HKDF](https://tools.ietf.org/html/rfc3610)
- [Cryptography Library Docs](https://cryptography.io/)

---

## License

Educational use only. Adapt as needed for your research or learning.
