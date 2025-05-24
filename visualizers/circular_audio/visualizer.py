"""
Circular Audio Visualizer - A circular audio visualizer with configurable segments and bloom effects.
"""

import numpy as np
import logging
from PIL import Image, ImageDraw, ImageFilter
from core.base_visualizer import BaseVisualizer
from .config import CIRCULAR_AUDIO_CONFIG
from .webgl_renderer import CircularAudioGLRenderer
from modules.media_handler import load_fonts

logger = logging.getLogger(__name__)

class CircularAudioVisualizer(BaseVisualizer):
    def __init__(self):
        # Set attributes before calling super().__init__()
        self.name = "Circular Audio"
        self.display_name = "Circular Audio (GL)"
        self.description = "A circular audio visualizer with configurable segments and bloom effects"
        self.thumbnail = "static/images/thumbnails/circular_audio.jpg"

        # Call parent constructor
        super().__init__()

        self.config = CIRCULAR_AUDIO_CONFIG
        self.renderer = None

    def get_config_template(self):
        """Return the configuration template for this visualizer"""
        return "circular_audio_form.html"

    def process_config(self, config=None):
        """Process and validate the configuration"""
        if config is None:
            config = {}

        # Start with defaults
        processed_config = self.config["defaults"].copy()

        # Process and convert form data types
        if config and isinstance(config, dict):
            # Process numeric values
            numeric_keys = [
                "sensitivity", "segment_size", "brightness", "bloom_size",
                "bloom_intensity", "bloom_falloff", "segment_gap", "fps",
                "height", "n_bars", "amplitude_scale", "decay_speed",
                "attack_speed", "noise_gate", "inner_radius", "scale",
                "glow_blur_radius", "duration"
            ]
            for key in numeric_keys:
                if key in config:
                    try:
                        processed_config[key] = float(config[key])
                        # Convert n_bars to int specifically
                        if key == "n_bars":
                            processed_config[key] = int(float(config[key]))
                        # Handle duration special case - if 0, set to None
                        elif key == "duration" and processed_config[key] == 0:
                            processed_config[key] = None
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid numeric value for {key}: {config[key]}")

            # Process boolean values
            bool_keys = ["use_log_scale", "show_text"]
            for key in bool_keys:
                if key in config:
                    if isinstance(config[key], str):
                        processed_config[key] = config[key].lower() in ("true", "on", "yes", "1")
                    else:
                        processed_config[key] = bool(config[key])

            # Process string values that should be preserved as-is
            string_keys = ["text_size", "text_color", "base_color", "hot_color", "glow_effect",
                          "background_shader", "artist_name", "track_title", "background_shader_path"]
            for key in string_keys:
                if key in config:
                    processed_config[key] = config[key]

            # Process other important keys that should be preserved
            other_keys = ["width"]  # width is important and should be preserved
            for key in other_keys:
                if key in config:
                    try:
                        processed_config[key] = int(float(config[key]))
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid value for {key}: {config[key]}")



        # Validate the configuration
        errors = self.validate_config(processed_config)
        if errors:
            raise ValueError(f"Configuration validation failed: {', '.join(errors)}")

        return processed_config

    def initialize_renderer(self, width, height, config):
        """Initialize the GL renderer for the circular visualizer and the PIL renderer for text."""
        # Load fonts for text rendering
        text_size = config.get("text_size", "large")
        print(f"Initializing renderer with text_size: {text_size}")
        self.artist_font, self.title_font = load_fonts(text_size=text_size)

        # Initialize PIL renderer for text only (reuse oscilloscope text renderer pattern)
        from visualizers.oscilloscope_waveform.renderer import OscilloscopeWaveformRenderer
        self.text_renderer = OscilloscopeWaveformRenderer(width, height, config, self.artist_font, self.title_font)

        # Initialize GL renderer for the circular visualization
        self.renderer = CircularAudioGLRenderer(width, height)
        if not self.renderer.initialize_gl():
            logger.error("Failed to initialize GL renderer, falling back to PIL-based renderer")
            # Create a fallback PIL-based renderer
            from .fallback_renderer import CircularAudioFallbackRenderer
            self.renderer = CircularAudioFallbackRenderer(width, height)
            logger.info("Using fallback PIL renderer for circular audio visualization")
        return self.renderer

    def render_frame(self, renderer, frame_data, background_image, metadata):
        """Render a single frame"""
        # Extract frequency data from frame_data
        frequency_data = frame_data.get('spectrum', np.zeros(64))
        time_seconds = frame_data.get('time', 0.0)

        # Debug logging to see what we're actually getting
        logger.info(f"CircularAudio render_frame: frequency_data shape: {frequency_data.shape}, min: {frequency_data.min():.3f}, max: {frequency_data.max():.3f}")
        logger.debug(f"CircularAudio render_frame: frame_data keys: {list(frame_data.keys())}")

        # Create config from metadata
        config = metadata.get('config', {})



        # Render the GL visualization
        webgl_image = renderer.render_frame(frequency_data, config, time_seconds, background_image)

        # Add text overlay if enabled and metadata is provided
        if config.get("show_text", True) and metadata and hasattr(self, 'artist_font') and hasattr(self, 'title_font'):
            # Get artist and track title from metadata
            artist_name = metadata.get("artist_name", "")
            track_title = metadata.get("track_title", "")

            if (artist_name or track_title) and (self.artist_font or self.title_font):
                # Parse text color from config
                def hex_to_rgba(hex_color):
                    """Convert hex color to RGBA tuple"""
                    if isinstance(hex_color, str) and hex_color.startswith('#') and len(hex_color) == 7:
                        hex_color = hex_color.lstrip('#')
                        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4)) + (255,)
                    return (255, 255, 255, 255)  # Default to white

                text_color = hex_to_rgba(config.get("text_color", "#ffffff"))
                glow_effect = config.get("glow_effect", "black")
                glow_blur_radius = int(config.get("glow_blur_radius", 3))

                # Calculate text positions (bottom of screen like other GL visualizers)
                artist_y = renderer.height - 80
                title_y = renderer.height - 40

                # Create the final text overlay
                text_overlay = Image.new('RGBA', (renderer.width, renderer.height), (0, 0, 0, 0))

                # Create glow layer first if glow effect is enabled
                if glow_effect and glow_effect != "none":
                    glow_layer = Image.new('RGBA', (renderer.width, renderer.height), (0, 0, 0, 0))
                    glow_draw = ImageDraw.Draw(glow_layer)

                    # Draw artist name with glow
                    if artist_name and self.artist_font:
                        glow_color = (0, 0, 0, 255) if glow_effect == "black" else (255, 255, 255, 255)
                        glow_draw.text((renderer.width // 2, artist_y), artist_name,
                                      fill=glow_color, font=self.artist_font, anchor="ms")

                    # Draw track title with glow
                    if track_title and self.title_font:
                        glow_color = (0, 0, 0, 255) if glow_effect == "black" else (255, 255, 255, 255)
                        glow_draw.text((renderer.width // 2, title_y), track_title,
                                      fill=glow_color, font=self.title_font, anchor="ms")

                    # Apply blur to the glow layer
                    glow_layer_blurred = glow_layer.filter(ImageFilter.GaussianBlur(glow_blur_radius))

                    # Composite the glow layer onto the text overlay first
                    text_overlay = Image.alpha_composite(text_overlay, glow_layer_blurred)

                # Create a separate layer for the main text (on top of glow)
                main_text_layer = Image.new('RGBA', (renderer.width, renderer.height), (0, 0, 0, 0))
                main_text_draw = ImageDraw.Draw(main_text_layer)

                # Draw the actual text on the main text layer
                if artist_name and self.artist_font:
                    main_text_draw.text((renderer.width // 2, artist_y), artist_name,
                                       fill=text_color, font=self.artist_font, anchor="ms")

                if track_title and self.title_font:
                    main_text_draw.text((renderer.width // 2, title_y), track_title,
                                       fill=text_color, font=self.title_font, anchor="ms")

                # Composite the main text layer on top of the glow
                text_overlay = Image.alpha_composite(text_overlay, main_text_layer)

                # Composite the complete text overlay onto the GL image
                webgl_image = Image.alpha_composite(webgl_image, text_overlay)

        return webgl_image

    def update_frame_data(self, frame_data, frame_idx, conf):
        """Update frame data for the current frame"""
        # Extract spectrum data from mel_spec_norm like other visualizers
        mel_spec_norm = frame_data.get("mel_spec_norm")
        target_bands = conf.get('n_bars', 64)

        if mel_spec_norm is not None and frame_idx < mel_spec_norm.shape[1]:
            # Get current spectrum frame
            current_spectrum = mel_spec_norm[:, frame_idx].copy()

            # ALWAYS resample to ensure we have exactly the right number of bands
            logger.info(f"CircularAudio: Input spectrum shape: {current_spectrum.shape}, target bands: {target_bands}")

            if len(current_spectrum) != target_bands:
                logger.info(f"CircularAudio: Resampling spectrum from {len(current_spectrum)} to {target_bands} bands")

                # Resample using linear interpolation
                x_old = np.linspace(0, 1, len(current_spectrum))
                x_new = np.linspace(0, 1, target_bands)
                current_spectrum = np.interp(x_new, x_old, current_spectrum)
                logger.info(f"CircularAudio: After resampling, spectrum shape: {current_spectrum.shape}")
            else:
                logger.info(f"CircularAudio: Spectrum already has correct size: {len(current_spectrum)} bands")

            # Ensure the spectrum is properly shaped and has some data
            current_spectrum = np.array(current_spectrum, dtype=np.float32)
            if len(current_spectrum) != target_bands:
                logger.error(f"CircularAudio: CRITICAL - Spectrum size mismatch after resampling: {len(current_spectrum)} != {target_bands}")
                current_spectrum = np.zeros(target_bands, dtype=np.float32)

            frame_data['spectrum'] = current_spectrum
            logger.info(f"CircularAudio: Final spectrum - shape: {current_spectrum.shape}, min: {current_spectrum.min():.3f}, max: {current_spectrum.max():.3f}")
        else:
            # Fallback to zeros if no spectrum data
            current_spectrum = np.zeros(target_bands, dtype=np.float32)
            frame_data['spectrum'] = current_spectrum
            logger.warning(f"CircularAudio: Using fallback spectrum with {target_bands} bands")

        # Add time information
        frame_data['time'] = frame_idx / conf.get('fps', 30)
        return frame_data

    def validate_config(self, config):
        """Validate the configuration parameters"""
        errors = []

        # Validate numeric ranges
        numeric_validations = [
            ('sensitivity', 0.5, 5.0),
            ('segment_size', 0.5, 2.0),
            ('brightness', 1.0, 8.0),
            ('bloom_size', 1.0, 15.0),
            ('bloom_intensity', 0.1, 2.0),
            ('bloom_falloff', 1.0, 4.0),
            ('segment_gap', 0.0, 3.0),
            ('fps', 1, 120),
            ('height', 360, 2160),
        ]

        for param, min_val, max_val in numeric_validations:
            if param in config:
                try:
                    value = float(config[param])
                    if not (min_val <= value <= max_val):
                        errors.append(f"{param} must be between {min_val} and {max_val}")
                except (ValueError, TypeError):
                    errors.append(f"{param} must be a valid number")

        # Validate colors
        color_params = ['base_color', 'hot_color', 'text_color']
        for param in color_params:
            if param in config:
                color = config[param]
                if not (isinstance(color, str) and color.startswith('#') and len(color) == 7):
                    errors.append(f"{param} must be a valid hex color (e.g., #ff0000)")

        return errors

    def cleanup(self):
        """Clean up resources"""
        if self.renderer:
            self.renderer.cleanup()
            self.renderer = None
