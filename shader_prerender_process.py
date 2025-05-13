#!/usr/bin/env python3
"""
Shader pre-rendering process for Audio Visualizer Suite.
This script pre-renders shader animations as video files in a separate process.
"""
import os
import sys
import time
import json
import argparse
from tqdm import tqdm

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the shader renderer
from glsl.shader import ShaderRenderer

def prerender_shader(shader_path, output_path, duration, fps, width, height, status_file):
    """
    Pre-render a shader animation as a video file.
    
    Args:
        shader_path (str): Path to the shader file
        output_path (str): Path to save the rendered video
        duration (float): Duration of the video in seconds
        fps (int): Frames per second
        width (int): Width of the video
        height (int): Height of the video
        status_file (str): Path to the status file
        
    Returns:
        str: Path to the rendered video file, or None if rendering failed
    """
    try:
        print(f"Pre-rendering shader: {shader_path}")
        print(f"Output: {output_path}")
        print(f"Duration: {duration}s, FPS: {fps}, Resolution: {width}x{height}")
        print(f"Status file: {status_file}")
        
        # Calculate the number of frames
        total_frames = int(duration * fps)
        print(f"Total frames to render: {total_frames}")
        
        # Update status
        update_status(status_file, 1, f"Starting shader pre-rendering ({total_frames} frames)...")
        
        # Build the FFmpeg command
        import subprocess
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
        
        # Track the last status update time to avoid too frequent updates
        last_update_time = time.time()
        update_interval = 0.5  # Update status every 0.5 seconds
        
        for frame_idx in tqdm(range(total_frames), desc="Pre-rendering shader"):
            # Calculate the time for this frame
            frame_time = frame_idx / fps
            
            # Render the frame
            if frame_idx % 10 == 0 or frame_idx == total_frames - 1:
                print(f"Rendering frame {frame_idx+1}/{total_frames} at time {frame_time:.2f}s")
            
            # Update status
            current_time = time.time()
            if current_time - last_update_time >= update_interval or frame_idx == total_frames - 1:
                # Calculate progress percentage (0-100)
                # We'll allocate 0-20% of the overall progress to shader pre-rendering
                progress_percent = int(20 * (frame_idx + 1) / total_frames)
                status_message = f"Pre-rendering shader: {frame_idx+1}/{total_frames} frames"
                print(f"Updating status: {progress_percent}%, {status_message}")
                
                update_status(status_file, progress_percent, status_message)
                last_update_time = current_time
            
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
            update_status(status_file, 0, f"FFmpeg error: {error_msg}")
            return None
        
        # Calculate the rendering time
        end_time = time.time()
        render_time = end_time - start_time
        fps_rate = total_frames / render_time
        
        print(f"Shader pre-rendering completed in {render_time:.2f} seconds")
        print(f"Average rendering speed: {fps_rate:.2f} fps")
        
        # Clean up
        renderer.cleanup()
        
        # Final status update
        update_status(status_file, 20, "Shader pre-rendering complete")
        
        return output_path
    
    except Exception as e:
        import traceback
        print(f"Error pre-rendering shader: {e}")
        traceback.print_exc()
        update_status(status_file, 0, f"Error pre-rendering shader: {e}")
        return None

def update_status(status_file, progress, message):
    """
    Update the status file with the current progress and message.
    
    Args:
        status_file (str): Path to the status file
        progress (int): Progress percentage (0-100)
        message (str): Status message
    """
    try:
        status = {
            "progress": progress,
            "message": message,
            "timestamp": time.time()
        }
        
        with open(status_file, 'w') as f:
            json.dump(status, f)
    except Exception as e:
        print(f"Error updating status file: {e}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Pre-render a shader animation as a video file")
    parser.add_argument("shader_path", help="Path to the shader file")
    parser.add_argument("output_path", help="Path to save the rendered video")
    parser.add_argument("status_file", help="Path to the status file")
    parser.add_argument("--duration", type=float, default=10.0, help="Duration of the video in seconds")
    parser.add_argument("--fps", type=int, default=30, help="Frames per second")
    parser.add_argument("--width", type=int, default=1280, help="Width of the video")
    parser.add_argument("--height", type=int, default=720, help="Height of the video")
    
    args = parser.parse_args()
    
    # Pre-render the shader
    result = prerender_shader(
        args.shader_path,
        args.output_path,
        args.duration,
        args.fps,
        args.width,
        args.height,
        args.status_file
    )
    
    # Update the status file with the final result
    if result:
        update_status(args.status_file, 20, f"Shader pre-rendering complete: {result}")
    else:
        update_status(args.status_file, 0, "Shader pre-rendering failed")
    
    sys.exit(0 if result else 1)

if __name__ == "__main__":
    main()
