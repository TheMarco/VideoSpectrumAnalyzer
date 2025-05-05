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
        print(f"Pre-rendering shader background: {shader_path}")
        print(f"Duration: {duration}s, FPS: {fps}, Resolution: {width}x{height}")

        # Calculate the number of frames
        total_frames = int(duration * fps)
        print(f"Total frames to render: {total_frames}")

        # If progress_callback is provided, send an initial progress update
        if progress_callback:
            try:
                progress_callback(1, f"Starting shader pre-rendering ({total_frames} frames)...")
            except Exception as e:
                print(f"Error in progress callback: {e}")

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
        print("Starting FFmpeg process...")
        ffmpeg_process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Import the shader module dynamically
        print("Importing shader module...")
        sys.path.append(os.path.dirname(os.path.abspath(shader_path)))
        from glsl.shader import ShaderRenderer

        # Create the renderer
        print(f"Creating shader renderer for {shader_path}...")
        renderer = ShaderRenderer(shader_path, width, height)

        # Render each frame and pipe it to FFmpeg
        print("Rendering frames...")
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
                print(f"Rendering frame {frame_idx+1}/{total_frames} at time {frame_time:.2f}s")

            # Update progress if callback is provided - limit updates to avoid overwhelming the UI
            current_time = time.time()
            if progress_callback and (current_time - last_update_time >= update_interval or frame_idx == total_frames - 1):
                # Calculate progress percentage (0-100)
                # We'll allocate 0-20% of the overall progress to shader pre-rendering
                progress_percent = int(20 * (frame_idx + 1) / total_frames)
                progress_message = f"Pre-rendering shader background: {frame_idx+1}/{total_frames} frames"
                print(f"Updating progress: {progress_percent}%, {progress_message}")

                try:
                    progress_callback(progress_percent, progress_message)
                    last_update_time = current_time
                except Exception as e:
                    print(f"Error in progress callback: {e}")

            # Render the frame
            frame = renderer.render_frame(frame_time)

            # Convert the PIL image to raw bytes
            frame_data = frame.tobytes()

            # Write the frame data to FFmpeg's stdin
            ffmpeg_process.stdin.write(frame_data)

        # Close FFmpeg's stdin to signal the end of input
        try:
            ffmpeg_process.stdin.close()
        except:
            print("Warning: FFmpeg stdin already closed")

        # Wait for FFmpeg to finish
        try:
            stdout, stderr = ffmpeg_process.communicate()
        except ValueError:
            # This can happen if stdin is already closed
            print("Warning: FFmpeg stdin already closed")
            # Wait for the process to finish
            ffmpeg_process.wait()

        # Check if FFmpeg was successful
        if ffmpeg_process.returncode != 0:
            error_msg = stderr.decode() if 'stderr' in locals() else 'Unknown error'
            print(f"FFmpeg error: {error_msg}")
            return None

        # Calculate the rendering time
        end_time = time.time()
        render_time = end_time - start_time
        fps_rate = total_frames / render_time

        print(f"Shader background pre-rendering completed in {render_time:.2f} seconds")
        print(f"Average rendering speed: {fps_rate:.2f} fps")

        # Clean up
        renderer.cleanup()

        # Final progress update
        if progress_callback:
            try:
                progress_callback(20, "Shader pre-rendering complete")
            except Exception as e:
                print(f"Error in final progress callback: {e}")

        return output_path

    except Exception as e:
        print(f"Error pre-rendering shader background: {e}")
        import traceback
        traceback.print_exc()
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
