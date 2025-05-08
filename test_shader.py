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
import numpy as np
from PIL import Image

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import audio processing functions if available
try:
    from modules.audio_processor import load_audio
except ImportError:
    print("Warning: Could not import audio_processor module. Audio reactivity will be limited.")
    load_audio = None

def test_shader(shader_path, output_path, duration=5.0, fps=30, width=1280, height=720,
                show_preview=False, verbose=False, audio_file=None, max_frames=None):
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
        audio_file (str, optional): Path to an audio file for audio-reactive shaders

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

        # Limit the number of frames if max_frames is specified
        if max_frames is not None and max_frames > 0 and max_frames < total_frames:
            print(f"Limiting frames to {max_frames} (from {total_frames})")
            total_frames = max_frames

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

        # Load audio data if provided
        audio_data = None
        audio_texture = None
        if audio_file and os.path.exists(audio_file):
            print(f"Loading audio file: {audio_file}")
            if load_audio:
                try:
                    # Load audio using the audio_processor module
                    y, sr, audio_duration = load_audio(audio_file, duration)
                    print(f"Audio loaded: {audio_duration:.2f}s at {sr}Hz")

                    # Limit duration if audio is shorter than requested
                    if audio_duration < duration:
                        print(f"Audio duration ({audio_duration:.2f}s) is shorter than requested duration ({duration:.2f}s)")
                        print(f"Limiting video duration to {audio_duration:.2f}s")
                        duration = audio_duration
                        total_frames = int(duration * fps)

                    # Create audio frames for each video frame
                    hop_length = sr // fps
                    audio_frames = []

                    for i in range(total_frames):
                        start_sample = i * hop_length
                        end_sample = min(start_sample + hop_length, len(y))
                        if start_sample < len(y):
                            frame_samples = y[start_sample:end_sample]
                            # Pad with zeros if needed
                            if len(frame_samples) < hop_length:
                                frame_samples = np.pad(frame_samples, (0, hop_length - len(frame_samples)))
                            audio_frames.append(frame_samples)
                        else:
                            # Pad with zeros if we've reached the end of the audio
                            audio_frames.append(np.zeros(hop_length))

                    audio_data = audio_frames
                    print(f"Created {len(audio_frames)} audio frames")
                except Exception as e:
                    print(f"Error loading audio: {e}")
                    audio_data = None
            else:
                print("Audio processing module not available. Using simple audio visualization.")
                try:
                    # Simple audio visualization without the audio_processor module
                    import wave
                    # numpy is already imported at the top of the file

                    with wave.open(audio_file, 'rb') as wf:
                        # Get audio parameters
                        channels = wf.getnchannels()
                        sample_width = wf.getsampwidth()
                        sample_rate = wf.getframerate()
                        n_frames = wf.getnframes()
                        audio_duration = n_frames / sample_rate

                        # Limit duration if audio is shorter than requested
                        if audio_duration < duration:
                            print(f"Audio duration ({audio_duration:.2f}s) is shorter than requested duration ({duration:.2f}s)")
                            print(f"Limiting video duration to {audio_duration:.2f}s")
                            duration = audio_duration
                            total_frames = int(duration * fps)

                        # Read all audio data
                        raw_data = wf.readframes(n_frames)

                        # Convert to numpy array
                        if sample_width == 1:
                            dtype = np.uint8
                        elif sample_width == 2:
                            dtype = np.int16
                        elif sample_width == 4:
                            dtype = np.int32
                        else:
                            raise ValueError(f"Unsupported sample width: {sample_width}")

                        audio_array = np.frombuffer(raw_data, dtype=dtype)

                        # Reshape for multiple channels
                        if channels > 1:
                            audio_array = audio_array.reshape(-1, channels)
                            # Convert to mono by averaging channels
                            audio_array = audio_array.mean(axis=1)

                        # Normalize to -1.0 to 1.0 range
                        if dtype == np.uint8:
                            audio_array = (audio_array.astype(np.float32) - 128) / 128.0
                        else:
                            audio_array = audio_array.astype(np.float32) / (2**(sample_width*8-1))

                        # Create audio frames for each video frame
                        hop_length = sample_rate // fps
                        audio_frames = []

                        for i in range(total_frames):
                            start_sample = i * hop_length
                            end_sample = min(start_sample + hop_length, len(audio_array))
                            if start_sample < len(audio_array):
                                frame_samples = audio_array[start_sample:end_sample]
                                # Pad with zeros if needed
                                if len(frame_samples) < hop_length:
                                    frame_samples = np.pad(frame_samples, (0, hop_length - len(frame_samples)))
                                audio_frames.append(frame_samples)
                            else:
                                # Pad with zeros if we've reached the end of the audio
                                audio_frames.append(np.zeros(hop_length))

                        audio_data = audio_frames
                        print(f"Created {len(audio_frames)} audio frames using simple audio processing")
                except Exception as e:
                    print(f"Error loading audio with simple processing: {e}")
                    audio_data = None

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

            # Update audio texture if we have audio data
            if audio_data and frame_idx < len(audio_data):
                try:
                    # Create audio texture for this frame
                    frame_audio = audio_data[frame_idx]

                    # Create a texture from the audio data
                    texture_width = 512  # Width of the texture
                    texture_data = np.zeros((1, texture_width, 4), dtype=np.uint8)

                    # Fill the texture with audio data
                    for i in range(min(texture_width, len(frame_audio))):
                        # Normalize to 0-255 range
                        value = int((frame_audio[i] + 1.0) / 2.0 * 255)
                        texture_data[0, i, 0] = value  # R channel
                        texture_data[0, i, 1] = value  # G channel
                        texture_data[0, i, 2] = value  # B channel
                        texture_data[0, i, 3] = 255    # A channel

                    # Create a temporary texture file
                    audio_texture_path = os.path.join(os.path.dirname(shader_path), "textures", "audio_data.png")
                    os.makedirs(os.path.dirname(audio_texture_path), exist_ok=True)

                    # Save the texture to a file
                    Image.fromarray(texture_data.reshape(1, texture_width, 4)).save(audio_texture_path)

                    # Update the renderer's audio texture
                    renderer.update_audio_texture(audio_texture_path)
                except Exception as e:
                    print(f"Error creating audio texture: {e}")
                    # Continue without audio texture

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
    parser.add_argument("--audio", "-a", help="Path to an audio file for audio-reactive shaders")
    parser.add_argument("--max_frames", type=int, help="Maximum number of frames to render")

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
        verbose=args.verbose,
        audio_file=args.audio,
        max_frames=args.max_frames
    )

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
