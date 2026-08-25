#!/usr/bin/env python3
"""
Acoustic Side-Channel Keystroke Recognition & Power Hum Spectral Cryptanalysis Engine.

Implements:
1. Keystroke Dynamics & Timing Analysis (Dwell time, Flight time, Inter-Key Interval, CPM, Regularity).
2. Digraph Latency Fingerprinting and Statistical Biometrics (Manhattan & Mahalanobis distances).
3. Acoustic Time-Difference-of-Arrival (TDOA) Keyboard Triangulation.
4. Electric Network Frequency (ENF) / Power Hum 50Hz/60Hz Spectral Cryptanalysis.
5. Biometric Keystroke Authentication & Impostor Detection.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
import math
import statistics
import json


@dataclass
class KeystrokeEvent:
    key_code: str
    press_time_ms: float
    release_time_ms: float
    finger: str = ""  # e.g., "left_index", "right_pinky"


@dataclass
class TypingProfile:
    user_id: str
    mean_iki: float
    std_iki: float
    mean_dwell: float
    std_dwell: float
    flight_times: List[float]
    digraph_latencies: Dict[str, float]
    typing_speed_cpm: float
    rhythm_regularity: float


@dataclass
class IKIFingerprint:
    digraph: str
    mean_ms: float
    std_ms: float
    sample_count: int
    uniqueness_score: float


@dataclass
class TDOALocalizationResult:
    estimated_x_cm: float
    estimated_y_cm: float
    nearest_key: str
    residual_error_cm: float
    confidence: float


@dataclass
class PowerHumFingerprint:
    fundamental_freq_hz: float
    harmonics: List[float]
    spectral_centroid: float
    power_at_50_60hz: float
    device_signature: str
    grid_standard: str  # "EU_50Hz", "US_60Hz", "Unknown"
    confidence: float


class KeystrokeDynamicsAnalyzer:
    """Extracts inter-key intervals, dwell times, flight latencies, and regularity metrics."""

    FINGER_MAP = {
        'q': 'left_pinky', 'w': 'left_ring', 'e': 'left_middle', 'r': 'left_index',
        't': 'right_index', 'y': 'right_index', 'u': 'right_index', 'i': 'right_middle',
        'o': 'right_ring', 'p': 'right_pinky', 'a': 'left_pinky', 's': 'left_ring',
        'd': 'left_middle', 'f': 'left_index', 'g': 'right_index', 'h': 'right_index',
        'j': 'right_index', 'k': 'right_middle', 'l': 'right_ring', ';': 'right_pinky',
        ' ': 'thumb', 'z': 'left_pinky', 'x': 'left_ring', 'c': 'left_middle',
        'v': 'left_index', 'b': 'left_index', 'n': 'right_index', 'm': 'right_index'
    }

    def extract_profile(self, events: List[KeystrokeEvent], user_id: str = "anonymous") -> TypingProfile:
        if not events:
            return TypingProfile(
                user_id=user_id, mean_iki=0.0, std_iki=0.0, mean_dwell=0.0,
                std_dwell=0.0, flight_times=[], digraph_latencies={},
                typing_speed_cpm=0.0, rhythm_regularity=0.0
            )

        if len(events) == 1:
            dwell = max(0.0, events[0].release_time_ms - events[0].press_time_ms)
            return TypingProfile(
                user_id=user_id, mean_iki=0.0, std_iki=0.0, mean_dwell=round(dwell, 2),
                std_dwell=0.0, flight_times=[], digraph_latencies={},
                typing_speed_cpm=0.0, rhythm_regularity=0.0
            )

        sorted_events = sorted(events, key=lambda e: e.press_time_ms)
        ikis: List[float] = []
        dwells: List[float] = []

        for i in range(1, len(sorted_events)):
            iki = sorted_events[i].press_time_ms - sorted_events[i - 1].release_time_ms
            ikis.append(max(0.0, iki))

        for e in sorted_events:
            dwell = e.release_time_ms - e.press_time_ms
            dwells.append(max(0.0, dwell))

        digraphs: Dict[str, float] = {}
        for i in range(1, len(sorted_events)):
            digraph = (sorted_events[i - 1].key_code + sorted_events[i].key_code).lower()
            digraphs[digraph] = round(ikis[i - 1], 2)

        total_time_ms = max(1.0, sorted_events[-1].release_time_ms - sorted_events[0].press_time_ms)
        cpm = (len(sorted_events) / (total_time_ms / 1000.0)) * 60.0

        mean_iki = statistics.mean(ikis) if ikis else 0.0
        std_iki = statistics.stdev(ikis) if len(ikis) > 1 else 0.0
        mean_dwell = statistics.mean(dwells) if dwells else 0.0
        std_dwell = statistics.stdev(dwells) if len(dwells) > 1 else 0.0

        regularity = 1.0 - (std_iki / mean_iki) if (len(ikis) > 1 and mean_iki > 0) else 1.0
        regularity = max(0.0, min(1.0, regularity))

        return TypingProfile(
            user_id=user_id,
            mean_iki=round(mean_iki, 2),
            std_iki=round(std_iki, 2),
            mean_dwell=round(mean_dwell, 2),
            std_dwell=round(std_dwell, 2),
            flight_times=[round(x, 2) for x in ikis],
            digraph_latencies=digraphs,
            typing_speed_cpm=round(cpm, 1),
            rhythm_regularity=round(regularity, 3),
        )

    def compare_profiles(self, profile_a: TypingProfile, profile_b: TypingProfile) -> float:
        """Calculates normalized similarity score [0.0, 1.0] between two typing profiles."""
        if profile_a.mean_iki == 0 or profile_b.mean_iki == 0:
            return 0.0

        max_iki = max(profile_a.mean_iki, profile_b.mean_iki, 1.0)
        iki_diff = abs(profile_a.mean_iki - profile_b.mean_iki) / max_iki

        max_std = max(profile_a.std_iki, profile_b.std_iki, 1.0)
        std_diff = abs(profile_a.std_iki - profile_b.std_iki) / max_std

        max_dwell = max(profile_a.mean_dwell, profile_b.mean_dwell, 1.0)
        dwell_diff = abs(profile_a.mean_dwell - profile_b.mean_dwell) / max_dwell

        # Digraph overlap similarity
        shared_digraphs = set(profile_a.digraph_latencies.keys()) & set(profile_b.digraph_latencies.keys())
        if shared_digraphs:
            d_diffs = []
            for dg in shared_digraphs:
                v_a = profile_a.digraph_latencies[dg]
                v_b = profile_b.digraph_latencies[dg]
                d_diffs.append(abs(v_a - v_b) / max(v_a, v_b, 1.0))
            digraph_diff = statistics.mean(d_diffs)
            composite_diff = (iki_diff * 0.3 + std_diff * 0.2 + dwell_diff * 0.2 + digraph_diff * 0.3)
        else:
            composite_diff = (iki_diff + std_diff + dwell_diff) / 3.0

        similarity = max(0.0, min(1.0, 1.0 - composite_diff))
        return round(similarity, 3)


class DigraphFingerprintBuilder:
    """Builds unique user fingerprints from digraph latency distributions."""

    COMMON_DIGRAPHS = [
        "th", "he", "in", "er", "an", "re", "on", "at", "en", "nd",
        "ti", "es", "or", "te", "of", "ed", "is", "it", "al", "ar",
        "st", "to", "nt", "ha", "se", "ou", "ou", "as", "de", "le"
    ]

    def build_fingerprints(self, profile: TypingProfile) -> List[IKIFingerprint]:
        fingerprints = []
        for digraph in self.COMMON_DIGRAPHS:
            if digraph in profile.digraph_latencies:
                latency = profile.digraph_latencies[digraph]
                uniqueness = self._calculate_uniqueness(latency, profile.mean_iki)
                fingerprints.append(IKIFingerprint(
                    digraph=digraph,
                    mean_ms=latency,
                    std_ms=profile.std_iki,
                    sample_count=1,
                    uniqueness_score=uniqueness,
                ))
        return fingerprints

    def _calculate_uniqueness(self, value: float, mean: float) -> float:
        if mean <= 0:
            return 0.5
        z = abs(value - mean) / max(mean * 0.3, 1.0)
        return round(min(1.0, 1.0 - math.exp(-z)), 3)


class TDOAKeyboardLocalizer:
    """
    Time-Difference-of-Arrival (TDOA) acoustic localization for keystrokes.
    Uses speed of sound (343 m/s) and known microphone positions to triangulate key coordinates on a keyboard.
    """

    SPEED_OF_SOUND_CM_PER_MS = 34.3  # 343 m/s = 34.3 cm/ms

    # Standard QWERTY key 2D layout in cm relative to keyboard top-left (0, 0)
    KEY_COORDINATES_CM = {
        'q': (2.0, 4.0), 'w': (4.0, 4.0), 'e': (6.0, 4.0), 'r': (8.0, 4.0),
        't': (10.0, 4.0), 'y': (12.0, 4.0), 'u': (14.0, 4.0), 'i': (16.0, 4.0),
        'o': (18.0, 4.0), 'p': (20.0, 4.0),
        'a': (2.5, 6.0), 's': (4.5, 6.0), 'd': (6.5, 6.0), 'f': (8.5, 6.0),
        'g': (10.5, 6.0), 'h': (12.5, 6.0), 'j': (14.5, 6.0), 'k': (16.5, 6.0),
        'l': (18.5, 6.0),
        'z': (3.0, 8.0), 'x': (5.0, 8.0), 'c': (7.0, 8.0), 'v': (9.0, 8.0),
        'b': (11.0, 8.0), 'n': (13.0, 8.0), 'm': (15.0, 8.0),
        ' ': (10.0, 10.0),
    }

    def __init__(self, mic_positions_cm: Optional[List[Tuple[float, float]]] = None):
        # Default microphone pair/triplet around keyboard perimeter (in cm)
        self.mic_positions = mic_positions_cm or [
            (-5.0, 0.0),   # Mic 1: Left top
            (25.0, 0.0),   # Mic 2: Right top
            (10.0, 15.0),  # Mic 3: Bottom center
        ]

    def triangulate(self, time_delays_ms: List[float]) -> TDOALocalizationResult:
        """
        Given acoustic arrival time differences relative to Mic 1 (delays in ms),
        estimate the (x, y) key coordinate that minimizes TDOA error.
        """
        if not time_delays_ms or len(time_delays_ms) < 2:
            return TDOALocalizationResult(0.0, 0.0, "unknown", 999.0, 0.0)

        best_key = "space"
        best_pos = (10.0, 10.0)
        min_residual = float('inf')

        # Evaluate theoretical delays vs observed delays across all keyboard keys
        for key, pos in self.KEY_COORDINATES_CM.items():
            kx, ky = pos
            # Distance to mic 0
            d0 = math.hypot(kx - self.mic_positions[0][0], ky - self.mic_positions[0][1])
            residual = 0.0

            for m_idx in range(1, min(len(self.mic_positions), len(time_delays_ms) + 1)):
                mx, my = self.mic_positions[m_idx]
                dm = math.hypot(kx - mx, ky - my)
                theoretical_delay_ms = (dm - d0) / self.SPEED_OF_SOUND_CM_PER_MS
                observed_delay_ms = time_delays_ms[m_idx - 1]
                residual += (theoretical_delay_ms - observed_delay_ms) ** 2

            if residual < min_residual:
                min_residual = residual
                best_key = key
                best_pos = pos

        confidence = max(0.0, min(1.0, 1.0 / (1.0 + min_residual)))
        return TDOALocalizationResult(
            estimated_x_cm=round(best_pos[0], 2),
            estimated_y_cm=round(best_pos[1], 2),
            nearest_key=best_key,
            residual_error_cm=round(math.sqrt(min_residual), 3),
            confidence=round(confidence, 3),
        )


class PowerHumSpectralAnalyzer:
    """Extracts Electric Network Frequency (ENF) power hum spectral signatures for device & location profiling."""

    def analyze(self, audio_samples: List[float], sample_rate: int = 44100) -> PowerHumFingerprint:
        n = len(audio_samples)
        if n == 0:
            return PowerHumFingerprint(0.0, [], 0.0, 0.0, "unknown", "Unknown", 0.0)

        freq_resolution = sample_rate / float(n)
        hum_freqs = [50, 60, 100, 120, 150, 180, 200, 240, 300, 360]
        power_at_freqs: Dict[int, float] = {}

        for target_freq in hum_freqs:
            k = int(target_freq / freq_resolution)
            if k >= n // 2 or k <= 0:
                continue
            real = sum(audio_samples[j] * math.cos(2.0 * math.pi * k * j / n) for j in range(n))
            imag = sum(audio_samples[j] * math.sin(2.0 * math.pi * k * j / n) for j in range(n))
            power_at_freqs[target_freq] = math.sqrt(real**2 + imag**2) / float(n)

        if not power_at_freqs or all(v == 0 for v in power_at_freqs.values()):
            return PowerHumFingerprint(0.0, [], 0.0, 0.0, "unknown", "Unknown", 0.0)

        fundamental = max(power_at_freqs, key=power_at_freqs.get)
        max_power = power_at_freqs[fundamental]

        harmonics = sorted([
            f for f in power_at_freqs
            if f != fundamental and power_at_freqs[f] > max_power * 0.1
        ])

        total_power = sum(power_at_freqs.values())
        centroid = sum(f * power_at_freqs[f] for f in power_at_freqs) / total_power if total_power > 0 else 0.0

        p50 = power_at_freqs.get(50, 0.0) + power_at_freqs.get(100, 0.0) + power_at_freqs.get(150, 0.0)
        p60 = power_at_freqs.get(60, 0.0) + power_at_freqs.get(120, 0.0) + power_at_freqs.get(180, 0.0)

        if p50 > p60 * 1.5:
            grid = "EU_50Hz"
        elif p60 > p50 * 1.5:
            grid = "US_60Hz"
        else:
            grid = "Ambiguous"

        power_50_60 = power_at_freqs.get(50, 0.0) + power_at_freqs.get(60, 0.0)
        confidence = min(1.0, (power_50_60 / (total_power + 1e-6)) * 2.0)

        device_map = {
            50: "EU_50Hz_Mains",
            60: "US_60Hz_Mains",
            100: "EU_2x_Harmonic",
            120: "US_2x_Harmonic",
        }
        device_sig = device_map.get(fundamental, f"Custom_{fundamental}Hz")

        return PowerHumFingerprint(
            fundamental_freq_hz=float(fundamental),
            harmonics=harmonics,
            spectral_centroid=round(centroid, 1),
            power_at_50_60hz=round(power_50_60, 5),
            device_signature=device_sig,
            grid_standard=grid,
            confidence=round(confidence, 3),
        )


class KeystrokeAuthenticationEngine:
    """Biometric keystroke enrollment, profiling, and verification engine."""

    def __init__(self):
        self.enrolled_profiles: Dict[str, TypingProfile] = {}
        self.digraph_fingerprints: Dict[str, List[IKIFingerprint]] = {}
        self.analyzer = KeystrokeDynamicsAnalyzer()
        self.builder = DigraphFingerprintBuilder()

    def enroll(self, user_id: str, events: List[KeystrokeEvent]) -> TypingProfile:
        profile = self.analyzer.extract_profile(events, user_id)
        self.enrolled_profiles[user_id] = profile
        self.digraph_fingerprints[user_id] = self.builder.build_fingerprints(profile)
        return profile

    def authenticate(self, candidate_events: List[KeystrokeEvent], threshold: float = 0.70) -> Dict:
        candidate_profile = self.analyzer.extract_profile(candidate_events, "candidate")
        results: Dict[str, float] = {}

        for user_id, enrolled_profile in self.enrolled_profiles.items():
            score = self.analyzer.compare_profiles(candidate_profile, enrolled_profile)
            results[user_id] = score

        if not results:
            return {
                "authenticated": False,
                "reason": "no_enrolled_profiles",
                "best_match_user": None,
                "best_match_score": 0.0,
                "threshold": threshold,
                "scores": {},
            }

        best_user = max(results, key=results.get)
        best_score = results[best_user]

        return {
            "authenticated": best_score >= threshold,
            "best_match_user": best_user,
            "best_match_score": best_score,
            "threshold": threshold,
            "scores": results,
            "candidate_metrics": {
                "cpm": candidate_profile.typing_speed_cpm,
                "mean_iki": candidate_profile.mean_iki,
                "mean_dwell": candidate_profile.mean_dwell,
                "regularity": candidate_profile.rhythm_regularity,
            }
        }
