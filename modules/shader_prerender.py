"""
Shader pre-rendering module for Audio Visualizer Suite.
This module pre-renders shader animations as video files.
"""
import os
import sys
import time
import tempfile
import subprocess
from pathlib import Path
import numpy as np
import logging
from .progress_tracker import ProgressTracker

logger = logging.getLogger('audio_visualizer.shader_prerender')

def prerender_shader_background(shader_path, output_path, duration, fps, width, height, progress_callback=None):
    """
    Pre-render a shader animation as a video file.

    Args:
        shader_path (str): Path to the shader file
        output_path (str): Path to save the rendered video
        duration (float): Duration of the video in seconds
        fps (int): Frames per second
        width (int): Width of the video
        height (int): Height of the video
        progress_callback (callable, optional): Callback function for progress updates

    Returns:
        str: Path to the rendered video file, or None if rendering failed
    """
    try:
        # Initialize progress tracker with custom stages for shader pre-rendering
        shader_stages = {
            "setup": 10,
            "rendering": 80,
            "finalization": 10
        }
        progress = ProgressTracker(stages=shader_stages, callback=progress_callback)

        # Start setup stage
        progress.start_stage("setup", f"Setting up shader pre-rendering for {os.path.basename(shader_path)}...")

        logger.info(f"Pre-rendering shader background: {shader_path}")
        logger.info(f"Duration: {duration}s, FPS: {fps}, Resolution: {width}x{height}")

        # Calculate the number of frames
        total_frames = int(duration * fps)
        logger.info(f"Total frames to render: {total_frames}")

        # Build the FFmpeg command
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",  # Overwrite output file if it exists
            "-f", "rawvideo",
            "-vcodec", "rawvideo",
            "-s", f"{width}x{height}",
            "-pix_fmt", "rgba",
            "-r", str(fps),
            "-i", "-",  # Read from stdin
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            output_path
        ]

        # Start the FFmpeg process
        logger.info("Starting FFmpeg process...")
        progress.update_stage_progress(30, "Starting FFmpeg process...")
        ffmpeg_process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Import the shader module dynamically
        logger.info("Importing shader module...")
        progress.update_stage_progress(50, "Loading shader module...")
        sys.path.append(os.path.dirname(os.path.abspath(shader_path)))
        from glsl.shader import ShaderRenderer

        # Create the renderer
        logger.info(f"Creating shader renderer for {shader_path}...")
        progress.update_stage_progress(70, "Initializing shader renderer...")
        renderer = ShaderRenderer(shader_path, width, height)

        # Complete setup stage
        progress.complete_stage("Shader setup complete")

        # Start rendering stage
        progress.start_stage("rendering", f"Rendering {total_frames} frames...")

        # Render each frame and pipe it to FFmpeg
        logger.info("Rendering frames...")
        start_time = time.time()

        # Use tqdm for progress tracking if available
        try:
            from tqdm import tqdm
            frame_range = tqdm(range(total_frames), desc="Pre-rendering shader")
        except ImportError:
            frame_range = range(total_frames)

        # Track the last progress update time to avoid too frequent updates
        last_update_time = time.time()
        update_interval = 0.5  # Update progress every 0.5 seconds

        for frame_idx in frame_range:
            # Calculate the time for this frame
            frame_time = frame_idx / fps

            # Render the frame
            if frame_idx % 10 == 0 or frame_idx == total_frames - 1:
                logger.info(f"Rendering frame {frame_idx+1}/{total_frames} at time {frame_time:.2f}s")

            # Update progress if callback is provided - limit updates to avoid overwhelming the UI
            current_time = time.time()
            if current_time - last_update_time >= update_interval or frame_idx == total_frames - 1:
                progress_percent = (frame_idx + 1) / total_frames * 100
                message = f"Rendering shader frame {frame_idx+1}/{total_frames}"
                progress.update_stage_progress(progress_percent, message)
                last_update_time = current_time

            # Render the frame
            frame = renderer.render_frame(frame_time)

            # Convert the PIL image to raw bytes
            frame_data = frame.tobytes()

            # Write the frame data to FFmpeg's stdin
            ffmpeg_process.stdin.write(frame_data)

        # Complete rendering stage
        progress.complete_stage("Shader rendering complete")

        # Start finalization stage
        progress.start_stage("finalization", "Finalizing shader video...")

        # Close FFmpeg's stdin to signal the end of input
        try:
            progress.update_stage_progress(30, "Finalizing FFmpeg encoding...")
            ffmpeg_process.stdin.close()
        except:
            logger.warning("Warning: FFmpeg stdin already closed")

        # Wait for FFmpeg to finish
        try:
            progress.update_stage_progress(60, "Waiting for video encoding to complete...")
            stdout, stderr = ffmpeg_process.communicate()
        except ValueError:
            # This can happen if stdin is already closed
            logger.warning("Warning: FFmpeg stdin already closed")
            # Wait for the process to finish
            ffmpeg_process.wait()

        # Check if FFmpeg was successful
        if ffmpeg_process.returncode != 0:
            error_msg = stderr.decode() if 'stderr' in locals() else 'Unknown error'
            logger.error(f"FFmpeg error: {error_msg}")
            progress.update_stage_progress(100, "Error: FFmpeg encoding failed")
            return None

        # Calculate the rendering time
        end_time = time.time()
        render_time = end_time - start_time
        fps_rate = total_frames / render_time

        logger.info(f"Shader background pre-rendering completed in {render_time:.2f} seconds")
        logger.info(f"Average rendering speed: {fps_rate:.2f} fps")

        # Clean up
        progress.update_stage_progress(90, "Cleaning up resources...")
        renderer.cleanup()

        # Complete finalization stage
        progress.complete_stage("Shader pre-rendering complete")

        return output_path

    except Exception as e:
        logger.error(f"Error pre-rendering shader background: {e}")
        import traceback
        traceback.print_exc()

        # If we have a progress tracker, update it with the error
        if 'progress' in locals():
            try:
                progress.update_stage_progress(100, f"Error: {str(e)}")
            except:
                pass

        return None


if __name__ == "__main__":
    # This can be used as a standalone script for testing
    import argparse

    parser = argparse.ArgumentParser(description="Pre-render a shader animation as a video file")
    parser.add_argument("--shader", required=True, help="Path to the shader file")
    parser.add_argument("--output", required=True, help="Path to save the rendered video")
    parser.add_argument("--duration", type=float, default=10.0, help="Duration of the video in seconds")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second")
    parser.add_argument("--width", type=int, default=1280, help="Width of the video")
    parser.add_argument("--height", type=int, default=720, help="Height of the video")

    args = parser.parse_args()

    prerender_shader_background(
        args.shader,
        args.output,
        args.duration,
        args.fps,
        args.width,
        args.height
    )
