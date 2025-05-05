#!/usr/bin/env python3
"""
Shader Testing Tool for Audio Visualizer Suite

This tool allows you to test GLSL shaders before using them in the main application.
It renders a short preview of the shader and saves it as a video file.
"""
import os
import sys
import time
import argparse
from tqdm import tqdm
import subprocess

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_shader(shader_path, output_path, duration=5.0, fps=30, width=1280, height=720,
                show_preview=False, verbose=False):
    """
    Test a GLSL shader by rendering it to a video file.

    Args:
        shader_path (str): Path to the shader file
        output_path (str): Path to save the rendered video
        duration (float): Duration of the video in seconds
        fps (int): Frames per second
        width (int): Width of the video
        height (int): Height of the video
        show_preview (bool): Whether to play the video after rendering
        verbose (bool): Whether to print detailed information

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"Testing shader: {shader_path}")
        print(f"Output: {output_path}")
        print(f"Duration: {duration}s, FPS: {fps}, Resolution: {width}x{height}")

        # Check if the shader file exists
        if not os.path.exists(shader_path):
            print(f"Error: Shader file not found: {shader_path}")
            return False

        # Import the shader renderer
        try:
            from glsl.shader import ShaderRenderer
            print("Using GPU-accelerated shader renderer")
        except ImportError:
            print("Error: Could not import ShaderRenderer from glsl.shader")
            return False

        # Calculate the number of frames
        total_frames = int(duration * fps)
        print(f"Total frames to render: {total_frames}")

        # Build the FFmpeg command with QuickTime-compatible settings
        # Use H.264 with settings specifically for QuickTime compatibility
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
            "-profile:v", "main",     # Main profile for better compatibility
            "-level", "4.0",          # Level 4.0 for QuickTime compatibility
            "-preset", "medium",      # Better quality-to-size ratio
            "-crf", "17",             # Higher quality
            "-pix_fmt", "yuv420p",    # Standard pixel format
            "-movflags", "+faststart", # Optimize for streaming
            "-brand", "mp42",         # MP4 v2 brand for better compatibility
            "-tag:v", "avc1",         # Standard AVC tag
            output_path
        ]

        # Start the FFmpeg process
        print("Starting FFmpeg process...")
        ffmpeg_process = subprocess.Popen(
            ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE if not verbose else None,
            stderr=subprocess.PIPE if not verbose else None
        )

        # Initialize the shader renderer
        print(f"Initializing shader renderer for {shader_path}...")
        start_init_time = time.time()
        renderer = ShaderRenderer(shader_path, width, height)
        end_init_time = time.time()
        print(f"Shader initialization completed in {end_init_time - start_init_time:.2f} seconds")

        # Render each frame and pipe it to FFmpeg
        print("Rendering frames...")
        start_time = time.time()

        for frame_idx in tqdm(range(total_frames), desc="Rendering shader"):
            # Calculate the time for this frame
            frame_time = frame_idx / fps

            # Render the frame
            if verbose and (frame_idx % 10 == 0 or frame_idx == total_frames - 1):
                print(f"Rendering frame {frame_idx+1}/{total_frames} at time {frame_time:.2f}s")

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
            return False

        # Calculate the rendering time
        end_time = time.time()
        render_time = end_time - start_time
        fps_rate = total_frames / render_time

        print(f"Shader rendering completed in {render_time:.2f} seconds")
        print(f"Average rendering speed: {fps_rate:.2f} fps")

        # Clean up
        renderer.cleanup()

        # Show the video if requested
        if show_preview:
            print(f"Playing video: {output_path}")
            if sys.platform == "darwin":  # macOS
                subprocess.call(["open", output_path])
            elif sys.platform == "win32":  # Windows
                os.startfile(output_path)
            else:  # Linux
                subprocess.call(["xdg-open", output_path])

        print(f"Shader test completed successfully: {output_path}")
        return True

    except Exception as e:
        import traceback
        print(f"Error testing shader: {e}")
        traceback.print_exc()
        return False

def list_available_shaders(shader_dir="glsl"):
    """
    List all available shaders in the shader directory.

    Args:
        shader_dir (str): Directory containing shader files

    Returns:
        list: List of shader file paths
    """
    if not os.path.exists(shader_dir):
        print(f"Error: Shader directory not found: {shader_dir}")
        return []

    shader_files = []
    for file in os.listdir(shader_dir):
        if file.endswith(".glsl") or file.endswith(".frag"):
            shader_files.append(os.path.join(shader_dir, file))

    return shader_files

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test GLSL shaders for Audio Visualizer Suite")
    parser.add_argument("shader", help="Path to the shader file or 'list' to list available shaders")
    parser.add_argument("--output", "-o", help="Path to save the rendered video (default: output_<shader_name>.mp4)")
    parser.add_argument("--duration", "-d", type=float, default=5.0, help="Duration of the video in seconds (default: 5.0)")
    parser.add_argument("--fps", "-f", type=int, default=30, help="Frames per second (default: 30)")
    parser.add_argument("--width", "-W", type=int, default=1280, help="Width of the video (default: 1280)")
    parser.add_argument("--height", "-H", type=int, default=720, help="Height of the video (default: 720)")
    parser.add_argument("--play", "-p", action="store_true", help="Play the video after rendering")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print detailed information")

    args = parser.parse_args()

    # List available shaders if requested
    if args.shader == "list":
        print("Available shaders:")
        shaders = list_available_shaders()
        if not shaders:
            print("  No shaders found in the 'glsl' directory")
        else:
            for shader in shaders:
                print(f"  {shader}")
        return 0

    # Set default output path if not specified
    if not args.output:
        shader_name = os.path.splitext(os.path.basename(args.shader))[0]
        args.output = f"output_{shader_name}.mp4"

    # Test the shader
    success = test_shader(
        args.shader,
        args.output,
        duration=args.duration,
        fps=args.fps,
        width=args.width,
        height=args.height,
        show_preview=args.play,
        verbose=args.verbose
    )

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
