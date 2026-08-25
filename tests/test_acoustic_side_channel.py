"""
Comprehensive Unit Test Suite for Acoustic Side-Channel Keystroke & ENF Cryptanalysis.
"""

import io
import json
import math
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from keystroke_analysis import (
    KeystrokeEvent,
    TypingProfile,
    IKIFingerprint,
    TDOALocalizationResult,
    PowerHumFingerprint,
    KeystrokeDynamicsAnalyzer,
    DigraphFingerprintBuilder,
    TDOAKeyboardLocalizer,
    PowerHumSpectralAnalyzer,
    KeystrokeAuthenticationEngine,
)
import cli


class TestKeystrokeDynamics(unittest.TestCase):
    def setUp(self):
        self.analyzer = KeystrokeDynamicsAnalyzer()

    def test_empty_events(self):
        profile = self.analyzer.extract_profile([], user_id="user_empty")
        self.assertEqual(profile.mean_iki, 0.0)
        self.assertEqual(profile.typing_speed_cpm, 0.0)
        self.assertEqual(profile.flight_times, [])

    def test_single_event(self):
        event = KeystrokeEvent(key_code="a", press_time_ms=100.0, release_time_ms=180.0)
        profile = self.analyzer.extract_profile([event], user_id="user_single")
        self.assertEqual(profile.mean_dwell, 80.0)
        self.assertEqual(profile.mean_iki, 0.0)

    def test_multi_event_normal_sequence(self):
        events = [
            KeystrokeEvent("t", 0.0, 80.0),
            KeystrokeEvent("e", 120.0, 200.0),
            KeystrokeEvent("s", 250.0, 330.0),
            KeystrokeEvent("t", 380.0, 460.0),
        ]
        profile = self.analyzer.extract_profile(events, user_id="user_normal")
        self.assertEqual(len(profile.flight_times), 3)
        self.assertEqual(profile.flight_times[0], 40.0)  # 120 - 80
        self.assertEqual(profile.flight_times[1], 50.0)  # 250 - 200
        self.assertEqual(profile.flight_times[2], 50.0)  # 380 - 330
        self.assertAlmostEqual(profile.mean_dwell, 80.0, delta=1.0)
        self.assertGreater(profile.typing_speed_cpm, 0.0)
        self.assertIn("te", profile.digraph_latencies)
        self.assertIn("es", profile.digraph_latencies)
        self.assertIn("st", profile.digraph_latencies)

    def test_out_of_order_events_sorted(self):
        events = [
            KeystrokeEvent("b", 150.0, 220.0),
            KeystrokeEvent("a", 50.0, 110.0),
        ]
        profile = self.analyzer.extract_profile(events, user_id="user_unordered")
        self.assertIn("ab", profile.digraph_latencies)
        self.assertEqual(profile.flight_times[0], 40.0)  # 150 - 110

    def test_rhythm_regularity_computation(self):
        # Perfect equal intervals
        events_regular = [
            KeystrokeEvent("a", 0.0, 50.0),
            KeystrokeEvent("b", 100.0, 150.0),
            KeystrokeEvent("c", 200.0, 250.0),
            KeystrokeEvent("d", 300.0, 350.0),
        ]
        p_reg = self.analyzer.extract_profile(events_regular, "regular")
        self.assertAlmostEqual(p_reg.rhythm_regularity, 1.0, delta=0.01)


class TestDigraphFingerprints(unittest.TestCase):
    def setUp(self):
        self.analyzer = KeystrokeDynamicsAnalyzer()
        self.builder = DigraphFingerprintBuilder()

    def test_common_digraphs_extracted(self):
        events = [
            KeystrokeEvent("t", 0.0, 60.0),
            KeystrokeEvent("h", 100.0, 160.0),
            KeystrokeEvent("e", 200.0, 260.0),
        ]
        profile = self.analyzer.extract_profile(events, "u1")
        fps = self.builder.build_fingerprints(profile)
        digraph_names = [f.digraph for f in fps]
        self.assertIn("th", digraph_names)
        self.assertIn("he", digraph_names)

    def test_uniqueness_bounds(self):
        score = self.builder._calculate_uniqueness(250.0, 100.0)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)


class TestProfileComparison(unittest.TestCase):
    def setUp(self):
        self.analyzer = KeystrokeDynamicsAnalyzer()

    def test_identical_profiles(self):
        events = [
            KeystrokeEvent("t", 0.0, 60.0),
            KeystrokeEvent("e", 100.0, 160.0),
            KeystrokeEvent("s", 200.0, 260.0),
            KeystrokeEvent("t", 300.0, 360.0),
        ]
        p1 = self.analyzer.extract_profile(events, "u1")
        p2 = self.analyzer.extract_profile(events, "u2")
        similarity = self.analyzer.compare_profiles(p1, p2)
        self.assertAlmostEqual(similarity, 1.0, delta=0.05)

    def test_distinct_profiles(self):
        events_fast = [
            KeystrokeEvent("a", 0.0, 30.0),
            KeystrokeEvent("b", 50.0, 80.0),
            KeystrokeEvent("c", 100.0, 130.0),
        ]
        events_slow = [
            KeystrokeEvent("a", 0.0, 250.0),
            KeystrokeEvent("b", 600.0, 850.0),
            KeystrokeEvent("c", 1200.0, 1450.0),
        ]
        p_fast = self.analyzer.extract_profile(events_fast, "fast")
        p_slow = self.analyzer.extract_profile(events_slow, "slow")
        similarity = self.analyzer.compare_profiles(p_fast, p_slow)
        self.assertLess(similarity, 0.6)


class TestTDOALocalizer(unittest.TestCase):
    def setUp(self):
        self.localizer = TDOAKeyboardLocalizer()

    def test_localization_space_or_center(self):
        # Near center delays
        res = self.localizer.triangulate([0.0, 0.0])
        self.assertIsNotNone(res.nearest_key)
        self.assertGreater(res.confidence, 0.0)

    def test_empty_delays_handling(self):
        res = self.localizer.triangulate([])
        self.assertEqual(res.nearest_key, "unknown")
        self.assertEqual(res.confidence, 0.0)


class TestPowerHumAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = PowerHumSpectralAnalyzer()

    def test_50hz_mains_detection(self):
        sr = 44100
        samples = [0.8 * math.sin(2.0 * math.pi * 50.0 * i / sr) for i in range(sr)]
        res = self.analyzer.analyze(samples, sr)
        self.assertEqual(res.fundamental_freq_hz, 50.0)
        self.assertEqual(res.grid_standard, "EU_50Hz")
        self.assertGreater(res.confidence, 0.5)

    def test_60hz_mains_detection(self):
        sr = 44100
        samples = [0.8 * math.sin(2.0 * math.pi * 60.0 * i / sr) for i in range(sr)]
        res = self.analyzer.analyze(samples, sr)
        self.assertEqual(res.fundamental_freq_hz, 60.0)
        self.assertEqual(res.grid_standard, "US_60Hz")
        self.assertGreater(res.confidence, 0.5)

    def test_empty_audio_samples(self):
        res = self.analyzer.analyze([], 44100)
        self.assertEqual(res.fundamental_freq_hz, 0.0)
        self.assertEqual(res.confidence, 0.0)


class TestKeystrokeAuthenticationEngine(unittest.TestCase):
    def setUp(self):
        self.engine = KeystrokeAuthenticationEngine()

    def test_enroll_and_authenticate_success(self):
        user_events = [
            KeystrokeEvent("a", 0.0, 80.0),
            KeystrokeEvent("d", 120.0, 200.0),
            KeystrokeEvent("m", 240.0, 320.0),
            KeystrokeEvent("i", 360.0, 440.0),
            KeystrokeEvent("n", 480.0, 560.0),
        ]
        self.engine.enroll("admin", user_events)
        auth = self.engine.authenticate(user_events, threshold=0.70)
        self.assertTrue(auth["authenticated"])
        self.assertEqual(auth["best_match_user"], "admin")
        self.assertGreaterEqual(auth["best_match_score"], 0.70)

    def test_authenticate_impostor_rejection(self):
        legit_events = [
            KeystrokeEvent("a", 0.0, 50.0),
            KeystrokeEvent("b", 80.0, 130.0),
            KeystrokeEvent("c", 160.0, 210.0),
        ]
        impostor_events = [
            KeystrokeEvent("a", 0.0, 400.0),
            KeystrokeEvent("b", 800.0, 1200.0),
            KeystrokeEvent("c", 1600.0, 2000.0),
        ]
        self.engine.enroll("legit_user", legit_events)
        auth = self.engine.authenticate(impostor_events, threshold=0.80)
        self.assertFalse(auth["authenticated"])


class TestCLIAndFileIO(unittest.TestCase):
    def test_cli_analyze_timing_csv(self):
        csv_content = (
            "key_code,press_time_ms,release_time_ms\n"
            "q,0,75\n"
            "w,110,185\n"
            "e,220,295\n"
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write(csv_content)
            temp_path = f.name

        try:
            out = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = out
            try:
                exit_code = cli.main(["--analyze-timing", temp_path, "--format", "json", "--user-id", "u_test"])
                self.assertEqual(exit_code, 0)
            finally:
                sys.stdout = old_stdout

            data = json.loads(out.getvalue())
            self.assertEqual(data["user_id"], "u_test")
            self.assertGreater(data["typing_speed_cpm"], 0)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_cli_tdoa_triangulation(self):
        out = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = out
        try:
            exit_code = cli.main(["--tdoa", "0.25", "-0.15", "--format", "json"])
            self.assertEqual(exit_code, 0)
        finally:
            sys.stdout = old_stdout

        data = json.loads(out.getvalue())
        self.assertIn("nearest_key", data)
        self.assertIn("confidence", data)

    def test_cli_enf_analysis(self):
        out = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = out
        try:
            exit_code = cli.main(["--enf", "--enf-hz", "50", "--format", "json"])
            self.assertEqual(exit_code, 0)
        finally:
            sys.stdout = old_stdout

        data = json.loads(out.getvalue())
        self.assertEqual(data["fundamental_freq_hz"], 50.0)
        self.assertEqual(data["grid_standard"], "EU_50Hz")


    def test_finger_mapping_accuracy(self):
        self.assertEqual(KeystrokeDynamicsAnalyzer.FINGER_MAP['q'], 'left_pinky')
        self.assertEqual(KeystrokeDynamicsAnalyzer.FINGER_MAP['f'], 'left_index')
        self.assertEqual(KeystrokeDynamicsAnalyzer.FINGER_MAP['j'], 'right_index')
        self.assertEqual(KeystrokeDynamicsAnalyzer.FINGER_MAP[' '], 'thumb')

    def test_zero_dwell_or_negative_clamp(self):
        analyzer = KeystrokeDynamicsAnalyzer()
        event = KeystrokeEvent("x", 100.0, 90.0)  # corrupt timestamp
        p = analyzer.extract_profile([event], "clamp_user")
        self.assertEqual(p.mean_dwell, 0.0)


class TestMultiUserAuthentication(unittest.TestCase):
    def setUp(self):
        self.engine = KeystrokeAuthenticationEngine()
        self.u1_events = [
            KeystrokeEvent("a", 0.0, 60.0),
            KeystrokeEvent("b", 100.0, 160.0),
            KeystrokeEvent("c", 200.0, 260.0),
        ]
        self.u2_events = [
            KeystrokeEvent("a", 0.0, 150.0),
            KeystrokeEvent("b", 300.0, 450.0),
            KeystrokeEvent("c", 600.0, 750.0),
        ]
        self.engine.enroll("user_fast", self.u1_events)
        self.engine.enroll("user_slow", self.u2_events)

    def test_authenticate_correct_user(self):
        auth1 = self.engine.authenticate(self.u1_events, threshold=0.7)
        self.assertEqual(auth1["best_match_user"], "user_fast")
        self.assertTrue(auth1["authenticated"])

        auth2 = self.engine.authenticate(self.u2_events, threshold=0.7)
        self.assertEqual(auth2["best_match_user"], "user_slow")
        self.assertTrue(auth2["authenticated"])

    def test_no_enrolled_profiles_empty_response(self):
        empty_engine = KeystrokeAuthenticationEngine()
        res = empty_engine.authenticate(self.u1_events)
        self.assertFalse(res["authenticated"])
        self.assertEqual(res["reason"], "no_enrolled_profiles")


class TestTDOAKeyResolution(unittest.TestCase):
    def test_left_key_localization(self):
        localizer = TDOAKeyboardLocalizer()
        # Closer to Mic 1 (left) -> theoretical delay to Mic 2 is positive
        res = localizer.triangulate([0.5, 0.2])
        self.assertIsNotNone(res.nearest_key)
        self.assertGreater(res.confidence, 0.0)

    def test_custom_mic_positions(self):
        mics = [(0.0, 0.0), (30.0, 0.0), (15.0, 20.0)]
        localizer = TDOAKeyboardLocalizer(mic_positions_cm=mics)
        res = localizer.triangulate([0.1, -0.1])
        self.assertIn(res.nearest_key, TDOAKeyboardLocalizer.KEY_COORDINATES_CM)


class TestPowerHumHarmonics(unittest.TestCase):
    def test_mixed_harmonic_detection(self):
        sr = 44100
        # 50Hz fundamental + 100Hz 2nd harmonic + 150Hz 3rd harmonic
        samples = [
            0.6 * math.sin(2.0 * math.pi * 50.0 * i / sr) +
            0.3 * math.sin(2.0 * math.pi * 100.0 * i / sr) +
            0.15 * math.sin(2.0 * math.pi * 150.0 * i / sr)
            for i in range(sr)
        ]
        analyzer = PowerHumSpectralAnalyzer()
        res = analyzer.analyze(samples, sr)
        self.assertEqual(res.fundamental_freq_hz, 50.0)
        self.assertIn(100, res.harmonics)


class TestCLIAdvanced(unittest.TestCase):
    def test_cli_json_enroll_and_auth(self):
        json_content = json.dumps([
            {"key_code": "t", "press_time_ms": 0, "release_time_ms": 80},
            {"key_code": "e", "press_time_ms": 120, "release_time_ms": 200},
            {"key_code": "s", "press_time_ms": 240, "release_time_ms": 320},
            {"key_code": "t", "press_time_ms": 360, "release_time_ms": 440},
        ])
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(json_content)
            temp_path = f.name

        try:
            # 1. Enroll
            out_enroll = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = out_enroll
            try:
                code_enroll = cli.main(["--enroll", temp_path, "--user-id", "alice", "--format", "json"])
                self.assertEqual(code_enroll, 0)
            finally:
                sys.stdout = old_stdout

            # 2. Auth
            out_auth = io.StringIO()
            sys.stdout = out_auth
            try:
                code_auth = cli.main(["--authenticate", temp_path, "--ref-file", temp_path, "--user-id", "alice", "--format", "json"])
                self.assertEqual(code_auth, 0)
            finally:
                sys.stdout = old_stdout

            auth_data = json.loads(out_auth.getvalue())
            self.assertTrue(auth_data["authenticated"])
            self.assertEqual(auth_data["best_match_user"], "alice")
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)



if __name__ == "__main__":
    unittest.main()

