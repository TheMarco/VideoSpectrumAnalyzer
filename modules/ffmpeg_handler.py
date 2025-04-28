"""
FFmpeg handling functions for the spectrum analyzer.
"""
import os
import subprocess
import tempfile
import time

def setup_ffmpeg_process(width, height, fps, output_path=None):
    """
    Set up an FFmpeg process for piping video frames.
    
    Args:
        width (int): Frame width
        height (int): Frame height
        fps (int): Frames per second
        output_path (str, optional): Path to save the output video
        
    Returns:
        tuple: (process, temp_video_path)
    """
    # Create temporary file if output_path is not provided
    if not output_path:
        temp_video_file = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        temp_video_path = temp_video_file.name
        temp_video_file.close()
    else:
        temp_video_path = output_path
    
    print(f"Temporary video path (no audio): {temp_video_path}")
    
    # Set up FFmpeg command
    ffmpeg_cmd = [
        "ffmpeg", "-y", 
        "-f", "rawvideo", 
        "-vcodec", "rawvideo", 
        "-s", f"{width}x{height}", 
        "-pix_fmt", "rgba", 
        "-r", str(fps), 
        "-i", "-", 
        "-an", 
        "-c:v", "libx264", 
        "-preset", "fast", 
        "-crf", "23", 
        "-pix_fmt", "yuv420p", 
        temp_video_path
    ]
    
    print("Starting FFmpeg process for video frames...")
    print(f"Command: {' '.join(ffmpeg_cmd)}")
    
    # Start FFmpeg process
    process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)
    
    return process, temp_video_path

def write_frame_to_ffmpeg(process, frame_bytes, frame_idx):
    """
    Write a frame to the FFmpeg process.
    
    Args:
        process: FFmpeg subprocess
        frame_bytes (bytes): Raw frame data
        frame_idx (int): Frame index for error reporting
        
    Raises:
        RuntimeError: If there is an error writing to FFmpeg
    """
    try:
        process.stdin.write(frame_bytes)
    except (BrokenPipeError, OSError) as e:
        print(f"\nError writing frame {frame_idx} to FFmpeg: {e}")
        try:
            if process.stdin:
                process.stdin.close()
        except OSError:
            print(f"Warning: Error closing stdin for frame {frame_idx}, might already be closed.")
        
        process.wait()
        print(f"FFmpeg exit code (pipe error): {process.returncode}")
        
        raise RuntimeError(f"FFmpeg pipe error on frame {frame_idx}: {e}") from e

def finalize_ffmpeg_process(process, temp_video_path):
    """
    Finalize the FFmpeg process and clean up if needed.
    
    Args:
        process: FFmpeg subprocess
        temp_video_path (str): Path to the temporary video file
        
    Returns:
        bool: True if successful, False otherwise
    """
    print("Closing FFmpeg stdin and waiting for video process...")
    
    if process.stdin:
        try:
            process.stdin.close()
        except (OSError, BrokenPipeError) as e:
            print(f"Warning: Error closing ffmpeg stdin (might be already closed): {e}")
    
    process.wait()
    
    if process.returncode != 0:
        print(f"ERROR: FFmpeg video encoding failed (code {process.returncode})")
        return False
    else:
        print("FFmpeg video encoding successful.")
        return True

def add_audio_to_video(temp_video_path, audio_file, output_file):
    """
    Add audio to the video file.
    
    Args:
        temp_video_path (str): Path to the temporary video file
        audio_file (str): Path to the audio file
        output_file (str): Path to save the output video with audio
        
    Returns:
        bool: True if successful, False otherwise
    """
    print("Adding audio to the video...")
    
    final_ffmpeg_cmd = [
        "ffmpeg", "-y", 
        "-i", temp_video_path, 
        "-i", audio_file, 
        "-c:v", "copy", 
        "-c:a", "aac", 
        "-b:a", "192k", 
        "-shortest", 
        output_file
    ]
    
    try:
        print(f"Running command: {' '.join(final_ffmpeg_cmd)}")
        result = subprocess.run(final_ffmpeg_cmd, check=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
        print("Audio added successfully.")
        
        if result.stderr:
            print(f"FFmpeg warnings (audio merge):\n{result.stderr}")
        
        return True
    
    except subprocess.CalledProcessError as e:
        print(f"ERROR: FFmpeg audio merge failed (code {e.returncode})\nStderr:\n{e.stderr}\nTemp video: {temp_video_path}")
        return False
    
    except FileNotFoundError:
        print("ERROR: ffmpeg not found for audio merge.")
        return False
    
    except Exception as e:
        print(f"ERROR: Unexpected audio merge error: {e}")
        return False

def cleanup_temp_files(temp_video_path, video_capture=None):
    """
    Clean up temporary files and resources.
    
    Args:
        temp_video_path (str): Path to the temporary video file
        video_capture: OpenCV video capture object
    """
    if video_capture:
        print("Releasing video capture...")
        video_capture.release()
    
    if os.path.exists(temp_video_path):
        try:
            os.remove(temp_video_path)
            print(f"Removed temp file: {temp_video_path}")
        except OSError as e:
            print(f"Warning: Could not remove temp file {temp_video_path}: {e}")
