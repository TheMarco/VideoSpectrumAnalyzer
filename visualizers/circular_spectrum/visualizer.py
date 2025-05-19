"""
Circular Spectrum visualizer implementation.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from core.base_visualizer import BaseVisualizer
from modules.audio_processor import load_audio
from modules.media_handler import load_background_media, process_video_frame, load_fonts
from modules.ffmpeg_handler import (
    setup_ffmpeg_process,
    write_frame_to_ffmpeg,
    finalize_ffmpeg_process,
    add_audio_to_video,
    cleanup_temp_files
)
from .config import process_config
from .gl_renderer import SimpleGLCircularRenderer

class CircularSpectrumVisualizer(BaseVisualizer):
    """
    Circular Spectrum Visualizer.
    This visualizer renders a circular spectrum analyzer using a GLSL shader.
    """
    name = "CircularSpectrumVisualizer"  # This must match the class name for proper registration
    display_name = "Circular Spectrum (GL)"   # This is what will be shown to users
    description = "Displays a circular audio spectrum analyzer with bars arranged in a ring using GL rendering."
    thumbnail = "static/images/thumbnails/circular_spectrum.jpg"  # Will need to be created

    def __init__(self):
        """Initialize the visualizer."""
        super().__init__()
        self.gl_renderer = None
        self.text_renderer = None
        self.audio_samples = None
        self.sample_rate = None
        self.total_frames = None
        self.samples_per_frame = None

    def process_config(self, config=None):
        """
        Process and validate the configuration for the circular spectrum visualizer.
        """
        return process_config(config if config is not None else {})

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
        # Create a text renderer for fallback and for rendering text on top of GL output
        self.text_renderer = CircularSpectrumTextRenderer(width, height, config)

        # Initialize GL renderer for the circular spectrum
        try:
            print("Attempting to initialize GL renderer...")
            self.gl_renderer = SimpleGLCircularRenderer(width, height, config)
            print("GL renderer initialized successfully")
            self.use_gl_renderer = True
        except Exception as e:
            print(f"Error initializing GL renderer: {e}")
            print("Falling back to PIL renderer")
            self.gl_renderer = None
            self.use_gl_renderer = False
            # Return the PIL renderer as fallback
            return self.text_renderer

        # Return the GL renderer as the primary renderer
        return self.gl_renderer

    def render_frame(self, renderer, frame_data, background_image, metadata):
        """
        Render a single frame.

        Args:
            renderer: Renderer instance
            frame_data (dict): Frame data (spectrum, peaks, etc.)
            background_image (PIL.Image): Background image
            metadata (dict): Additional metadata (artist, title, etc.)

        Returns:
            PIL.Image: Rendered frame
        """
        if "raw_audio_samples" not in frame_data:
            raise ValueError("Raw audio samples not found in frame_data.")

        # Extract data from frame_data
        frame_audio_data = frame_data["raw_audio_samples"]

        # Extract metadata
        artist_name = metadata.get("artist_name", "")
        track_title = metadata.get("track_title", "")

        # Check if we're using GL renderer or falling back to PIL
        if hasattr(self, 'use_gl_renderer') and self.use_gl_renderer and self.gl_renderer:
            try:
                # Render the circular spectrum using the GL renderer with background image
                print("Using GL renderer for circular spectrum")
                spectrum_image = self.gl_renderer.render_frame(frame_audio_data, background_image)

                # Create a blank image for text only
                text_image = Image.new("RGBA", (self.gl_renderer.width, self.gl_renderer.height), (0, 0, 0, 0))

                # Render text on the blank image
                if artist_name or track_title:
                    draw = ImageDraw.Draw(text_image)
                    fonts = load_fonts(self.gl_renderer.config.get("font_size", 24))

                    # Unpack fonts tuple (artist_font, title_font)
                    artist_font, title_font = fonts

                    # Draw track title at the top
                    if track_title:
                        title_color = self.gl_renderer.config.get("title_color", "#FFFFFF")
                        # Use textbbox instead of deprecated textsize
                        left, top, right, bottom = title_font.getbbox(track_title)
                        title_width, title_height = right - left, bottom - top
                        title_position = ((self.gl_renderer.width - title_width) // 2,
                                         self.gl_renderer.config.get("text_padding", 20))
                        draw.text(title_position, track_title, fill=title_color, font=title_font)

                    # Draw artist name at the bottom
                    if artist_name:
                        artist_color = self.gl_renderer.config.get("artist_color", "#FFFFFF")
                        # Use textbbox instead of deprecated textsize
                        left, top, right, bottom = artist_font.getbbox(artist_name)
                        artist_width, artist_height = right - left, bottom - top
                        artist_position = ((self.gl_renderer.width - artist_width) // 2,
                                          self.gl_renderer.height - artist_height -
                                          self.gl_renderer.config.get("text_padding", 20))
                        draw.text(artist_position, artist_name, fill=artist_color, font=artist_font)

                # Composite the text onto the spectrum image
                result = Image.alpha_composite(spectrum_image, text_image)
                print(f"Final composited result: size={result.size}, mode={result.mode}")

                return result
            except Exception as e:
                print(f"Error rendering with GL renderer: {e}")
                print("Falling back to PIL renderer for this frame")
                import traceback
                traceback.print_exc()
                # Fall back to PIL renderer
                return self.text_renderer.render_frame(frame_audio_data, background_image, metadata)
        else:
            # Use PIL renderer for everything
            print("Using PIL renderer for circular spectrum (GL renderer not available)")
            return self.text_renderer.render_frame(frame_audio_data, background_image, metadata)

    def update_frame_data(self, frame_data, frame_idx, config):
        """
        Update frame data for the current frame using spectrogram data.

        Args:
            frame_data (dict): Frame data to update
            frame_idx (int): Current frame index
            config (dict): Configuration dictionary
        """
        # Use mel spectrogram data for shader input
        mel_spec = frame_data.get("mel_spec_norm")
        if mel_spec is None:
            raise ValueError("Spectrogram data not found in frame_data for circular spectrum.")

        num_bars = int(config.get("num_bars", mel_spec.shape[0]))
        print(f"Mel spec shape: {mel_spec.shape}, num_bars: {num_bars}")

        # Extract spectrogram slice for this frame and trim to num_bars
        if frame_idx < mel_spec.shape[1]:
            spec_frame = mel_spec[:num_bars, frame_idx]
        else:
            spec_frame = mel_spec[:num_bars, -1]

        # Debug: Print stats about the spectrogram frame
        zero_count = np.sum(spec_frame == 0.0)
        print(f"Spectrogram frame stats - min: {np.min(spec_frame):.6f}, max: {np.max(spec_frame):.6f}, zeros: {zero_count}/{len(spec_frame)}")

        # Apply a small noise floor to ensure all bars have at least some minimal value
        # This helps identify if the issue is with zero values in the audio data
        spec_frame = np.maximum(spec_frame, 0.001)

        # Provide spectrogram values as audio samples for shader
        frame_data["raw_audio_samples"] = spec_frame.astype("float32")

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
        Create a visualization for an audio file, tailored for the circular spectrum.
        """
        # Process configuration
        conf = self.process_config(config)

        # Load audio file and get raw samples
        print(f"Loading audio file: {audio_file}")
        y, sr, audio_duration = load_audio(audio_file, duration=duration)
        self.audio_samples = y
        self.sample_rate = sr

        # Calculate frame details
        if duration is None:
            duration = audio_duration
        self.total_frames = int(duration * fps)
        self.samples_per_frame = int(sr / fps)

        # Call the base class's create_visualization to handle the rest of the process
        # Pass the loaded audio samples and calculated frame details
        return super().create_visualization(
            audio_file=audio_file, # Pass original audio file for audio merging
            output_file=output_file,
            background_image_path=background_image_path,
            background_video_path=background_video_path,
            background_shader_path=background_shader_path,
            artist_name=artist_name,
            track_title=track_title,
            duration=duration, # Pass duration to base class
            fps=fps,
            height=height,
            width=width,
            config=conf, # Pass processed config
            progress_callback=progress_callback,
        )

    def get_config_template(self):
        """Returns the path to the visualizer's configuration template."""
        return "circular_spectrum_form.html"


class CircularSpectrumTextRenderer:
    """
    Fallback PIL-based renderer for the Circular Spectrum visualizer.
    This is used when the GL renderer fails to initialize or for rendering text.
    """

    def __init__(self, width, height, config):
        """
        Initialize the text renderer.

        Args:
            width (int): Frame width
            height (int): Frame height
            config (dict): Configuration dictionary
        """
        self.width = width
        self.height = height
        self.config = config

    def render_frame(self, audio_data, background_image, metadata):
        """
        Render a frame using PIL.

        Args:
            audio_data (numpy.ndarray): Audio data for the current frame (not used in PIL renderer)
            background_image (PIL.Image): Background image
            metadata (dict): Additional metadata (artist, title, etc.)

        Returns:
            PIL.Image: Rendered frame
        """
        # Create a blank image if no background is provided
        if background_image is None:
            bg_color = self.config.get("background_color", (0, 0, 0))
            image = Image.new("RGBA", (self.width, self.height), bg_color + (255,))
        else:
            # Use the provided background image
            if background_image.mode != "RGBA":
                background_image = background_image.convert("RGBA")
            if background_image.size != (self.width, self.height):
                background_image = background_image.resize((self.width, self.height))
            image = background_image.copy()

        # Draw text
        artist_name = metadata.get("artist_name", "")
        track_title = metadata.get("track_title", "")

        if artist_name or track_title:
            draw = ImageDraw.Draw(image)
            fonts = load_fonts(self.config.get("font_size", 24))

            # Unpack fonts tuple (artist_font, title_font)
            artist_font, title_font = fonts

            # Draw track title at the top
            if track_title:
                title_color = self.config.get("title_color", "#FFFFFF")
                # Use textbbox instead of deprecated textsize
                left, top, right, bottom = title_font.getbbox(track_title)
                title_width, title_height = right - left, bottom - top
                title_position = ((self.width - title_width) // 2,
                                 self.config.get("text_padding", 20))
                draw.text(title_position, track_title, fill=title_color, font=title_font)

            # Draw artist name at the bottom
            if artist_name:
                artist_color = self.config.get("artist_color", "#FFFFFF")
                # Use textbbox instead of deprecated textsize
                left, top, right, bottom = artist_font.getbbox(artist_name)
                artist_width, artist_height = right - left, bottom - top
                artist_position = ((self.width - artist_width) // 2,
                                  self.height - artist_height -
                                  self.config.get("text_padding", 20))
                draw.text(artist_position, artist_name, fill=artist_color, font=artist_font)

        return image
