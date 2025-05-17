#!/usr/bin/env python3
"""
Shader Renderer Wrapper for Audio Visualizer Suite

This script detects which shader to use and calls the appropriate renderer.
"""
import os
import sys
import argparse

def render_shader(shader_path, output_path, duration=5.0, fps=30, width=1280, height=720,
                  show_preview=False, verbose=False):
    """
    Render a shader to a video file.

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
    # Check if the shader file exists
    if not os.path.exists(shader_path):
        print(f"Error: Shader file not found: {shader_path}")
        return False

    # Get the shader filename
    shader_filename = os.path.basename(shader_path)

    # Import the shader preprocessor
    from glsl.shader_preprocessor import create_fixed_shader, is_problematic_shader

    # Check if this is a problematic shader
    if is_problematic_shader(shader_path) or shader_filename in ["angel.glsl", "nebula.glsl", "blackhole.glsl", "shield.glsl", "ghosts.glsl", "quantum.glsl", "starnest.glsl", "starbirth.glsl", "biomine.glsl"]:
        print(f"Detected potentially problematic shader: {shader_filename}")

        # Create a fixed version of the shader
        fixed_shader_path = create_fixed_shader(shader_path)
        print(f"Using fixed shader: {fixed_shader_path}")

        # Use the test_shader.py with the fixed version
        from test_shader import test_shader
        return test_shader(
            fixed_shader_path,
            output_path,
            duration=duration,
            fps=fps,
            width=width,
            height=height,
            show_preview=show_preview,
            verbose=verbose
        )

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Render a shader to a video file")
    parser.add_argument("shader", help="Path to the shader file")
    parser.add_argument("--output", "-o", help="Path to save the rendered video (default: output_<shader_name>.mp4)")
    parser.add_argument("--duration", "-d", type=float, default=5.0, help="Duration of the video in seconds (default: 5.0)")
    parser.add_argument("--fps", "-f", type=int, default=30, help="Frames per second (default: 30)")
    parser.add_argument("--width", "-W", type=int, default=1280, help="Width of the video (default: 1280)")
    parser.add_argument("--height", "-H", type=int, default=720, help="Height of the video (default: 720)")
    parser.add_argument("--play", "-p", action="store_true", help="Play the video after rendering")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print detailed information")

    args = parser.parse_args()

    # Set default output path if not specified
    if not args.output:
        shader_name = os.path.splitext(os.path.basename(args.shader))[0]
        args.output = f"output_{shader_name}.mp4"

    # Render the shader
    success = render_shader(
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
