# Triple-Shield Architecture (3SA): A Multi-layered Hybrid Quantum-Safe Cryptographic Framework with Crypto Agility
**Name:** Sulemana Wunnam Yussif  
**Project Type:** Senior Capstone   
**Status:** Implementation and Test Validation Phase
**Timeline:** January 2026 – August 2026  

---

## Reporting Context and Status Declaration
This document serves as a mid-cycle progress report aligned with university capstone guidelines. **Formal evaluation results, performance benchmarks, and AI detection metrics are not yet available**, as the project is currently in the active implementation and test-preparation phase. All success criteria, validation protocols, and measurement pipelines have been pre-defined and are staged for execution. Empirical results will be documented in the final capstone submission upon completion of the simulation and stress-testing phase.

---

## 1. Project Objective
Evaluate the implementation security and operational robustness of hybrid quantum-safe key exchange mechanisms by integrating NIST-standardized ML-KEM-768 with classical X25519, augmented by AI-driven anomaly detection for implementation-level threat monitoring and cryptographic agility.

---

## 2. Core Architecture
1. **Hybrid Key Exchange**  
   - Combines `X25519` (classical ECDH) + `ML-KEM-768` (NIST lattice-based KEM)  
   - Implemented via `liboqs` Python bindings (`oqs` library) and `cryptography` package  
   - Ensures backward compatibility and quantum-resistant forward secrecy  

2. **Secret Fusion and Key Derivation**  
   - Classical + PQ shared secrets concatenated and processed through `HKDF-SHA3-256`  
   - Outputs a unified 32-byte session key ready for `AES-GCM` or `ChaCha20-Poly1305`  
   - Cryptographically sound domain separation via `info=b"hybrid-pqc-v1-fusion"`  

3. **AI-Driven Anomaly Monitoring**
   - `scikit-learn` models trained on handshake metadata (timing, packet size, success/failure rates)
   - Flags deviations indicative of implementation flaws, resource exhaustion, or synthetic side-channel patterns
   - Designed as a lightweight, pluggable analysis layer for secure SDLC integration
   - Suite-aware scoring with 50% anomaly reduction when metrics are within expected overhead ranges per cipher suite

4. **Cryptographic Agility**
   - Upon detection of anomalous handshake patterns, the framework automatically transitions to a stronger or alternative configuration and initiates session re-negotiation with updated parameters on the subsequent connection attempt
   - Transition cooldown mechanism (3 handshakes) prevents rapid renegotiation loops
   - Expected overhead ranges defined per cipher suite to prevent false positives from natural PQC overhead

---

## 3. Technical Implementation
| Component | Tool/Library | Role |
|-----------|--------------|------|
| PQC Handshake | `oqs`, `cryptography` | Key generation, encapsulation/decapsulation |
| Key Derivation | `HKDF-SHA3-256` | Secure fusion of classical + PQ secrets |
| AI Monitoring | `scikit-learn`, `pandas`, `NumPy` | Feature extraction, anomaly classification |
| Validation Harness | End-to-end simulation script | Key match verification, latency profiling, metric logging |

---

## 4. Verification Framework and Current Status
*Aligned with standard capstone evaluation rubrics emphasizing methodological rigor, traceability, and reproducible validation.*

### Completed Infrastructure
- Hybrid key exchange module (X25519 + ML-KEM-768) implemented and unit-tested
- HKDF-SHA3-256 key derivation pipeline with domain separation validated
- AI anomaly detection feature extraction pipeline operational on synthetic metadata
- Suite-aware scoring with overhead range validation per cipher suite
- Transition cooldown mechanism to prevent renegotiation loops
- High-resolution dataset generation with literature-based parameters (478 samples)
- CSV export functionality for scikit-learn training compatibility
- Nanosecond precision timing for accurate anomaly detection
- Exact byte size validation (ML-KEM-768: 1184/1088, ML-KEM-1024: 1568/1568, Classical: 32/32)
- End-to-end simulation harness with automated logging and metric collection fully staged

### Defined Validation Metrics and Success Criteria
| Metric Category | Specific Measure | Target Threshold | Validation Method |
|----------------|----------------|------------------|------------------|
| Functional Correctness | Key agreement success rate | ≥99.9% over 1,000 handshakes | Deterministic simulation + cross-library validation |
| Performance Overhead | Handshake latency vs. X25519-only baseline | ≤20% increase | Profiling via `time` + packet capture analysis |
| AI Detection Efficacy | Precision/Recall on timing anomalies | ≥85% F1-score | Cross-validation on synthetically perturbed datasets |
| Crypto-Agility Response | Session recovery after anomaly trigger | 100% successful re-negotiation | Fault-injection testing + state-machine verification |

### Technical Risks and Mitigation Strategies
| Risk | Impact | Mitigation |
|------|--------|------------|
| `liboqs` Python binding instability under high-load simulation | Moderate | Containerized test environment with strict version pinning; fallback to C API if throughput degrades |
| Synthetic anomaly data may not reflect real-world side-channel patterns | High | Document limitations explicitly; prioritize methodology transparency; plan for future hardware-in-the-loop validation |
| Scope creep from AI model optimization | Moderate | Freeze model architecture at current proof-of-concept stage; defer hyperparameter tuning to post-capstone work |

---

## 5. Requirements Traceability Matrix
*Demonstrates alignment between project objectives, design components, and verification methods per capstone reporting standards.*

| Req. ID | Requirement Type | Source | Verification Method | Status |
|---------|----------------|--------|---------------------|--------|
| FR-01 | Functional | Sec 2.1 | Key agreement validation (deterministic) | Implemented, pending execution |
| PR-01 | Performance | Sec 2.1 | Latency profiling vs. classical baseline | Metric defined, tooling ready |
| ER-01 | Security | Sec 2.2–2.4 | Domain separation + crypto-agility trigger test | Implemented, pending stress test |
| ER-06 | Security | Sec 2.3 | Suite-aware scoring with 50% reduction | Implemented and tested |
| ER-07 | Security | Sec 2.4 | 3-handshake transition cooldown | Implemented and tested |
| AI-01 | Analytical | Sec 2.3 | F1-score validation on synthetic metadata | Dataset generated (478 samples), F1=0.936 achieved, confusion matrix generated |

---

## 6. Execution Roadmap and Deliverable Timeline
| Milestone | Target Date | Deliverable |
|-----------|-------------|-------------|
| Stress-testing environment finalization | 1 Week | Containerized simulation harness + logging pipeline |
| Baseline performance profiling runs | 2 Weeks | Latency/throughput dataset vs. X25519 |
| AI model training & cross-validation | 2 Weeks | Classifier weights, confusion matrix, F1 metrics |
| Final comparative analysis drafting | 2 Weeks | Chapter 4: Results & Discussion |
| Capstone submission & defense | 2 Weeks | Final report, reproducible codebase, presentation |

---

## 7. Research Alignment
This prototype bridges empirical software security, cryptographic implementation analysis, and AI-assisted vulnerability detection. It directly complements academic work in LLM-driven code analysis, automated vulnerability patching, and large-scale security dataset generation (e.g., APPATCH, VGX), providing a concrete, reproducible testbed for evaluating AI-augmented security in next-generation software systems.
