"""
Smooth Curves visualizer implementation.
"""

import os
import numpy as np
from PIL import Image
from core.base_visualizer import BaseVisualizer
from modules.audio_processor import load_audio
from modules.media_handler import load_background_media, process_video_frame, load_fonts
from .config import process_config
from .webgl_renderer import SmoothCurvesWebGLRenderer

class SmoothCurvesVisualizer(BaseVisualizer):
    """
    Smooth Curves visualizer.
    This visualizer renders smooth audio-reactive curves using a GLSL shader.
    """
    name = "SmoothCurvesVisualizer"  # Internal name for registration
    display_name = "Smooth Curves (WebGL)"  # Display name shown to users
    description = "Displays smooth audio-reactive curves with glow effects using WebGL rendering for better performance."
    thumbnail = "static/images/thumbnails/smooth_curves.jpg"  # Will need to be created

    def __init__(self):
        """Initialize the visualizer."""
        super().__init__()
        self.gl_renderer = None
        self.audio_samples = None
        self.sample_rate = None
        self.total_frames = None
        self.samples_per_frame = None

    def process_config(self, config=None):
        """
        Process and validate the configuration.

        Args:
            config (dict, optional): User-provided configuration

        Returns:
            dict: Processed configuration with all required parameters
        """
        return process_config(config)

    def initialize_renderer(self, width, height, config):
        """
        Initialize the renderer for this visualizer.

        Args:
            width (int): Frame width
            height (int): Frame height
            config (dict): Configuration dictionary

        Returns:
            object: Renderer instance
        """
        # Initialize GL renderer
        try:
            print(f"Initializing Smooth Curves GL renderer with width={width}, height={height}...")

            # Ensure width and height are integers
            try:
                width = int(width)
                height = int(height)
            except (ValueError, TypeError) as e:
                print(f"Error converting width/height to int: {e}")
                # Use default values if conversion fails
                width = 1280
                height = 720

            # Make sure we're not passing the width parameter from the config as the frame width
            if isinstance(config, dict) and "width" in config and config["width"] == width:
                print("Warning: Config width parameter matches frame width. This may cause confusion.")
                print(f"Config width: {config['width']}, Frame width: {width}")

                # If width is a string like "0.06", it's likely the config width parameter
                if isinstance(config["width"], str) and "." in config["width"]:
                    print(f"Using default frame width 1280 instead of config width {config['width']}")
                    width = 1280

            self.gl_renderer = SmoothCurvesWebGLRenderer(width, height, config)
            print("GL renderer initialized successfully")
            return self.gl_renderer
        except Exception as e:
            print(f"Error initializing GL renderer: {e}")
            import traceback
            traceback.print_exc()
            raise

    def render_frame(self, renderer, frame_data, background_image=None, metadata=None):
        """
        Render a single frame.

        Args:
            renderer (SmoothCurvesWebGLRenderer): Renderer instance
            frame_data (dict): Frame data (audio samples, time, etc.)
            background_image (PIL.Image, optional): Background image
            metadata (dict, optional): Additional metadata (artist, title, etc.)

        Returns:
            PIL.Image: Rendered frame
        """
        # Extract audio data from frame_data
        frame_audio_data = frame_data.get("audio_data", np.zeros(512))

        # Ensure metadata is properly formatted for text rendering
        if metadata is None:
            metadata = {}

        # Make sure artist_name and track_title are in metadata
        if "artist_name" not in metadata and hasattr(self, "artist_name"):
            metadata["artist_name"] = self.artist_name

        if "track_title" not in metadata and hasattr(self, "track_title"):
            metadata["track_title"] = self.track_title

        # Debug: Print metadata being passed to renderer
        print(f"Passing metadata to renderer: {metadata}")

        # Render the frame using the GL renderer
        try:
            return renderer.render_frame(frame_audio_data, background_image, metadata)
        except Exception as e:
            print(f"Error rendering frame: {e}")
            import traceback
            traceback.print_exc()

            # Return a black image as fallback
            return Image.new('RGBA', (renderer.width, renderer.height), (0, 0, 0, 255))

    def create_visualization(
        self,
        audio_file,
        output_file="output.mp4",
        background_image_path=None,
        background_video_path=None,
        background_shader_path=None,
        artist_name="Artist Name",
        track_title="Track Title",
        duration=None,
        fps=30,
        height=720,
        width=1280,
        config=None,
        progress_callback=None,
    ):
        """
        Create a visualization for an audio file.

        Args:
            audio_file (str): Path to the audio file
            output_file (str): Path to the output video file
            background_image_path (str, optional): Path to the background image
            background_video_path (str, optional): Path to the background video
            background_shader_path (str, optional): Path to the background shader
            artist_name (str): Artist name
            track_title (str): Track title
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

        # Override fps with the value from config if available
        if "fps" in conf:
            print(f"Using fps from config: {conf['fps']}")
            fps = conf["fps"]
        else:
            print(f"Using default fps: {fps}")

        # Ensure width and height are integers
        try:
            width = int(width)
        except (ValueError, TypeError):
            print(f"Invalid width value: {width}, using default 1280")
            width = 1280

        try:
            height = int(height)
        except (ValueError, TypeError):
            print(f"Invalid height value: {height}, using default 720")
            height = 720

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

        # Calculate frame details
        self.total_frames = int(audio_duration * fps)
        self.samples_per_frame = int(sr / fps)
        self.audio_samples = y
        self.sample_rate = sr

        # Store artist and track title for text rendering
        self.artist_name = artist_name
        self.track_title = track_title

        print(f"Audio loaded: duration={audio_duration}s, sample_rate={sr}Hz")
        print(f"Total frames: {self.total_frames}, samples per frame: {self.samples_per_frame}")
        print(f"Artist: {self.artist_name}, Track: {self.track_title}")

        # Call the base class's create_visualization to handle the rest of the process
        return super().create_visualization(
            audio_file=audio_file,
            output_file=output_file,
            background_image_path=background_image_path,
            background_video_path=background_video_path,
            background_shader_path=background_shader_path,
            artist_name=artist_name,
            track_title=track_title,
            duration=duration,
            fps=fps,
            height=height,
            width=width,
            config=conf,
            progress_callback=progress_callback,
        )

    def update_frame_data(self, frame_data, frame_idx, config):
        """
        Update frame data for the current frame.

        Args:
            frame_data (dict): Frame data dictionary to update
            frame_idx (int): Current frame index
            config (dict): Configuration dictionary
        """
        # Calculate the start and end sample indices for this frame
        start_sample = frame_idx * self.samples_per_frame
        end_sample = min(start_sample + self.samples_per_frame, len(self.audio_samples))

        # Get the audio samples for this frame
        frame_samples = self.audio_samples[start_sample:end_sample]

        # Perform FFT to get frequency domain data
        n_fft = 2048  # FFT size
        hop_length = self.samples_per_frame  # Hop length

        # Pad the frame samples if needed
        if len(frame_samples) < n_fft:
            frame_samples = np.pad(frame_samples, (0, n_fft - len(frame_samples)), 'constant')

        # Calculate the FFT
        try:
            import librosa
            stft = librosa.stft(frame_samples, n_fft=n_fft, hop_length=hop_length)
            magnitudes = np.abs(stft)

            # Convert to dB scale
            magnitudes_db = librosa.amplitude_to_db(magnitudes, ref=np.max)

            # Normalize to 0-1 range
            magnitudes_normalized = (magnitudes_db - magnitudes_db.min()) / (magnitudes_db.max() - magnitudes_db.min() + 1e-10)

            # Reshape to 1D array for the shader
            audio_data = np.mean(magnitudes_normalized, axis=1)

            # Ensure we have 512 frequency bins for the shader
            if len(audio_data) < 512:
                audio_data = np.pad(audio_data, (0, 512 - len(audio_data)), 'constant')
            elif len(audio_data) > 512:
                audio_data = audio_data[:512]

        except Exception as e:
            print(f"Error calculating FFT: {e}")
            # Fallback to raw audio samples
            audio_data = np.zeros(512)
            if len(frame_samples) > 0:
                # Normalize and reshape
                normalized_samples = frame_samples / (np.max(np.abs(frame_samples)) + 1e-10)
                # Repeat to fill 512 bins
                repeat_count = int(np.ceil(512 / len(normalized_samples)))
                audio_data = np.tile(normalized_samples, repeat_count)[:512]

        # Update frame_data with audio data
        frame_data["audio_data"] = audio_data

    def get_config_template(self):
        """Returns the path to the visualizer's configuration template."""
        return "smooth_curves_form.html"
