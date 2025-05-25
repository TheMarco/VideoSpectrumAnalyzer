#!/usr/bin/env python3
"""
Test Media Preparation Script

This script prepares sample media files for testing the Audio Visualizer Suite.
It copies existing files from uploads and creates new test media as needed.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MediaPreparator:
    def __init__(self):
        self.test_media_dir = Path("smoketest/media")
        self.uploads_dir = Path("uploads")

    def setup_directories(self):
        """Create necessary directories."""
        self.test_media_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created test media directory: {self.test_media_dir}")

    def copy_existing_audio(self):
        """Copy existing audio files from uploads to test media, or use existing ones."""
        audio_extensions = ['.wav', '.mp3', '.flac', '.m4a']
        copied_files = []

        # First check if we already have test audio files
        for ext in audio_extensions:
            existing_test_file = self.test_media_dir / f"test_audio{ext}"
            if existing_test_file.exists():
                copied_files.append(existing_test_file)
                logger.info(f"Using existing test audio file: {existing_test_file}")
                return copied_files  # Use the first existing one we find

        # If no existing test files, try to copy from uploads
        for ext in audio_extensions:
            audio_files = list(self.uploads_dir.glob(f"*{ext}"))
            if audio_files:
                # Copy the first file of each type
                source = audio_files[0]
                dest = self.test_media_dir / f"test_audio{ext}"
                shutil.copy2(source, dest)
                copied_files.append(dest)
                logger.info(f"Copied audio file: {source} -> {dest}")
                break  # Just need one audio file

        return copied_files

    def copy_existing_video(self):
        """Copy existing video files from uploads to test media, or use existing ones."""
        video_extensions = ['.mp4', '.mov', '.avi', '.webm']
        copied_files = []

        # First check if we already have test video files
        for ext in video_extensions:
            existing_test_file = self.test_media_dir / f"test_background_video{ext}"
            if existing_test_file.exists():
                copied_files.append(existing_test_file)
                logger.info(f"Using existing test video file: {existing_test_file}")
                return copied_files  # Use the first existing one we find

        # If no existing test files, try to copy from uploads
        for ext in video_extensions:
            video_files = list(self.uploads_dir.glob(f"*{ext}"))
            if video_files:
                # Copy the first file
                source = video_files[0]
                dest = self.test_media_dir / f"test_background_video{ext}"
                shutil.copy2(source, dest)
                copied_files.append(dest)
                logger.info(f"Copied video file: {source} -> {dest}")
                break  # Just need one video file

        return copied_files

    def create_test_audio(self):
        """Create a test audio file using ffmpeg."""
        output_path = self.test_media_dir / "generated_test_audio.wav"

        if output_path.exists():
            logger.info(f"Using existing test audio file: {output_path}")
            return str(output_path)

        try:
            # Generate a 30-second test tone with some variation
            cmd = [
                'ffmpeg', '-y',
                '-f', 'lavfi',
                '-i', 'sine=frequency=440:duration=30,sine=frequency=880:duration=30',
                '-filter_complex', '[0:a][1:a]amix=inputs=2:duration=longest',
                '-ar', '44100',
                '-ac', '2',
                str(output_path)
            ]

            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Created test audio: {output_path}")
            return str(output_path)

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create test audio: {e}")
            return None
        except FileNotFoundError:
            logger.error("ffmpeg not found. Please install ffmpeg to generate test audio.")
            return None

    def create_test_images(self):
        """Create test background images."""
        created_files = []

        # Create a simple gradient image
        gradient_path = self.test_media_dir / "test_gradient.png"
        if gradient_path.exists():
            created_files.append(gradient_path)
            logger.info(f"Using existing test gradient image: {gradient_path}")
        else:
            if self._create_gradient_image(gradient_path):
                created_files.append(gradient_path)

        # Create a pattern image
        pattern_path = self.test_media_dir / "test_pattern.png"
        if pattern_path.exists():
            created_files.append(pattern_path)
            logger.info(f"Using existing test pattern image: {pattern_path}")
        else:
            if self._create_pattern_image(pattern_path):
                created_files.append(pattern_path)

        return created_files

    def _create_gradient_image(self, path):
        """Create a gradient background image."""
        try:
            from PIL import Image, ImageDraw

            width, height = 1920, 1080
            img = Image.new('RGB', (width, height))
            draw = ImageDraw.Draw(img)

            # Create a radial gradient
            center_x, center_y = width // 2, height // 2
            max_radius = min(center_x, center_y)

            for y in range(height):
                for x in range(width):
                    # Calculate distance from center
                    distance = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                    # Normalize distance
                    normalized = min(distance / max_radius, 1.0)

                    # Create color based on distance
                    r = int(255 * (1 - normalized))
                    g = int(128 * normalized)
                    b = int(255 * normalized)

                    img.putpixel((x, y), (r, g, b))

            img.save(path)
            logger.info(f"Created gradient image: {path}")
            return True

        except ImportError:
            logger.error("PIL not available. Cannot create test images.")
            return False
        except Exception as e:
            logger.error(f"Failed to create gradient image: {e}")
            return False

    def _create_pattern_image(self, path):
        """Create a pattern background image."""
        try:
            from PIL import Image, ImageDraw

            width, height = 1920, 1080
            img = Image.new('RGB', (width, height), color='black')
            draw = ImageDraw.Draw(img)

            # Create a geometric pattern
            colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]

            # Draw rectangles in a grid pattern
            rect_width = width // 10
            rect_height = height // 6

            for i in range(10):
                for j in range(6):
                    x1 = i * rect_width
                    y1 = j * rect_height
                    x2 = x1 + rect_width
                    y2 = y1 + rect_height

                    color = colors[(i + j) % len(colors)]
                    draw.rectangle([x1, y1, x2, y2], fill=color)

            img.save(path)
            logger.info(f"Created pattern image: {path}")
            return True

        except ImportError:
            logger.error("PIL not available. Cannot create test images.")
            return False
        except Exception as e:
            logger.error(f"Failed to create pattern image: {e}")
            return False

    def create_test_video(self):
        """Create a test background video."""
        output_path = self.test_media_dir / "test_background_video.mp4"

        if output_path.exists():
            logger.info(f"Using existing test video file: {output_path}")
            return str(output_path)

        try:
            # Create a colorful test pattern video
            cmd = [
                'ffmpeg', '-y',
                '-f', 'lavfi',
                '-i', 'testsrc2=duration=30:size=1920x1080:rate=30',
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-crf', '23',
                str(output_path)
            ]

            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"Created test video: {output_path}")
            return str(output_path)

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create test video: {e}")
            return None
        except FileNotFoundError:
            logger.error("ffmpeg not found. Please install ffmpeg to generate test video.")
            return None

    def prepare_all_media(self):
        """Prepare all test media files."""
        logger.info("Preparing test media files...")

        self.setup_directories()

        # Copy existing files
        audio_files = self.copy_existing_audio()
        video_files = self.copy_existing_video()

        # Create new files if needed
        if not audio_files:
            generated_audio = self.create_test_audio()
            if generated_audio:
                audio_files.append(generated_audio)

        if not video_files:
            generated_video = self.create_test_video()
            if generated_video:
                video_files.append(generated_video)

        image_files = self.create_test_images()

        # Summary
        logger.info("\nTest media preparation complete:")
        logger.info(f"Audio files: {len(audio_files)}")
        for f in audio_files:
            logger.info(f"  - {f}")

        logger.info(f"Video files: {len(video_files)}")
        for f in video_files:
            logger.info(f"  - {f}")

        logger.info(f"Image files: {len(image_files)}")
        for f in image_files:
            logger.info(f"  - {f}")

        return len(audio_files) > 0 and len(image_files) > 0


def main():
    """Main entry point."""
    preparator = MediaPreparator()

    try:
        success = preparator.prepare_all_media()
        if success:
            logger.info("Test media preparation completed successfully!")
            return 0
        else:
            logger.error("Test media preparation failed!")
            return 1
    except Exception as e:
        logger.error(f"Test media preparation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
