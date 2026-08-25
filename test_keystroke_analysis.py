"""
Entry point test runner for Acoustic Side-Channel Keystroke & ENF Cryptanalysis.
"""

import sys
import unittest
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, str(Path(__file__).parent))

from tests.test_acoustic_side_channel import (
    TestKeystrokeDynamics,
    TestDigraphFingerprints,
    TestProfileComparison,
    TestTDOALocalizer,
    TestPowerHumAnalyzer,
    TestKeystrokeAuthenticationEngine,
    TestCLIAndFileIO,
)

if __name__ == "__main__":
    unittest.main()
