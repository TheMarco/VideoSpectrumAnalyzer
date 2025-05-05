#!/usr/bin/env python3
"""
Generate preview videos for all GLSL shaders in the glsl directory.
This script is used to create preview videos for the Background Shader Explorer page.
"""
import os
import sys
import glob
import argparse
import subprocess

# Try to import tqdm for progress bars, but make it optional
try:
    from tqdm import tqdm
except ImportError:
    # Define a simple fallback if tqdm is not available
    def tqdm(iterable, **kwargs):
        total = len(iterable) if hasattr(iterable, '__len__') else None
        if total and 'desc' in kwargs:
            print(f"{kwargs['desc']} (total: {total})")
        return iterable

def get_shader_files():
    """
    Get a list of all GLSL shader files in the glsl directory.

    Returns:
        list: List of shader file paths
    """
    # Get all .glsl files in the glsl directory, excluding the fixed directory
    shader_files = glob.glob("glsl/*.glsl")

    # Filter out the optical_deconstruction shader as per user preference
    shader_files = [f for f in shader_files if "optical_deconstruction" not in f]

    return sorted(shader_files)

def get_shader_name(shader_path):
    """
    Get the display name of a shader from its path.

    Args:
        shader_path (str): Path to the shader file

    Returns:
        str: Display name of the shader
    """
    # Get just the filename without extension
    shader_name = os.path.basename(shader_path).replace(".glsl", "")

    # Convert to title case for display (e.g., "biomine" -> "Biomine")
    display_name = shader_name.replace("_", " ").title()

    return display_name

def generate_preview_video(shader_path, output_path, duration=10.0, fps=30, width=640, height=360, verbose=False):
    """
    Generate a preview video for a shader.

    Args:
        shader_path (str): Path to the shader file
        output_path (str): Path to save the preview video
        duration (float): Duration of the video in seconds
        fps (int): Frames per second
        width (int): Width of the video
        height (int): Height of the video
        verbose (bool): Whether to print detailed information

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"Generating preview for {shader_path}...")

        # Create the output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Use the render_shader.py script which works better for all shaders
        cmd = [
            sys.executable,
            "test_shader.py",
            shader_path,
            "--output", output_path,
            "--duration", str(duration),
            "--fps", str(fps),
            "--width", str(width),
            "--height", str(height)
        ]

        if verbose:
            print(f"Running command: {' '.join(cmd)}")

        # Run the command
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE if not verbose else None,
            stderr=subprocess.PIPE if not verbose else None,
            text=True
        )

        if process.returncode != 0:
            print(f"Error generating preview for {shader_path}:")
            if not verbose:
                print(process.stderr)
            return False

        print(f"Preview generated successfully: {output_path}")
        return True

    except Exception as e:
        print(f"Error generating preview for {shader_path}: {e}")
        return False

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate preview videos for all GLSL shaders")
    parser.add_argument("--force", "-f", action="store_true", help="Force regeneration of all previews")
    parser.add_argument("--duration", "-d", type=float, default=10.0, help="Duration of the preview videos in seconds")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second")
    parser.add_argument("--width", "-W", type=int, default=1280, help="Width of the preview videos")
    parser.add_argument("--height", "-H", type=int, default=720, help="Height of the preview videos")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print detailed information")

    args = parser.parse_args()

    # Get all shader files
    shader_files = get_shader_files()
    print(f"Found {len(shader_files)} shader files")

    # Create the previews directory if it doesn't exist
    os.makedirs("glsl/previews", exist_ok=True)

    # Generate preview videos for each shader
    success_count = 0
    skip_count = 0
    error_count = 0

    for shader_path in tqdm(shader_files, desc="Generating previews"):
        # Get the shader name
        shader_name = os.path.basename(shader_path).replace(".glsl", "")

        # Define the output path
        output_path = f"glsl/previews/{shader_name}.mp4"

        # Check if the preview already exists
        if os.path.exists(output_path) and not args.force:
            if args.verbose:
                print(f"Preview already exists for {shader_path}, skipping")
            skip_count += 1
            continue

        # Generate the preview
        success = generate_preview_video(
            shader_path,
            output_path,
            duration=args.duration,
            fps=args.fps,
            width=args.width,
            height=args.height,
            verbose=args.verbose
        )

        if success:
            success_count += 1
        else:
            error_count += 1

    # Print summary
    print(f"\nSummary:")
    print(f"  Total shaders: {len(shader_files)}")
    print(f"  Successfully generated: {success_count}")
    print(f"  Skipped (already exist): {skip_count}")
    print(f"  Errors: {error_count}")

    return 0 if error_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
