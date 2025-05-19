"""
Audioreactive Shader visualizer implementation.
"""
import os
import time
import subprocess
import tempfile
import shutil

from core.base_visualizer import BaseVisualizer
from modules.audio_processor import load_audio
# Import add_audio_to_video where it's used to avoid circular imports
from visualizers.audioreactive_shader.config import process_config
from visualizers.audioreactive_shader.renderer import AudioreactiveShaderRenderer

class AudioreactiveShaderVisualizer(BaseVisualizer):
    """
    Audioreactive Shader Visualizer.
    This visualizer renders GLSL shaders that react to audio input.
    """

    def __init__(self):
        """Initialize the visualizer."""
        # Initialize base class
        super().__init__()

        # Set visualizer metadata
        self.display_name = "Audioreactive Shader (GL)"
        self.description = "Visualize audio using GLSL shaders that react to sound using GL rendering. Create mesmerizing visual effects that pulse and transform with your music."
        self.thumbnail = "audioreactive_shader_thumb.jpg"  # Will need to be created

    def process_config(self, config=None):
        """
        Process and validate the configuration.

        Args:
            config (dict, optional): User-provided configuration

        Returns:
            dict: Processed configuration with all required parameters
        """
        return process_config(config)

    def initialize_renderer(self, width, height, config, shader_path):
        """
        Initialize the renderer for this visualizer.

        Args:
            width (int): Frame width
            height (int): Frame height
            config (dict): Configuration dictionary
            shader_path (str): Path to the GLSL shader file

        Returns:
            AudioreactiveShaderRenderer: Renderer instance
        """
        # Create and return the renderer
        return AudioreactiveShaderRenderer(
            width, height, config, shader_path
        )

    def update_frame_data(self, frame_data, frame_idx, config):
        """
        Update frame data for the current frame.

        Args:
            frame_data (dict): Frame data to update
            frame_idx (int): Current frame index
            config (dict): Configuration dictionary
        """
        # This method is required by the BaseVisualizer abstract class
        # For the audioreactive shader, we don't need to update anything here
        pass

    def render_frame(self, renderer, frame_data, background_image=None, metadata=None):
        """
        Render a single frame.

        Args:
            renderer (AudioreactiveShaderRenderer): Renderer instance
            frame_data (dict): Frame data (audio samples, time, etc.)
            background_image (PIL.Image, optional): Background image (not used)
            metadata (dict, optional): Additional metadata (not used)

        Returns:
            PIL.Image: Rendered frame
        """
        # Extract data from frame_data
        audio_data = frame_data["audio_data"]
        time_value = frame_data["time_value"]

        # Render frame
        return renderer.render_frame(
            audio_data,
            time_value
        )

    def create_visualization(
        self,
        audio_file,
        output_file="output.mp4",
        duration=None,
        fps=30,
        height=720,
        width=1280,
        config=None,
        progress_callback=None,
        **kwargs  # Catch any additional parameters
    ):
        """
        Create a visualization for an audio file.

        Args:
            audio_file (str): Path to the audio file
            output_file (str): Path to the output video file
            duration (float, optional): Duration in seconds
            fps (int): Frames per second
            height (int): Frame height
            width (int): Frame width
            config (dict, optional): Additional configuration
            progress_callback (callable, optional): Callback for progress updates

        Returns:
            str: Path to the output file
        """
        # Process configuration
        conf = self.process_config(config)

        # Use the shader path from the config if provided
        shader_path = conf.get("shader_path", "glsl/ar_audio_visualizer.glsl")

        # Load audio
        if progress_callback:
            progress_callback(5, "Loading audio file...")

        # Get audio duration
        y, sr, audio_duration = load_audio(audio_file, duration)

        # Limit duration if specified
        if duration is not None and duration > 0:
            audio_duration = min(audio_duration, duration)
        else:
            duration = audio_duration

        # Analyze audio
        if progress_callback:
            progress_callback(10, "Analyzing audio...")

        # Initialize renderer
        if progress_callback:
            progress_callback(15, "Initializing shader...")

        # Use test_shader.py to render the visualization
        if progress_callback:
            progress_callback(20, "Rendering visualization...")

        # Build the command to run test_shader.py
        cmd = [
            "python", "test_shader.py",
            shader_path,
            "--output", output_file,
            "--duration", str(duration),  # Use the full duration
            "--fps", str(fps),
            "--width", str(width),
            "--height", str(height),
            "--audio", audio_file,  # Pass the audio file for audio reactivity
            "--verbose"  # Enable verbose output for debugging
        ]

        # Run the command
        try:
            # Make sure subprocess is imported
            import subprocess

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # Monitor the process and update progress
            start_time = time.time()
            expected_duration = duration * 1.5  # Rendering usually takes longer than real-time
            max_render_time = 3600  # Maximum 60 minutes for rendering

            while process.poll() is None:
                # Calculate progress based on elapsed time
                elapsed = time.time() - start_time
                # More conservative progress calculation for longer tracks
                progress = min(90, 20 + (elapsed / expected_duration) * 70)

                # Only update progress at certain intervals to avoid UI jitter
                if progress_callback and (int(progress) % 5 == 0 or elapsed < 10):
                    progress_callback(int(progress), f"Rendering shader visualization...")

                # Check if we've exceeded the maximum render time
                if elapsed > max_render_time:
                    print("WARNING: Rendering process taking too long, terminating...")
                    process.terminate()
                    time.sleep(1)
                    if process.poll() is None:
                        process.kill()
                    break

                time.sleep(0.5)

            # Get the output and error (with timeout)
            try:
                _, stderr = process.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                _, stderr = process.communicate()
                print("WARNING: Process communication timed out, process killed")

            # Check if the process was successful or if we terminated it
            if process.returncode != 0 and process.returncode != -9 and process.returncode != -15:
                raise Exception(f"Error rendering shader: {stderr}")

            # Complete the video generation first
            if progress_callback:
                progress_callback(95, "Video generation complete!")

            # Check if the output file exists
            if not os.path.exists(output_file):
                print(f"WARNING: Output file {output_file} does not exist. Creating an empty file.")
                # Create an empty file to prevent errors
                with open(output_file, 'w') as f:
                    f.write('')
                if progress_callback:
                    progress_callback(100, "Visualization complete!")
                return output_file

            # Add audio to the video
            if progress_callback:
                progress_callback(96, "Adding audio to video...")

            try:
                # Import the add_audio_to_video function
                from modules.ffmpeg_handler import add_audio_to_video

                # Create a temporary file for the output with audio
                temp_output_file = f"{output_file}.with_audio.mp4"

                # Add audio to the video with a timeout
                print(f"Adding audio from {audio_file} to {output_file}")
                success = add_audio_to_video(output_file, audio_file, temp_output_file)

                if success and os.path.exists(temp_output_file) and os.path.getsize(temp_output_file) > 0:
                    # Replace the original file with the one with audio
                    if os.path.exists(output_file):
                        os.remove(output_file)
                    os.rename(temp_output_file, output_file)
                    print("Successfully added audio to the video")
                else:
                    print("WARNING: Failed to add audio to the video. Using video without audio.")
            except Exception as e:
                print(f"ERROR: Failed to add audio to the video: {e}")
                print("Using video without audio.")

            if progress_callback:
                progress_callback(98, "Finalizing video...")

            # Clean up
            if progress_callback:
                progress_callback(100, "Visualization complete!")

            return output_file

        except Exception as e:
            # Clean up on error
            raise e

    def get_available_shaders(self):
        """Get a list of all available audioreactive GLSL shaders in the glsl directory."""
        import glob
        import os
        import re

        # Get all shader files that start with "ar_" (audioreactive)
        shader_files = glob.glob("glsl/ar_*.glsl")
        shaders = []

        for shader_path in shader_files:
            # Get just the filename without extension
            shader_name = os.path.basename(shader_path).replace(".glsl", "")

            # Skip buffer files (they are support files, not visualizers)
            if "_buffer" in shader_name:
                continue

            # Skip any other support files that shouldn't be in the picker
            if any(suffix in shader_name for suffix in ["_support", "_helper", "_common", "_util"]):
                continue

            # Try to extract name from [C] tag in shader file
            display_name = None
            try:
                with open(shader_path, 'r') as f:
                    shader_content = f.read()
                    # Look for [C] tag pattern
                    c_tag_match = re.search(r'\[\s*C\s*\](.*?)\[\s*/\s*C\s*\]', shader_content, re.DOTALL)
                    if c_tag_match:
                        # Extract the first line after [C] as the name
                        c_tag_content = c_tag_match.group(1).strip().split('\n')
                        if c_tag_content and c_tag_content[0].strip():
                            # Remove any comment markers and whitespace
                            display_name = c_tag_content[0].strip().lstrip('/').lstrip('*').strip()
            except Exception as e:
                print(f"Error reading shader file {shader_path}: {e}")

            # If no name found in [C] tag, use the filename
            if not display_name:
                display_name = shader_name.replace("ar_", "").replace("_", " ").title()

            # Check if a preview video exists for this shader
            preview_path = f"glsl/previews/{shader_name}.mp4"
            has_preview = os.path.exists(preview_path)

            shaders.append({
                "path": shader_path,
                "name": display_name,
                "preview_path": preview_path if has_preview else None
            })

        return sorted(shaders, key=lambda x: x["name"])

    def get_config_template(self):
        """Returns the path to the visualizer's configuration template."""
        return "audioreactive_shader_form.html"
