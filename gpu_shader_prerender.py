#!/usr/bin/env python3
import os
import sys
import time
import argparse
import subprocess
from tqdm import tqdm

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the original GPU-accelerated shader renderer
from glsl.shader import ShaderRenderer

def prerender_shader_to_video(shader_path, output_path, duration=10.0, fps=30, width=1280, height=720):
    """
    Pre-render a shader animation as a video file using GPU acceleration.

    Args:
        shader_path (str): Path to the shader file
        output_path (str): Path to save the rendered video
        duration (float): Duration of the video in seconds
        fps (int): Frames per second
        width (int): Width of the video
        height (int): Height of the video

    Returns:
        str: Path to the rendered video file, or None if rendering failed
    """
    try:
        print(f"Pre-rendering shader: {shader_path}")
        print(f"Output: {output_path}")
        print(f"Duration: {duration}s, FPS: {fps}, Resolution: {width}x{height}")

        # Calculate the number of frames
        total_frames = int(duration * fps)
        print(f"Total frames to render: {total_frames}")

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

        # Initialize the shader renderer
        print(f"Initializing shader renderer for {shader_path}...")
        renderer = ShaderRenderer(shader_path, width, height)

        # Render each frame and pipe it to FFmpeg
        print("Rendering frames...")
        start_time = time.time()

        for frame_idx in tqdm(range(total_frames), desc="Pre-rendering shader"):
            # Calculate the time for this frame
            frame_time = frame_idx / fps

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
            pass

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
            print(f"FFmpeg error: {stderr.decode()}")
            return None

        # Calculate the rendering time
        end_time = time.time()
        render_time = end_time - start_time
        fps_rate = total_frames / render_time

        print(f"Shader pre-rendering completed in {render_time:.2f} seconds")
        print(f"Average rendering speed: {fps_rate:.2f} fps")

        # Clean up
        renderer.cleanup()

        return output_path

    except Exception as e:
        print(f"Error pre-rendering shader: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pre-render a shader animation as a video file")
    parser.add_argument("shader", help="Path to the shader file")
    parser.add_argument("output", help="Path to save the rendered video")
    parser.add_argument("--duration", type=float, default=10.0, help="Duration of the video in seconds")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second")
    parser.add_argument("--width", type=int, default=1280, help="Width of the video")
    parser.add_argument("--height", type=int, default=720, help="Height of the video")

    args = parser.parse_args()

    success = prerender_shader_to_video(
        args.shader,
        args.output,
        duration=args.duration,
        fps=args.fps,
        width=args.width,
        height=args.height
    )

    sys.exit(0 if success else 1)
