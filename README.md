# Acoustic Side Channel Keystroke

> **Domain:** Post-Quantum Cryptography & Zero-Knowledge Architecture  
> **Reference Guidelines & Standards:** `NIST FIPS 203/204/205, NIST SP 800-90B & ISO/IEC Standards`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Acoustic Side-Channel Keystroke & Power Hum Cryptanalysis Main Module.

Acoustic Side-Channel Keystroke Recognition & Power Hum Spectral Cryptanalysis Engine.

Implements:
1. Keystroke Dynamics & Timing Analysis (Dwell time, Flight time, Inter-Key Interval, CPM, Regularity).
2. Digraph Latency Fingerprinting and Statistical Biometrics (Manhattan & Mahalanobis distances).
3. Acoustic Time-Difference-of-Arrival (TDOA) Keyboard Triangulation.
4. Electric Network Frequency (ENF) / Power Hum 50Hz/60Hz Spectral Cryptanalysis.
5. Biometric Keystroke Authentication & Impostor Detection.

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Core Algorithmic & Evaluation Engines

- **`KeystrokeEvent`** — dedicated module for keystroke event evaluation and state verification.
- **`TypingProfile`** — dedicated module for typing profile evaluation and state verification.
- **`IKIFingerprint`** — dedicated module for i k i fingerprint evaluation and state verification.
- **`TDOALocalizationResult`** — dedicated module for t d o a localization result evaluation and state verification.
- **`PowerHumFingerprint`** — dedicated module for power hum fingerprint evaluation and state verification.
- **`KeystrokeDynamicsAnalyzer`**: Extracts inter-key intervals, dwell times, flight latencies, and regularity metrics.

---

## 📐 Mathematical Formulation & Logic

```text
  uniqueness = self._calculate_uniqueness(latency, profile.mean_iki)
  score = self.analyzer.compare_profiles(candidate_profile, enrolled_profile)
  best_score = results[best_user]
```

---

## 💻 CLI Quickstart & Usage

### 1. Guided Interactive Mode
```bash
python cli.py
```

### 2. Direct Parameterized Evaluation
```bash
python cli.py --interactive <value> --analyze-timing <value> --tdoa <value> --enf <value>
```

### Parameter Reference
- `--interactive`: Specifies input measurement or parameter value.
- `--analyze-timing`: Specifies input measurement or parameter value.
- `--tdoa`: Specifies input measurement or parameter value.
- `--enf`: Specifies input measurement or parameter value.
- `--enroll`: Specifies input measurement or parameter value.
- `--authenticate`: Specifies input measurement or parameter value.
- `--user-id`: Specifies input measurement or parameter value.
- `--ref-file`: Specifies input measurement or parameter value.
- `--threshold`: Specifies input measurement or parameter value.
- `--enf-hz`: Specifies input measurement or parameter value.

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `task_id` | Parameter / observation metric | Required |
| `target_identifier` | Parameter / observation metric | Required |
| `primary_metric` | Parameter / observation metric | Required |
| `secondary_metric` | Parameter / observation metric | Required |
| `is_critical_flag` | Parameter / observation metric | Required |
| `status_descriptor` | Parameter / observation metric | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active AST and regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **Air-Gapped LLM Reasoning Adapter:** Agnostic integration for local Ollama instances (`llama3`, `mistral`), Claude 3.5 Sonnet, GPT-4o, and deterministic test mocks.
* **Active Learning Bayesian Calibration:** Dynamic tracker updating worker reliability weights and monitoring Brier calibration drift.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
docker build -t acoustic-side-channel-keystroke .
docker run -p 8000:8000 acoustic-side-channel-keystroke
```
