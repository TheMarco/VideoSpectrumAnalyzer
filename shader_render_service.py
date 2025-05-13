#!/usr/bin/env python3
"""
Shader Rendering Service for Audio Visualizer Suite.
This script runs as a separate process to render GLSL shaders using GPU acceleration.
It takes input parameters via command line arguments and outputs rendered frames to disk.
"""
import os
import sys
import time
import json
import argparse
from PIL import Image
import numpy as np

# Add the project root to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def render_frame(shader_path, output_path, width, height, time_value):
    """
    Render a single frame using the shader at the specified time.
    
    Args:
        shader_path (str): Path to the shader file
        output_path (str): Path to save the rendered frame
        width (int): Width of the output image
        height (int): Height of the output image
        time_value (float): Time value for the shader
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Import the shader module dynamically
        sys.path.append(os.path.dirname(os.path.abspath(shader_path)))
        from glsl.shader import ShaderRenderer
        
        # Create the renderer
        print(f"Creating renderer for {shader_path} at {width}x{height}")
        renderer = ShaderRenderer(shader_path, width, height)
        
        # Render the frame
        print(f"Rendering frame at time {time_value}")
        frame = renderer.render_frame(time_value)
        
        # Save the frame
        frame.save(output_path)
        print(f"Frame saved to {output_path}")
        
        # Clean up
        renderer.cleanup()
        
        return True
    except Exception as e:
        print(f"Error rendering frame: {e}")
        import traceback
        traceback.print_exc()
        return False

def render_frames(shader_path, output_dir, width, height, time_values):
    """
    Render multiple frames using the shader at the specified times.
    
    Args:
        shader_path (str): Path to the shader file
        output_dir (str): Directory to save the rendered frames
        width (int): Width of the output image
        height (int): Height of the output image
        time_values (list): List of time values for the shader
        
    Returns:
        list: List of paths to the rendered frames
    """
    try:
        # Import the shader module dynamically
        sys.path.append(os.path.dirname(os.path.abspath(shader_path)))
        from glsl.shader import ShaderRenderer
        
        # Create the renderer
        print(f"Creating renderer for {shader_path} at {width}x{height}")
        renderer = ShaderRenderer(shader_path, width, height)
        
        # Create the output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Render the frames
        output_paths = []
        for i, time_value in enumerate(time_values):
            # Render the frame
            print(f"Rendering frame {i+1}/{len(time_values)} at time {time_value}")
            frame = renderer.render_frame(time_value)
            
            # Save the frame
            output_path = os.path.join(output_dir, f"frame_{i:04d}.png")
            frame.save(output_path)
            output_paths.append(output_path)
            
            # Print progress
            if (i+1) % 10 == 0 or i+1 == len(time_values):
                print(f"Progress: {i+1}/{len(time_values)} frames rendered")
        
        # Clean up
        renderer.cleanup()
        
        return output_paths
    except Exception as e:
        print(f"Error rendering frames: {e}")
        import traceback
        traceback.print_exc()
        return []

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Shader Rendering Service")
    parser.add_argument("--shader", required=True, help="Path to the shader file")
    parser.add_argument("--output", required=True, help="Path to save the rendered frame or directory for multiple frames")
    parser.add_argument("--width", type=int, default=1280, help="Width of the output image")
    parser.add_argument("--height", type=int, default=720, help="Height of the output image")
    parser.add_argument("--time", type=float, help="Time value for the shader (for single frame)")
    parser.add_argument("--times", help="JSON file with time values for the shader (for multiple frames)")
    parser.add_argument("--times-list", help="Comma-separated list of time values for the shader (for multiple frames)")
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.time is not None and (args.times is not None or args.times_list is not None):
        print("Error: Cannot specify both --time and --times/--times-list")
        return 1
    
    if args.time is None and args.times is None and args.times_list is None:
        print("Error: Must specify either --time or --times/--times-list")
        return 1
    
    # Render a single frame
    if args.time is not None:
        success = render_frame(args.shader, args.output, args.width, args.height, args.time)
        return 0 if success else 1
    
    # Render multiple frames from a JSON file
    if args.times is not None:
        try:
            with open(args.times, 'r') as f:
                time_values = json.load(f)
            
            if not isinstance(time_values, list):
                print("Error: Times file must contain a JSON array of time values")
                return 1
            
            output_paths = render_frames(args.shader, args.output, args.width, args.height, time_values)
            
            # Write the output paths to a JSON file
            output_json = os.path.join(args.output, "frames.json")
            with open(output_json, 'w') as f:
                json.dump(output_paths, f)
            
            print(f"Output paths written to {output_json}")
            return 0 if output_paths else 1
        except Exception as e:
            print(f"Error loading times file: {e}")
            return 1
    
    # Render multiple frames from a comma-separated list
    if args.times_list is not None:
        try:
            time_values = [float(t) for t in args.times_list.split(',')]
            
            output_paths = render_frames(args.shader, args.output, args.width, args.height, time_values)
            
            # Write the output paths to a JSON file
            output_json = os.path.join(args.output, "frames.json")
            with open(output_json, 'w') as f:
                json.dump(output_paths, f)
            
            print(f"Output paths written to {output_json}")
            return 0 if output_paths else 1
        except Exception as e:
            print(f"Error parsing times list: {e}")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
