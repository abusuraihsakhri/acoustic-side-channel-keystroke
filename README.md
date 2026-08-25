# Acoustic Side-Channel Keystroke & Power Hum (ENF) Cryptanalysis

Production-grade hardware security and acoustic cryptanalysis engine for **keystroke dynamics profiling**, **acoustic Time-Difference-of-Arrival (TDOA) localization**, and **Electric Network Frequency (ENF) power hum forensic analysis**.

---

## Core Capabilities

1. **Keystroke Dynamics & Timing Analysis**:
   - **Dwell Time ($T_{\text{dwell}}$)**: Duration between key press and key release ($\Delta t = t_{\text{release}} - t_{\text{press}}$).
   - **Flight Time / Inter-Key Interval (IKI)**: Latency between consecutive keystroke releases and subsequent presses ($\text{IKI} = t_{\text{press}, i} - t_{\text{release}, i-1}$).
   - **Typing Velocity (CPM)**: Characters per minute normalized over active session duration.
   - **Rhythm Regularity Metric**: Coefficient of variation metric ($1 - \frac{\sigma_{\text{IKI}}}{\mu_{\text{IKI}}}$) measuring typing cadence consistency.

2. **Digraph Latency Fingerprinting**:
   - Extraction of characteristic digraph transition distributions (`th`, `he`, `in`, `er`, `an`, `re`, `on`, `at`, `en`, `nd`).
   - Statistical uniqueness calculation based on exponential deviation from baseline user mean.

3. **Acoustic TDOA Keyboard Triangulation**:
   - Multilateration solving for 2D coordinate $(x, y)$ on keyboard layout:
     $$\Delta t_{ij} = \frac{d_i - d_j}{v_{\text{sound}}}$$
   - Spatial key identification comparing observed acoustic delays to spatial key centroids.

4. **Electric Network Frequency (ENF) Power Hum Forensics**:
   - Discrete Fourier Transform (DFT) spectral decomposition across mains power frequencies (50 Hz European / Asian grid vs. 60 Hz North American grid) and higher harmonics (100 Hz, 120 Hz, 150 Hz, 180 Hz, 240 Hz).
   - Power ratio confidence and grid standard attribution.

5. **Biometric Keystroke Authentication**:
   - User profiling, template enrollment, and candidate verification using multi-feature composite distance functions.

---

## Mathematical Formulations

### Composite Keystroke Distance
Given reference profile $P_{\text{ref}}$ and candidate profile $P_{\text{cand}}$:

$$D = w_1 \frac{|\mu_{\text{IKI}, 1} - \mu_{\text{IKI}, 2}|}{\max(\mu_1, \mu_2)} + w_2 \frac{|\sigma_{\text{IKI}, 1} - \sigma_{\text{IKI}, 2}|}{\max(\sigma_1, \sigma_2)} + w_3 \frac{|\mu_{\text{dwell}, 1} - \mu_{\text{dwell}, 2}|}{\max(\mu_1, \mu_2)} + w_4 \frac{1}{|S|} \sum_{dg \in S} \frac{|L_1(dg) - L_2(dg)|}{\max(L_1, L_2)}$$

Similarity score:

$$\text{Similarity} = \max(0, 1 - D)$$

---

## Command Line Interface (CLI)

### 1. Analyze Keystroke Timing from CSV/JSON
```bash
python cli.py --analyze-timing sample.csv --user-id "analyst_01" --format text
```

### 2. Acoustic TDOA Keystroke Localization
```bash
python cli.py --tdoa 0.25 -0.15 --format json
```

### 3. Electric Network Frequency (ENF) Analysis
```bash
python cli.py --enf --enf-hz 50.0 --format json
```

### 4. Enroll Reference User Profile
```bash
python cli.py --enroll reference_typing.csv --user-id "analyst_01"
```

### 5. Authenticate Candidate Keystroke Sample
```bash
python cli.py --authenticate candidate_typing.csv --ref-file reference_typing.csv --threshold 0.75
```

### 6. Interactive Cryptanalysis Console
```bash
python cli.py --interactive
```

---

## Unit Testing

Execute all unit tests using pure Python:

```bash
python -m unittest discover -s tests -v
# or
python test_keystroke_analysis.py
```
