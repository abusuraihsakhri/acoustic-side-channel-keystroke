# Acoustic Side-Channel Keystroke Recognition & Power Hum Cryptanalysis

A Python forensic acoustics and side-channel cryptanalysis library and CLI tool. Implements keystroke dynamics timing analysis, digraph latency biometrics, acoustic Time-Difference-of-Arrival (TDOA) keyboard triangulation, and Electric Network Frequency (ENF) 50Hz/60Hz spectral power hum analysis.

Requires Python standard library only (zero external runtime dependencies).

---

## Features

- **Keystroke Dynamics Analysis:** Computes inter-key intervals (IKI), key dwell times, flight times, typing speed in characters per minute (CPM), and typing rhythm regularity.
- **Digraph Fingerprinting:** Profiles latency across character pairs (digraphs) and calculates statistical uniqueness scores against baseline typing speeds.
- **Acoustic TDOA Keyboard Triangulation:** Multilaterates key impact positions $(x, y)$ on a physical keyboard surface from sub-millisecond microphone arrival time differences.
- **Electric Network Frequency (ENF) Forensics:** Extracts 50Hz / 60Hz power grid hum and harmonic signatures to verify regional electrical grid standard (`EU_50Hz` vs. `US_60Hz`) and assess device audio timestamp fidelity.
- **Biometric Authentication & Impostor Detection:** Matches candidate typing samples against enrolled reference profiles using normalized distance metrics and configurable match thresholds.
- **Interactive Console & Batch CLI:** Wizard mode, batch timing profile extraction from CSV/JSON, TDOA multilateration, and automated synthetic/recorded ENF spectral checks.

---

## Installation & Requirements

- Python 3.10+ (tested on 3.10, 3.11, 3.12)
- Zero external runtime dependencies. `pytest` is optional for running tests.

```bash
git clone https://github.com/abusuraihsakhri/acoustic-side-channel-keystroke.git
cd acoustic-side-channel-keystroke
```

---

## CLI Usage

### 1. Keystroke Timing Analysis
Analyze typing events from CSV or JSON:
```bash
python cli.py -a sample.csv
```
Output as JSON:
```bash
python cli.py -a sample.csv --json
```

### 2. Acoustic TDOA Triangulation
Estimate key location from microphone arrival delays (in milliseconds):
```bash
python cli.py --tdoa 0.25 -0.15 --json
```

### 3. Electric Network Frequency (ENF) Analysis
Analyze mains power hum frequency and grid standard:
```bash
# US 60 Hz grid
python cli.py --enf --enf-hz 60 --json

# EU 50 Hz grid
python cli.py --enf --enf-hz 50 --json
```

### 4. User Enrollment & Biometric Authentication
Enroll reference typing profile:
```bash
python cli.py --enroll sample.csv --user-id alice --json
```

Authenticate candidate keystrokes against enrolled reference:
```bash
python cli.py --authenticate sample.csv --ref-file sample.csv --user-id alice --threshold 0.70 --json
```

### 5. Interactive Wizard Mode
Launch the terminal cryptanalysis console:
```bash
python cli.py --interactive
```

---

## Python API Quickstart

```python
from keystroke_analysis import (
    KeystrokeEvent,
    KeystrokeDynamicsAnalyzer,
    DigraphFingerprintBuilder,
    TDOAKeyboardLocalizer,
    PowerHumSpectralAnalyzer,
)

# 1. Analyze Keystroke Dynamics
events = [
    KeystrokeEvent(key_code="t", press_time_ms=0.0, release_time_ms=80.0),
    KeystrokeEvent(key_code="e", press_time_ms=120.0, release_time_ms=200.0),
    KeystrokeEvent(key_code="s", press_time_ms=240.0, release_time_ms=320.0),
    KeystrokeEvent(key_code="t", press_time_ms=360.0, release_time_ms=440.0),
]
analyzer = KeystrokeDynamicsAnalyzer()
profile = analyzer.extract_profile(events, "user1")
print(f"Typing Speed: {profile.typing_speed_cpm} CPM, Mean IKI: {profile.mean_iki} ms")

# 2. TDOA Keyboard Triangulation
localizer = TDOAKeyboardLocalizer()
result = localizer.triangulate([0.25, -0.15])
print(f"Nearest key: {result.nearest_key} (x: {result.estimated_x_cm} cm, y: {result.estimated_y_cm} cm)")

# 3. ENF Analysis
import math
sr = 44100
samples = [0.5 * math.sin(2.0 * math.pi * 60.0 * i / sr) for i in range(sr)]
enf_res = PowerHumSpectralAnalyzer().analyze(samples, sr)
print(f"Grid Standard: {enf_res.grid_standard} ({enf_res.fundamental_freq_hz} Hz)")
```

---

## Running Tests

Run unit tests via standard `unittest` or `pytest`:

```bash
python test_keystroke_analysis.py
# or
pytest -v
```

