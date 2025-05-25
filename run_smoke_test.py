#!/usr/bin/env python3
"""
Smoke Test Runner

Simple wrapper script to run comprehensive smoke tests for the Audio Visualizer Suite.
This script will:
1. Prepare test media if needed
2. Run smoke tests for all visualizers
3. Generate a summary report

Usage:
    python3 run_smoke_test.py [options]

Options:
    --quick         Run very quick tests (1 second duration) [default]
    --full          Run longer tests (3 seconds duration)
    --prepare-only  Only prepare test media, don't run tests
    --clean         Clean previous test results before running
"""

import os
import sys
import argparse
import shutil
from pathlib import Path

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from prepare_test_media import MediaPreparator
from comprehensive_smoke_test import SmokeTestRunner

def clean_previous_results():
    """Clean previous test results."""
    test_dir = Path("smoketest")
    if test_dir.exists():
        print("Cleaning previous test results...")
        shutil.rmtree(test_dir)
        print("Previous results cleaned.")

def main():
    parser = argparse.ArgumentParser(description="Run smoke tests for Audio Visualizer Suite")
    parser.add_argument("--quick", action="store_true", help="Run very quick tests (1 second)")
    parser.add_argument("--full", action="store_true", help="Run longer tests (3 seconds)")
    parser.add_argument("--prepare-only", action="store_true", help="Only prepare test media")
    parser.add_argument("--clean", action="store_true", help="Clean previous results")

    args = parser.parse_args()

    # Clean if requested
    if args.clean:
        clean_previous_results()

    # Prepare test media
    print("=" * 60)
    print("PREPARING TEST MEDIA")
    print("=" * 60)

    preparator = MediaPreparator()
    if not preparator.prepare_all_media():
        print("Failed to prepare test media!")
        return 1

    if args.prepare_only:
        print("Test media preparation complete. Exiting.")
        return 0

    # Run smoke tests
    print("\n" + "=" * 60)
    print("RUNNING SMOKE TESTS")
    print("=" * 60)

    runner = SmokeTestRunner()

    # Set test duration based on arguments
    if args.full:
        runner.test_duration = 3
        print("Running longer tests (3 seconds per test)")
    else:
        runner.test_duration = 1
        print("Running quick tests (1 second per test)")

    try:
        success = runner.run_all_tests()

        print("\n" + "=" * 60)
        print("SMOKE TEST COMPLETE")
        print("=" * 60)

        if success:
            print("✓ All smoke tests passed!")
            print(f"Results saved to: {runner.results_dir}")
            return 0
        else:
            print("✗ Some smoke tests failed!")
            print(f"Check results in: {runner.results_dir}")
            print(f"See report: {runner.test_dir}/smoke_test_report.txt")
            return 1

    except KeyboardInterrupt:
        print("\nSmoke test interrupted by user")
        return 1
    except Exception as e:
        print(f"Smoke test failed with error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
