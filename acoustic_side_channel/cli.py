"""
CLI entry point for the acoustic_side_channel package.

This module exposes the CLI main function at the package level so that
the console_scripts entry point declared in pyproject.toml works correctly.
"""

from cli import main

__all__ = ["main"]
