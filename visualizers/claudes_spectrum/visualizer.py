"""
Claude's Spectrum Visualizer - A horizontal spectrum analyzer with configurable bars and bloom effects.
"""

import numpy as np
import logging
from PIL import Image, ImageDraw, ImageFilter
from core.base_visualizer import BaseVisualizer
from .config import CLAUDES_SPECTRUM_CONFIG
from .webgl_renderer import ClaudesSpectrumGLRenderer
from modules.media_handler import load_fonts

logger = logging.getLogger(__name__)

class ClaudesSpectrumVisualizer(BaseVisualizer):
    def __init__(self):
        # Set attributes before calling super().__init__()
        self.name = "Claudes Spectrum"
        self.display_name = "Claude's Spectrum (GL)"
        self.description = "A horizontal spectrum analyzer with configurable bars, bloom effects, and color schemes"
        self.thumbnail = "static/images/thumbnails/claudes_spectrum.jpg"

        # Call parent constructor
        super().__init__()

        self.config = CLAUDES_SPECTRUM_CONFIG
        self.renderer = None

    def get_config_template(self):
        """Return the configuration template for this visualizer"""
        return "claudes_spectrum_form.html"

    def process_config(self, config=None):
        """Process and validate the configuration"""
        if config is None:
            config = {}

        # Start with defaults
        processed_config = self.config["defaults"].copy()

        # Override with user-provided values
        for key, value in config.items():
            if key in processed_config:
                # Type conversion based on the default type
                default_value = processed_config[key]
                if isinstance(default_value, bool):
                    # Handle checkbox values
                    if isinstance(value, str):
                        processed_config[key] = value.lower() in ('true', '1', 'on', 'yes')
                    else:
                        processed_config[key] = bool(value)
                elif isinstance(default_value, (int, float)):
                    try:
                        if isinstance(default_value, int):
                            processed_config[key] = int(float(value))
                        else:
                            processed_config[key] = float(value)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid value for {key}: {value}, using default")
                else:
                    processed_config[key] = value

        # Validate ranges - FIXED: Use pixel ranges for bar_width, bar_spacing, and center_line_thickness
        processed_config["bar_width"] = max(2, min(50, processed_config["bar_width"]))  # 2-50 pixels
        processed_config["bar_spacing"] = max(2, min(100, processed_config["bar_spacing"]))  # 2-100 pixels
        processed_config["center_line_thickness"] = max(1, min(10, processed_config["center_line_thickness"]))  # 1-10 pixels
        processed_config["max_bar_height"] = max(0.3, min(1.0, processed_config["max_bar_height"]))
        processed_config["num_bars"] = max(24, min(128, processed_config["num_bars"]))
        processed_config["waveform_width"] = max(0.5, min(1.0, processed_config["waveform_width"]))
        processed_config["bloom_size"] = max(5.0, min(50.0, processed_config["bloom_size"]))
        processed_config["bloom_intensity"] = max(0.1, min(2.0, processed_config["bloom_intensity"]))
        processed_config["bloom_falloff"] = max(0.5, min(4.0, processed_config["bloom_falloff"]))
        processed_config["color_scheme"] = max(0, min(5, processed_config["color_scheme"]))
        processed_config["log_scale_factor"] = max(0.1, min(1.0, processed_config["log_scale_factor"]))
        processed_config["center_line_overhang"] = max(0.0, min(0.1, processed_config["center_line_overhang"]))
        processed_config["sensitivity"] = max(0.5, min(3.0, processed_config["sensitivity"]))

        # Validate the configuration
        errors = self.validate_config(processed_config)
        if errors:
            raise ValueError(f"Configuration validation failed: {', '.join(errors)}")

        return processed_config

    def initialize_renderer(self, width, height, config):
        """Initialize the GL renderer for the spectrum visualizer and the PIL renderer for text."""
        # Load fonts for text rendering
        text_size = config.get("text_size", "large")
        print(f"Initializing renderer with text_size: {text_size}")
        self.artist_font, self.title_font = load_fonts(text_size=text_size)

        # Initialize PIL renderer for text only (reuse oscilloscope text renderer pattern)
        from visualizers.oscilloscope_waveform.renderer import OscilloscopeWaveformRenderer
        self.text_renderer = OscilloscopeWaveformRenderer(width, height, config, self.artist_font, self.title_font)

        # Initialize GL renderer for the spectrum visualization
        self.renderer = ClaudesSpectrumGLRenderer(width, height)
        if not self.renderer.initialize_gl(config):
            logger.error("Failed to initialize GL renderer, falling back to PIL-based renderer")
            # Create a fallback PIL-based renderer
            from .fallback_renderer import ClaudesSpectrumFallbackRenderer
            self.renderer = ClaudesSpectrumFallbackRenderer(width, height)
            logger.info("Using fallback PIL renderer for Claude's Spectrum visualization")
        else:
            logger.info("Successfully initialized GL renderer for Claude's Spectrum visualization")

        logger.info(f"Final renderer type: {type(self.renderer).__name__}")
        return self.renderer

    def render_frame(self, renderer, frame_data, background_image, metadata):
        """Render a single frame"""
        # Extract frequency data from frame_data
        frequency_data = frame_data.get('spectrum', np.zeros(64))
        time_seconds = frame_data.get('time', 0.0)

        # Debug logging to see what we're actually getting
        logger.info(f"ClaudesSpectrum render_frame: frequency_data shape: {frequency_data.shape}, min: {frequency_data.min():.3f}, max: {frequency_data.max():.3f}")
        logger.info(f"ClaudesSpectrum render_frame: Using renderer type: {type(renderer).__name__}")
        logger.debug(f"ClaudesSpectrum render_frame: frame_data keys: {list(frame_data.keys())}")

        # Create config from metadata
        config = metadata.get('config', {})

        # Render the visualization
        webgl_image = renderer.render_frame(frequency_data, config, time_seconds, background_image)

        # Check if GL renderer returned None and create fallback
        if webgl_image is None:
            logger.error("GL renderer returned None, creating fallback image")
            webgl_image = Image.new('RGBA', (renderer.width, renderer.height), (0, 0, 0, 255))

        # Debug: Log the image properties after ensuring it's not None
        logger.info(f"ClaudesSpectrum render_frame returning image: mode={webgl_image.mode}, size={webgl_image.size}")

        # Add text overlay if enabled
        show_text = config.get('show_text', True)
        if show_text:
            artist_name = metadata.get('artist_name', '')
            track_title = metadata.get('track_title', '')

            if artist_name or track_title:
                # Create text overlay using the oscilloscope text renderer pattern
                text_image = Image.new('RGBA', webgl_image.size, (0, 0, 0, 0))

                # Draw text glow first if enabled
                if hasattr(self.text_renderer, 'glow_effect') and self.text_renderer.glow_effect and hasattr(self.text_renderer, 'glow_color') and self.text_renderer.glow_color:
                    text_glow_layer = Image.new("RGBA", webgl_image.size, (0, 0, 0, 0))
                    self.text_renderer._draw_text_mask(text_glow_layer, artist_name, track_title)

                    # Apply blur to the text glow layer
                    from PIL import ImageFilter
                    text_glow_blurred = text_glow_layer.filter(ImageFilter.GaussianBlur(self.text_renderer.glow_blur_radius))

                    # Composite the text glow layer onto the text image
                    text_image = Image.alpha_composite(text_image, text_glow_blurred)

                # Draw the main text
                self.text_renderer._draw_text(text_image, artist_name, track_title)

                # Convert webgl_image to RGBA for compositing
                if webgl_image.mode != 'RGBA':
                    webgl_image = webgl_image.convert('RGBA')

                # Composite the text onto the visualization
                result = Image.alpha_composite(webgl_image, text_image)
                return result

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
            logger.info(f"ClaudesSpectrum: Input spectrum shape: {current_spectrum.shape}, target bands: {target_bands}")

            if len(current_spectrum) != target_bands:
                logger.info(f"ClaudesSpectrum: Resampling spectrum from {len(current_spectrum)} to {target_bands} bands")

                # Resample using linear interpolation
                x_old = np.linspace(0, 1, len(current_spectrum))
                x_new = np.linspace(0, 1, target_bands)
                current_spectrum = np.interp(x_new, x_old, current_spectrum)
                logger.info(f"ClaudesSpectrum: After resampling, spectrum shape: {current_spectrum.shape}")
            else:
                logger.info(f"ClaudesSpectrum: Spectrum already has correct size: {len(current_spectrum)} bands")

            # Ensure the spectrum is properly shaped and has some data
            current_spectrum = np.array(current_spectrum, dtype=np.float32)
            if len(current_spectrum) != target_bands:
                logger.error(f"ClaudesSpectrum: CRITICAL - Spectrum size mismatch after resampling: {len(current_spectrum)} != {target_bands}")
                current_spectrum = np.zeros(target_bands, dtype=np.float32)

            # Apply amplitude scaling and sensitivity
            amplitude_scale = conf.get('amplitude_scale', 1.0)
            sensitivity = conf.get('sensitivity', 1.0)
            current_spectrum = current_spectrum * amplitude_scale * sensitivity

            # Apply noise gate
            noise_gate = conf.get('noise_gate', 0.03)
            current_spectrum = np.where(current_spectrum < noise_gate, 0, current_spectrum)

            frame_data['spectrum'] = current_spectrum
            logger.info(f"ClaudesSpectrum: Final spectrum - shape: {current_spectrum.shape}, min: {current_spectrum.min():.3f}, max: {current_spectrum.max():.3f}")
        else:
            # Fallback to zeros if no spectrum data
            current_spectrum = np.zeros(target_bands, dtype=np.float32)
            frame_data['spectrum'] = current_spectrum
            logger.warning(f"ClaudesSpectrum: Using fallback spectrum with {target_bands} bands")

        # Add time information
        frame_data['time'] = frame_idx / conf.get('fps', 30)
        return frame_data

    def validate_config(self, config):
        """Validate the configuration parameters"""
        errors = []

        # Validate numeric ranges - FIXED: Use pixel ranges for bar_width, bar_spacing, and center_line_thickness
        numeric_validations = [
            ('bar_width', 2, 50),  # pixels
            ('bar_spacing', 2, 100),  # pixels
            ('center_line_thickness', 1, 10),  # pixels
            ('max_bar_height', 0.3, 1.0),
            ('num_bars', 24, 128),
            ('waveform_width', 0.5, 1.0),
            ('bloom_size', 5.0, 50.0),
            ('bloom_intensity', 0.1, 2.0),
            ('bloom_falloff', 0.5, 4.0),
            ('color_scheme', 0, 5),
            ('log_scale_factor', 0.1, 1.0),
            ('center_line_overhang', 0.0, 0.1),
            ('sensitivity', 0.5, 3.0),
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
        color_params = ['single_color', 'color_low', 'color_mid', 'color_high', 'center_line_color', 'text_color']
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
