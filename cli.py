#!/usr/bin/env python3
"""
Command Line Interface for Acoustic Side-Channel Keystroke & ENF Cryptanalysis.
"""

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import List, Optional

from keystroke_analysis import (
    KeystrokeEvent,
    TypingProfile,
    KeystrokeDynamicsAnalyzer,
    DigraphFingerprintBuilder,
    TDOAKeyboardLocalizer,
    PowerHumSpectralAnalyzer,
    KeystrokeAuthenticationEngine,
)


def _validate_file_path(filepath: str) -> Path:
    """Validate file path for existence, extension, and directory traversal safety."""
    # Reject obvious path traversal attempts before resolving
    if ".." in filepath:
        raise ValueError(f"Access denied: path traversal not allowed: {filepath}")

    path = Path(filepath)

    try:
        resolved = path.resolve()
    except (OSError, RuntimeError) as e:
        raise ValueError(f"Invalid file path: {filepath} ({e})")

    if not resolved.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    if not resolved.is_file():
        raise ValueError(f"Path is not a regular file: {filepath}")

    # Whitelist allowed extensions to prevent arbitrary file execution
    allowed_extensions = {".csv", ".json"}
    if resolved.suffix.lower() not in allowed_extensions:
        raise ValueError(
            f"Unsupported file type '{resolved.suffix}'. "
            f"Allowed: {', '.join(sorted(allowed_extensions))}"
        )

    return resolved


def _safe_float(value, field_name: str = "value") -> float:
    """Safely parse a float, rejecting NaN and infinity."""
    try:
        result = float(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Invalid numeric value for {field_name}: {value!r} ({e})")
    if math.isnan(result) or math.isinf(result):
        raise ValueError(f"Invalid numeric value for {field_name}: {result} (NaN/Inf not allowed)")
    return result


def load_keystrokes_from_file(filepath: str) -> List[KeystrokeEvent]:
    """Load keystroke events from a CSV or JSON file with validation."""
    path = _validate_file_path(filepath)
    events: List[KeystrokeEvent] = []

    try:
        if path.suffix.lower() == ".json":
            data = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(data, list):
                raise ValueError("JSON file must contain a list of keystroke objects")
            for idx, item in enumerate(data):
                if not isinstance(item, dict):
                    raise ValueError(f"JSON item at index {idx} is not an object")
                events.append(KeystrokeEvent(
                    key_code=str(item.get("key_code") or item.get("key", "")),
                    press_time_ms=_safe_float(
                        item.get("press_time_ms") if item.get("press_time_ms") is not None else item.get("press", 0.0),
                        f"press_time_ms[{idx}]"
                    ),
                    release_time_ms=_safe_float(
                        item.get("release_time_ms") if item.get("release_time_ms") is not None else item.get("release", 0.0),
                        f"release_time_ms[{idx}]"
                    ),
                    finger=str(item.get("finger", "")),
                ))
        else:
            with open(path, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row_idx, row in enumerate(reader):
                    events.append(KeystrokeEvent(
                        key_code=str(row.get("key_code") or row.get("key") or ""),
                        press_time_ms=_safe_float(
                            row.get("press_time_ms") or row.get("press") or 0.0,
                            f"press_time_ms row {row_idx}"
                        ),
                        release_time_ms=_safe_float(
                            row.get("release_time_ms") or row.get("release") or 0.0,
                            f"release_time_ms row {row_idx}"
                        ),
                        finger=str(row.get("finger") or ""),
                    ))
    except (json.JSONDecodeError, csv.Error) as e:
        raise ValueError(f"Failed to parse {path.suffix.upper()} file: {e}")

    return events


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="acoustic-side-channel",
        description="Acoustic Side-Channel Keystroke Recognition & Power Hum (ENF) Cryptanalysis Suite",
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--interactive", "-I", action="store_true", help="Launch interactive cryptanalysis console.")
    mode.add_argument("--analyze-timing", "-a", metavar="FILE", help="Analyze keystroke timing profile from CSV/JSON.")
    mode.add_argument("--tdoa", nargs="+", type=float, metavar="DELAY_MS", help="Triangulate keystroke position from TDOA delays in ms.")
    mode.add_argument("--enf", action="store_true", help="Analyze Electric Network Frequency (ENF) power hum.")
    mode.add_argument("--enroll", metavar="FILE", help="Enroll reference profile from keystroke CSV/JSON.")
    mode.add_argument("--authenticate", metavar="FILE", help="Authenticate candidate keystrokes against reference profile.")

    # Options
    parser.add_argument("--user-id", default="target_user", help="User identifier for enrollment / analysis.")
    parser.add_argument("--ref-file", metavar="FILE", help="Reference profile file for authentication.")
    parser.add_argument("--threshold", type=float, default=0.70, help="Biometric match threshold (default: 0.70).")
    parser.add_argument("--enf-hz", type=float, default=60.0, help="Target frequency for synthetic ENF signal test (default: 60.0 Hz).")
    parser.add_argument("--audio-file", metavar="FILE", help="Audio samples file (JSON list of floats) for ENF analysis.")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format (default: text).")
    parser.add_argument("--json", action="store_true", help="Output result as formatted JSON (shorthand for --format json).")
    parser.add_argument("--output", "-o", metavar="FILE", help="Output file to write results.")

    return parser


def run_interactive():
    print("=" * 72)
    print("  ACOUSTIC SIDE-CHANNEL & KEYSTROKE CRYPTANALYSIS CONSOLE")
    print("=" * 72)
    print("1. Simulate typed password / text timing attack")
    print("2. Acoustic TDOA keystroke triangulation")
    print("3. Power Hum / ENF grid frequency analysis")
    print("4. Exit")
    print("-" * 72)

    choice = input("Select an option [1-4]: ").strip()
    if choice == "1":
        text = input("Enter simulated keystrokes (e.g. 'password'): ").strip() or "password"
        # Generate representative typing events
        events = []
        cur_t = 0.0
        for ch in text:
            dwell = 75.0 + (ord(ch) % 15)
            events.append(KeystrokeEvent(key_code=ch, press_time_ms=cur_t, release_time_ms=cur_t + dwell))
            cur_t += dwell + (120.0 + (ord(ch) % 25))

        analyzer = KeystrokeDynamicsAnalyzer()
        profile = analyzer.extract_profile(events, "interactive_user")
        builder = DigraphFingerprintBuilder()
        fps = builder.build_fingerprints(profile)

        print("\nExtracted Typing Profile:")
        print(f"  Typing Speed:     {profile.typing_speed_cpm} CPM")
        print(f"  Mean IKI:         {profile.mean_iki} ms (std: {profile.std_iki} ms)")
        print(f"  Mean Dwell:       {profile.mean_dwell} ms (std: {profile.std_dwell} ms)")
        print(f"  Rhythm Regularity:{profile.rhythm_regularity}")
        print(f"  Digraphs Extracted: {len(fps)}")
        for fp in fps[:5]:
            print(f"    Digraph '{fp.digraph}': {fp.mean_ms} ms (uniqueness: {fp.uniqueness_score})")

    elif choice == "2":
        delays_input = input("Enter microphone arrival delays in ms (e.g. 0.25 -0.15): ").strip()
        delays = [float(x) for x in delays_input.split()] if delays_input else [0.25, -0.15]
        localizer = TDOAKeyboardLocalizer()
        res = localizer.triangulate(delays)
        print("\nTDOA Localization Result:")
        print(f"  Estimated Position: ({res.estimated_x_cm} cm, {res.estimated_y_cm} cm)")
        print(f"  Nearest Key:        '{res.nearest_key}'")
        print(f"  Residual Error:     {res.residual_error_cm} cm")
        print(f"  Confidence:         {res.confidence}")

    elif choice == "3":
        grid_input = input("Test frequency [50 or 60 Hz, default 60]: ").strip()
        target_hz = float(grid_input) if grid_input in ("50", "60") else 60.0
        sr = 44100
        n_samples = 44100  # 1 second
        # Generate synthetic tone with power hum harmonic
        samples = [
            0.5 * math.sin(2.0 * math.pi * target_hz * i / sr) +
            0.2 * math.sin(2.0 * math.pi * (target_hz * 2) * i / sr)
            for i in range(n_samples)
        ]
        analyzer = PowerHumSpectralAnalyzer()
        res = analyzer.analyze(samples, sr)
        print("\nPower Hum / ENF Analysis:")
        print(f"  Fundamental Freq:   {res.fundamental_freq_hz} Hz")
        print(f"  Grid Standard:      {res.grid_standard}")
        print(f"  Harmonics:          {res.harmonics} Hz")
        print(f"  Confidence:         {res.confidence}")
    print("=" * 72)


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.json:
        args.format = "json"

    if args.interactive or (not args.analyze_timing and not args.tdoa and not args.enf and not args.enroll and not args.authenticate):
        if len(sys.argv) == 1 or args.interactive:
            run_interactive()
            return 0
        parser.print_help()
        return 1

    result_data = {}
    output_text = ""

    try:
        if args.analyze_timing:
            events = load_keystrokes_from_file(args.analyze_timing)
            analyzer = KeystrokeDynamicsAnalyzer()
            profile = analyzer.extract_profile(events, args.user_id)
            builder = DigraphFingerprintBuilder()
            fps = builder.build_fingerprints(profile)

            result_data = {
                "user_id": profile.user_id,
                "typing_speed_cpm": profile.typing_speed_cpm,
                "mean_iki_ms": profile.mean_iki,
                "std_iki_ms": profile.std_iki,
                "mean_dwell_ms": profile.mean_dwell,
                "std_dwell_ms": profile.std_dwell,
                "rhythm_regularity": profile.rhythm_regularity,
                "digraph_fingerprints": [fp.__dict__ for fp in fps],
            }

            output_text = (
                f"Keystroke Timing Analysis for User: {profile.user_id}\n"
                f"  Speed:             {profile.typing_speed_cpm} CPM\n"
                f"  Mean IKI:          {profile.mean_iki} ms (±{profile.std_iki} ms)\n"
                f"  Mean Dwell Time:   {profile.mean_dwell} ms (±{profile.std_dwell} ms)\n"
                f"  Rhythm Regularity: {profile.rhythm_regularity}\n"
                f"  Digraph Fingerprints: {len(fps)} unique patterns extracted\n"
            )

        elif args.tdoa:
            localizer = TDOAKeyboardLocalizer()
            res = localizer.triangulate(args.tdoa)
            result_data = res.__dict__
            output_text = (
                f"Acoustic Keystroke Triangulation (TDOA):\n"
                f"  Estimated Position: ({res.estimated_x_cm} cm, {res.estimated_y_cm} cm)\n"
                f"  Nearest Key:        '{res.nearest_key}'\n"
                f"  Residual Error:     {res.residual_error_cm} cm\n"
                f"  Confidence:         {res.confidence}\n"
            )

        elif args.enf:
            analyzer = PowerHumSpectralAnalyzer()
            sr = 44100
            if args.audio_file:
                audio_path = _validate_file_path(args.audio_file)
                samples = json.loads(audio_path.read_text(encoding="utf-8"))
                if not isinstance(samples, list):
                    raise ValueError("Audio file must contain a list of numeric samples")
            else:
                # Synthetic ENF test signal
                samples = [
                    0.6 * math.sin(2.0 * math.pi * args.enf_hz * i / sr) +
                    0.25 * math.sin(2.0 * math.pi * (args.enf_hz * 2) * i / sr)
                    for i in range(sr)
                ]
            res = analyzer.analyze(samples, sr)
            result_data = res.__dict__
            output_text = (
                f"Electric Network Frequency (ENF) Spectral Analysis:\n"
                f"  Fundamental Freq:   {res.fundamental_freq_hz} Hz\n"
                f"  Grid Standard:      {res.grid_standard}\n"
                f"  Device Signature:   {res.device_signature}\n"
                f"  Detected Harmonics: {res.harmonics}\n"
                f"  Confidence:         {res.confidence}\n"
            )

        elif args.enroll:
            events = load_keystrokes_from_file(args.enroll)
            engine = KeystrokeAuthenticationEngine()
            profile = engine.enroll(args.user_id, events)
            result_data = {
                "enrolled_user": args.user_id,
                "events_count": len(events),
                "profile": profile.__dict__,
            }
            output_text = (
                f"User Successfully Enrolled: {args.user_id}\n"
                f"  Total Keystrokes:  {len(events)}\n"
                f"  Typing Speed:      {profile.typing_speed_cpm} CPM\n"
                f"  Mean IKI:          {profile.mean_iki} ms\n"
            )

        elif args.authenticate:
            if not args.ref_file:
                print("Error: --ref-file required for candidate authentication.", file=sys.stderr)
                return 1
            ref_events = load_keystrokes_from_file(args.ref_file)
            cand_events = load_keystrokes_from_file(args.authenticate)
            engine = KeystrokeAuthenticationEngine()
            engine.enroll(args.user_id, ref_events)
            auth_res = engine.authenticate(cand_events, threshold=args.threshold)
            result_data = auth_res
            output_text = (
                f"Biometric Keystroke Authentication:\n"
                f"  Authenticated:     {auth_res['authenticated']}\n"
                f"  Best Match User:   {auth_res['best_match_user']}\n"
                f"  Similarity Score:  {auth_res['best_match_score']} (Threshold: {auth_res['threshold']})\n"
            )
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if args.format == "json":
        final_str = json.dumps(result_data, indent=2)
    else:
        final_str = output_text

    if args.output:
        Path(args.output).write_text(final_str, encoding="utf-8")
    else:
        print(final_str)

    return 0


if __name__ == "__main__":
    sys.exit(main())
