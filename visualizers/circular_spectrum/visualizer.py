"""
Circular Spectrum visualizer implementation.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
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

                # Draw text with glow effect
                if (artist_name or track_title) and hasattr(self.text_renderer, '_draw_text'):
                    print(f"Drawing text with glow effect: artist='{artist_name}', title='{track_title}'")

                    # Create a text glow layer first if glow effect is enabled
                    if self.text_renderer.glow_effect and self.text_renderer.glow_color:
                        text_glow_layer = Image.new("RGBA", (self.gl_renderer.width, self.gl_renderer.height), (0, 0, 0, 0))
                        self.text_renderer._draw_text_mask(text_glow_layer, artist_name, track_title)

                        # Apply blur to the text glow layer
                        text_glow_blurred = text_glow_layer.filter(ImageFilter.GaussianBlur(self.text_renderer.glow_blur_radius))

                        # Composite the text glow layer onto the text image first
                        text_image = Image.alpha_composite(text_image, text_glow_blurred)

                    # Then draw the text on top of the glow
                    self.text_renderer._draw_text(text_image, artist_name, track_title)

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

        # Check for silence condition (all values are the same or very close)
        max_val = np.max(spec_frame)
        min_val = np.min(spec_frame)
        mean_val = np.mean(spec_frame)

        # Consider it silent if:
        # 1. All values are within a very small range (indicating no meaningful audio variation)
        # 2. All values are exactly 0.8 (specific case we're seeing in the logs)
        # 3. Mean value is very close to 0.8 (to catch slight variations around 0.8)
        is_silent = (max_val - min_val < 0.001) or \
                   (abs(max_val - 0.8) < 0.001 and abs(min_val - 0.8) < 0.001) or \
                   (abs(mean_val - 0.8) < 0.001)

        if is_silent:
            # Print which condition triggered the silence detection
            if max_val - min_val < 0.001:
                print(f"SILENCE DETECTED in audio data - all values are within a small range: min={min_val:.6f}, max={max_val:.6f}")
            elif abs(max_val - 0.8) < 0.001 and abs(min_val - 0.8) < 0.001:
                print(f"SILENCE DETECTED in audio data - all values are approximately 0.8: min={min_val:.6f}, max={max_val:.6f}")
            elif abs(mean_val - 0.8) < 0.001:
                print(f"SILENCE DETECTED in audio data - mean value is approximately 0.8: mean={mean_val:.6f}")

            # Print a sample of the values to help diagnose
            print(f"Sample values before zeroing: {spec_frame[:5]}")

            # For silence, set all values to 0 to ensure proper silence rendering
            spec_frame = np.zeros_like(spec_frame)
        else:
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

        # Glow effect parameters
        self.glow_effect = config.get("glow_effect", True)
        self.glow_color = self._parse_color(config.get("glow_color", config.get("segment_color", "#FFFFFF")))
        self.glow_blur_radius = int(config.get("glow_blur_radius", 3))

        # Font colors
        self.title_color_rgb = self._parse_color(config.get("title_color", "#FFFFFF"))
        self.artist_color_rgb = self._parse_color(config.get("artist_color", "#FFFFFF"))

        # Scale factor for high-resolution rendering
        self.scale_factor = max(1.0, min(width, height) / 720.0)

        # Scale glow blur radius based on resolution
        self.glow_blur_radius = int(self.glow_blur_radius * self.scale_factor)

        # Load fonts
        fonts = load_fonts(config.get("font_size", 24))
        self.artist_font, self.title_font = fonts

        # Store font sizes for positioning
        if self.artist_font:
            self.artist_font_size = getattr(self.artist_font, 'size', 36)
        else:
            self.artist_font_size = 36

        if self.title_font:
            self.title_font_size = getattr(self.title_font, 'size', 24)
        else:
            self.title_font_size = 24

    def _parse_color(self, color):
        """
        Parse a color value from various formats to an RGB tuple.

        Args:
            color: Can be a hex string ('#RRGGBB'), a tuple/list of RGB values (0-255),
                  or a tuple/list of normalized RGB values (0.0-1.0)

        Returns:
            tuple: (r, g, b) with values in 0-255 range
        """
        if isinstance(color, str) and color.startswith('#'):
            # Convert hex color string to RGB
            color = color.lstrip('#')
            if len(color) == 6:
                r = int(color[0:2], 16)
                g = int(color[2:4], 16)
                b = int(color[4:6], 16)
                return (r, g, b)
            else:
                print(f"Warning: Invalid hex color format: {color}, using default")
                return (255, 255, 255)  # Default white
        elif isinstance(color, (list, tuple)):
            # Check if it's already in 0-255 range
            if all(isinstance(c, int) and 0 <= c <= 255 for c in color):
                return tuple(color[:3])  # Return first 3 values (r,g,b)
            # Check if it's normalized (values between 0-1)
            elif all(isinstance(c, float) and 0.0 <= c <= 1.0 for c in color):
                return tuple(int(c * 255) for c in color[:3])
            else:
                print(f"Warning: Invalid color tuple format: {color}, using default")
                return (255, 255, 255)  # Default white
        else:
            print(f"Warning: Unsupported color format: {color}, using default")
            return (255, 255, 255)  # Default white

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

        # Draw text with glow effect
        artist_name = metadata.get("artist_name", "")
        track_title = metadata.get("track_title", "")

        if artist_name or track_title:
            # Create a text layer
            text_layer = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))

            # Create a text glow layer if glow effect is enabled
            if self.glow_effect and self.glow_color:
                text_glow_layer = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
                self._draw_text_mask(text_glow_layer, artist_name, track_title)

                # Apply blur to the text glow layer
                text_glow_blurred = text_glow_layer.filter(ImageFilter.GaussianBlur(self.glow_blur_radius))

                # Composite the text glow layer onto the result
                image = Image.alpha_composite(image, text_glow_blurred)

            # Draw the text on top of the glow
            self._draw_text(text_layer, artist_name, track_title)

            # Composite the text layer on top
            image = Image.alpha_composite(image, text_layer)

        return image

    def _draw_text(self, image, artist_name, track_title):
        """
        Draw artist name and track title on the image.

        Args:
            image (PIL.Image): Image to draw on
            artist_name (str): Artist name to display
            track_title (str): Track title to display
        """
        if not artist_name and not track_title:
            return

        draw = ImageDraw.Draw(image)
        fonts = load_fonts(self.config.get("font_size", 24))

        # Unpack fonts tuple (artist_font, title_font)
        artist_font, title_font = fonts

        # Position text at the bottom of the image with some padding (like oscilloscope)
        bottom_padding = 50
        artist_y = self.height - bottom_padding - (self.title_font_size if track_title else 0) - (self.artist_font_size if self.artist_font else 0)

        # Draw artist name first (at the bottom)
        if artist_name and artist_font:
            artist_color_rgba = self.artist_color_rgb + (255,)
            try:
                # For newer PIL versions
                artist_text_width = draw.textlength(artist_name, font=artist_font)
            except AttributeError:
                # For older PIL versions
                artist_text_width = artist_font.getlength(artist_name)
            artist_x = (self.width - artist_text_width) // 2
            draw.text((artist_x, artist_y), artist_name, fill=artist_color_rgba, font=artist_font)

        # Draw track title below artist name
        if track_title and title_font:
            title_color_rgba = self.title_color_rgb + (255,)
            try:
                # For newer PIL versions
                title_text_width = draw.textlength(track_title, font=title_font)
            except AttributeError:
                # For older PIL versions
                title_text_width = title_font.getlength(track_title)
            title_x = (self.width - title_text_width) // 2

            # Adjust spacing between artist and title based on font size
            spacing = 5 if self.artist_font_size < 40 else 10
            title_y = artist_y + (self.artist_font_size + spacing if artist_name and artist_font else 0)

            draw.text((title_x, title_y), track_title, fill=title_color_rgba, font=title_font)

    def _draw_text_mask(self, image, artist_name, track_title):
        """
        Draw artist name and track title as a mask for glow effect.
        Uses exactly the same font and positioning as the regular text.

        Args:
            image (PIL.Image): Image to draw on
            artist_name (str): Artist name to display
            track_title (str): Track title to display
        """
        if not artist_name and not track_title:
            return

        draw = ImageDraw.Draw(image)
        fonts = load_fonts(self.config.get("font_size", 24))

        # Unpack fonts tuple (artist_font, title_font)
        artist_font, title_font = fonts

        # Use the glow color with full opacity for the mask
        glow_color = self.glow_color + (255,)

        # Position text at the bottom of the image with some padding - MUST MATCH _draw_text method
        bottom_padding = 50
        artist_y = self.height - bottom_padding - (self.title_font_size if track_title else 0) - (self.artist_font_size if self.artist_font else 0)

        # Draw artist name first (at the bottom)
        if artist_name and artist_font:
            try:
                # For newer PIL versions
                artist_text_width = draw.textlength(artist_name, font=artist_font)
            except AttributeError:
                # For older PIL versions
                artist_text_width = artist_font.getlength(artist_name)
            artist_x = (self.width - artist_text_width) // 2
            draw.text((artist_x, artist_y), artist_name, fill=glow_color, font=artist_font)

        # Draw track title below artist name
        if track_title and title_font:
            try:
                # For newer PIL versions
                title_text_width = draw.textlength(track_title, font=title_font)
            except AttributeError:
                # For older PIL versions
                title_text_width = title_font.getlength(track_title)
            title_x = (self.width - title_text_width) // 2

            # Adjust spacing between artist and title based on font size - MUST MATCH _draw_text method
            spacing = 5 if self.artist_font_size < 40 else 10
            title_y = artist_y + (self.artist_font_size + spacing if artist_name and artist_font else 0)

            draw.text((title_x, title_y), track_title, fill=glow_color, font=title_font)
