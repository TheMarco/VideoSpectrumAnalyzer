#!/usr/bin/env python3
"""
Comprehensive Smoke Test for Audio Visualizer Suite

This script tests all available visualizers with different configurations:
- Plain (no background)
- With background image
- With background video
- With background shader
- With artist/track info enabled

Results are saved to smoketest/ directory with organized subdirectories.
"""

import os
import sys
import shutil
import time
import glob
from pathlib import Path
import logging

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.registry import registry

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SmokeTestRunner:
    def __init__(self):
        self.test_dir = Path("smoketest")
        self.media_dir = self.test_dir / "media"
        self.results_dir = self.test_dir / "results"

        # Test parameters
        self.test_duration = 1  # seconds - short duration for quick smoke tests
        self.test_fps = 30
        self.test_width = 1280
        self.test_height = 720

        # Media files to use for testing
        self.test_audio = None
        self.test_image = None
        self.test_video = None
        self.test_shaders = []

    def setup_directories(self):
        """Create necessary directories for the smoke test."""
        logger.info("Setting up test directories...")

        try:
            # Create main directories
            self.test_dir.mkdir(exist_ok=True)
            self.media_dir.mkdir(exist_ok=True)
            self.results_dir.mkdir(exist_ok=True)

            # Create subdirectories for each visualizer
            registry.discover_visualizers()
            for viz_name in registry.get_visualizer_names():
                viz_dir = self.results_dir / viz_name.replace(" ", "_").lower()
                viz_dir.mkdir(exist_ok=True)

            return True
        except Exception as e:
            logger.error(f"Failed to setup directories: {e}")
            return False

    def prepare_test_media(self):
        """Prepare or copy test media files."""
        logger.info("Preparing test media...")

        # First try to prepare media using the media preparator
        try:
            from prepare_test_media import MediaPreparator
            preparator = MediaPreparator()
            success = preparator.prepare_all_media()
            if not success:
                logger.warning("Media preparation had some issues, but continuing...")
        except Exception as e:
            logger.warning(f"Media preparation failed: {e}, but continuing...")

        # Find audio files - check smoketest/media first, then uploads
        audio_extensions = ['*.wav', '*.mp3', '*.flac', '*.m4a']
        audio_files = []

        # Check smoketest/media first
        for ext in audio_extensions:
            audio_files.extend(list(self.media_dir.glob(ext)))

        # If not found, check uploads
        if not audio_files:
            for ext in audio_extensions:
                audio_files.extend(list(Path("uploads").glob(ext)))

        if audio_files:
            self.test_audio = str(audio_files[0])
            logger.info(f"Using audio file: {self.test_audio}")
        else:
            logger.error("No audio files found in smoketest/media or uploads directory!")
            return False

        # Find test image - check smoketest/media first
        test_image_path = self.media_dir / "test_background.png"
        existing_images = list(self.media_dir.glob("*.png")) + list(self.media_dir.glob("*.jpg"))

        if existing_images:
            self.test_image = str(existing_images[0])
            logger.info(f"Using existing test image: {self.test_image}")
        elif not test_image_path.exists():
            self._create_test_image(test_image_path)
            self.test_image = str(test_image_path)
        else:
            self.test_image = str(test_image_path)

        # Find video files - check smoketest/media first, then uploads
        video_extensions = ['*.mp4', '*.mov', '*.avi', '*.webm']
        video_files = []

        # Check smoketest/media first
        for ext in video_extensions:
            video_files.extend(list(self.media_dir.glob(ext)))

        # If not found, check uploads
        if not video_files:
            for ext in video_extensions:
                video_files.extend(list(Path("uploads").glob(ext)))

        if video_files:
            self.test_video = str(video_files[0])
            logger.info(f"Using video file: {self.test_video}")
        else:
            # Create a simple test video
            test_video_path = self.media_dir / "test_background.mp4"
            if not test_video_path.exists():
                self._create_test_video(test_video_path)
            self.test_video = str(test_video_path)

        # Get available shaders
        self.test_shaders = self._get_test_shaders()

        return True

    def _create_test_image(self, path):
        """Create a simple test background image."""
        try:
            from PIL import Image, ImageDraw

            # Create a gradient image
            img = Image.new('RGB', (1280, 720), color='black')
            draw = ImageDraw.Draw(img)

            # Draw some simple patterns
            for i in range(0, 1280, 50):
                color = (i // 10 % 255, 100, 200)
                draw.rectangle([i, 0, i+25, 720], fill=color)

            img.save(path)
            logger.info(f"Created test image: {path}")
        except Exception as e:
            logger.error(f"Failed to create test image: {e}")

    def _create_test_video(self, path):
        """Create a simple test background video."""
        try:
            import subprocess

            # Create a simple colored video using ffmpeg
            cmd = [
                'ffmpeg', '-y',
                '-f', 'lavfi',
                '-i', 'testsrc=duration=15:size=1280x720:rate=30',
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                str(path)
            ]

            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Created test video: {path}")
        except Exception as e:
            logger.error(f"Failed to create test video: {e}")

    def _get_test_shaders(self):
        """Get a list of shaders to test."""
        shader_files = glob.glob("glsl/*.glsl")
        # Filter out audio-reactive shaders and problematic ones
        test_shaders = []
        for shader in shader_files:
            shader_name = os.path.basename(shader)
            # Skip audio-reactive shaders and known problematic ones
            if not shader_name.startswith('ar_') and 'broken' not in shader_name.lower():
                test_shaders.append(shader)

        # Limit to a few shaders for smoke test
        return test_shaders[:3]  # Just test first 3 shaders

    def run_visualizer_test(self, visualizer_name, test_config):
        """Run a single test configuration for a visualizer."""
        try:
            visualizer = registry.get_visualizer(visualizer_name)
            if not visualizer:
                logger.error(f"Visualizer {visualizer_name} not found")
                return False

            # Create output filename
            config_name = test_config['name']
            safe_viz_name = visualizer_name.replace(" ", "_").lower()
            output_file = self.results_dir / safe_viz_name / f"{config_name}.mp4"

            logger.info(f"Testing {visualizer_name} - {config_name}")

            # Prepare configuration
            config = {
                'duration': self.test_duration,
                'fps': self.test_fps,
                'width': self.test_width,
                'height': self.test_height,
            }

            # Add test-specific config
            if test_config.get('artist_track'):
                config['artist_name'] = "Test Artist"
                config['track_title'] = "Test Track"
            else:
                config['artist_name'] = ""
                config['track_title'] = ""

            # Run the visualization
            start_time = time.time()

            visualizer.create_visualization(
                audio_file=self.test_audio,
                output_file=str(output_file),
                background_image_path=test_config.get('background_image'),
                background_video_path=test_config.get('background_video'),
                background_shader_path=test_config.get('background_shader'),
                artist_name=config.get('artist_name', ''),
                track_title=config.get('track_title', ''),
                duration=config['duration'],
                fps=config['fps'],
                width=config['width'],
                height=config['height'],
                config=config
            )

            end_time = time.time()
            duration = end_time - start_time

            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                logger.info(f"✓ {visualizer_name} - {config_name} completed in {duration:.1f}s (size: {file_size/1024/1024:.1f}MB)")
                return True
            else:
                logger.error(f"✗ {visualizer_name} - {config_name} failed - no output file")
                return False

        except Exception as e:
            logger.error(f"✗ {visualizer_name} - {config_name} failed: {e}")
            return False

    def run_all_tests(self):
        """Run all smoke tests for all visualizers."""
        logger.info("Starting comprehensive smoke test...")

        # Setup
        if not self.setup_directories():
            return False

        if not self.prepare_test_media():
            return False

        # Discover visualizers
        registry.discover_visualizers()
        visualizer_names = registry.get_visualizer_names()

        if not visualizer_names:
            logger.error("No visualizers found!")
            return False

        logger.info(f"Found {len(visualizer_names)} visualizers: {visualizer_names}")

        # Define test configurations
        test_configs = [
            {
                'name': 'plain',
                'description': 'Plain visualization (no background)',
                'artist_track': False
            },
            {
                'name': 'with_image',
                'description': 'With background image',
                'background_image': self.test_image,
                'artist_track': False
            },
            {
                'name': 'with_video',
                'description': 'With background video',
                'background_video': self.test_video,
                'artist_track': False
            },
            {
                'name': 'with_artist_track',
                'description': 'With artist and track info',
                'artist_track': True
            },
            {
                'name': 'with_image_and_text',
                'description': 'With background image and artist/track info',
                'background_image': self.test_image,
                'artist_track': True
            }
        ]

        # Add shader tests if shaders are available
        for i, shader in enumerate(self.test_shaders):
            shader_name = os.path.basename(shader).replace('.glsl', '')
            test_configs.append({
                'name': f'with_shader_{shader_name}',
                'description': f'With background shader: {shader_name}',
                'background_shader': shader,
                'artist_track': False
            })

        # Run tests
        total_tests = len(visualizer_names) * len(test_configs)
        current_test = 0
        passed_tests = 0
        failed_tests = 0

        results = {}

        for viz_name in visualizer_names:
            logger.info(f"\n{'='*60}")
            logger.info(f"Testing visualizer: {viz_name}")
            logger.info(f"{'='*60}")

            results[viz_name] = {}

            for config in test_configs:
                current_test += 1
                logger.info(f"[{current_test}/{total_tests}] {config['description']}")

                success = self.run_visualizer_test(viz_name, config)
                results[viz_name][config['name']] = success

                if success:
                    passed_tests += 1
                else:
                    failed_tests += 1

        # Generate summary report
        self._generate_report(results, passed_tests, failed_tests, total_tests)

        return failed_tests == 0

    def _generate_report(self, results, passed, failed, total):
        """Generate a summary report of the test results."""
        report_path = self.test_dir / "smoke_test_report.txt"

        with open(report_path, 'w') as f:
            f.write("Audio Visualizer Suite - Smoke Test Report\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Test Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Tests: {total}\n")
            f.write(f"Passed: {passed}\n")
            f.write(f"Failed: {failed}\n")
            f.write(f"Success Rate: {(passed/total)*100:.1f}%\n\n")

            f.write("Detailed Results:\n")
            f.write("-" * 30 + "\n")

            for viz_name, viz_results in results.items():
                f.write(f"\n{viz_name}:\n")
                for test_name, success in viz_results.items():
                    status = "PASS" if success else "FAIL"
                    f.write(f"  {test_name}: {status}\n")

        logger.info(f"\nTest Summary:")
        logger.info(f"Total: {total}, Passed: {passed}, Failed: {failed}")
        logger.info(f"Success Rate: {(passed/total)*100:.1f}%")
        logger.info(f"Report saved to: {report_path}")


def main():
    """Main entry point for the smoke test."""
    runner = SmokeTestRunner()

    try:
        success = runner.run_all_tests()
        if success:
            logger.info("All smoke tests passed!")
            return 0
        else:
            logger.error("Some smoke tests failed!")
            return 1
    except KeyboardInterrupt:
        logger.info("Smoke test interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Smoke test failed with error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
