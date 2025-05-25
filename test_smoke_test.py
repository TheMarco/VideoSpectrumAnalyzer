#!/usr/bin/env python3
"""
Simple test to verify smoke test functionality works.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from comprehensive_smoke_test import SmokeTestRunner
from core.registry import registry

def test_single_visualizer():
    """Test a single visualizer with minimal configuration."""
    print("Testing single visualizer...")

    runner = SmokeTestRunner()
    runner.test_duration = 1  # Very short test

    # Setup
    if not runner.setup_directories():
        print("Failed to setup directories")
        return False

    if not runner.prepare_test_media():
        print("Failed to prepare test media")
        return False

    # Get available visualizers
    registry.discover_visualizers()
    viz_names = registry.get_visualizer_names()

    if not viz_names:
        print("No visualizers available")
        return False

    print(f"Available visualizers: {viz_names}")

    # Test the first visualizer with a simple config
    test_config = {
        'name': 'simple_test',
        'description': 'Simple test',
        'artist_track': False
    }

    viz_name = viz_names[0]
    print(f"Testing {viz_name}...")

    result = runner.run_visualizer_test(viz_name, test_config)

    if result:
        print(f"✓ Test passed for {viz_name}")

        # Check if output file exists
        safe_viz_name = viz_name.replace(" ", "_").lower()
        output_file = runner.results_dir / safe_viz_name / f"{test_config['name']}.mp4"

        if output_file.exists():
            file_size = output_file.stat().st_size
            print(f"✓ Output file exists: {output_file} ({file_size} bytes)")
            return True
        else:
            print(f"✗ Output file missing: {output_file}")
            return False
    else:
        print(f"✗ Test failed for {viz_name}")
        return False

def main():
    """Main test function."""
    print("=" * 50)
    print("SMOKE TEST VERIFICATION")
    print("=" * 50)

    try:
        success = test_single_visualizer()

        if success:
            print("\n✓ Smoke test functionality verified!")
            print("You can now run the full smoke test with:")
            print("  python3 run_smoke_test.py --quick")
            return 0
        else:
            print("\n✗ Smoke test verification failed!")
            return 1

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
