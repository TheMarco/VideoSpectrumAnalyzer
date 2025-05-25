"""
Fallback PIL-based renderer for Claude's Spectrum visualizer when GL fails.
"""

import numpy as np
import math
from PIL import Image, ImageDraw, ImageFilter
import logging

logger = logging.getLogger(__name__)

class ClaudesSpectrumFallbackRenderer:
    """Fallback PIL-based renderer for Claude's Spectrum visualization"""

    def __init__(self, width, height):
        self.width = int(width)
        self.height = int(height)
        logger.info(f"Initialized fallback PIL renderer: {self.width}x{self.height}")

    def render_frame(self, frequency_data, config, time_seconds, background_image=None):
        """Render a single frame using PIL."""
        try:
            # Create base image
            if background_image:
                image = background_image.resize((self.width, self.height), Image.LANCZOS)
                if image.mode != 'RGBA':
                    image = image.convert('RGBA')
            else:
                image = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 255))

            draw = ImageDraw.Draw(image)

            # Create separate layers for efficient glow rendering
            bars_layer = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
            bars_draw = ImageDraw.Draw(bars_layer)

            # Create glow layer if bloom is enabled
            glow_layer = None
            glow_draw = None
            bloom_intensity = config.get('bloom_intensity', 0.3)
            if bloom_intensity > 0:
                glow_layer = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
                glow_draw = ImageDraw.Draw(glow_layer)

            # Get configuration values
            bar_width = config.get('bar_width', 0.008) * self.width
            bar_spacing = config.get('bar_spacing', 0.014) * self.width
            max_bar_height = config.get('max_bar_height', 0.7) * self.height
            num_bars = int(config.get('num_bars', 48))
            waveform_width = config.get('waveform_width', 0.8)
            sensitivity = config.get('sensitivity', 1.0)
            color_scheme = int(config.get('color_scheme', 0))
            show_center_line = config.get('show_center_line', True)
            center_line_thickness = config.get('center_line_thickness', 0.006) * self.height
            center_line_overhang = config.get('center_line_overhang', 0.05) * self.width

            # Calculate positioning
            total_width = waveform_width * self.width
            available_width = total_width - num_bars * bar_width
            actual_spacing = min(bar_spacing, available_width / max(1, num_bars - 1))

            actual_waveform_width = num_bars * bar_width + (num_bars - 1) * actual_spacing
            start_x = (self.width - actual_waveform_width) / 2
            center_y = self.height / 2

            # Draw center line if enabled
            if show_center_line:
                line_start_x = max(0, start_x - center_line_overhang)
                line_end_x = min(self.width, start_x + actual_waveform_width + center_line_overhang)

                center_line_color = self._hex_to_rgb(config.get('center_line_color', '#999999'))

                draw.rectangle([
                    line_start_x,
                    center_y - center_line_thickness / 2,
                    line_end_x,
                    center_y + center_line_thickness / 2
                ], fill=center_line_color)

            # Prepare frequency data
            if len(frequency_data) == 0:
                frequency_data = np.zeros(num_bars)
            else:
                # Resample to match number of bars
                if len(frequency_data) != num_bars:
                    indices = np.linspace(0, len(frequency_data) - 1, num_bars)
                    frequency_data = np.interp(indices, np.arange(len(frequency_data)), frequency_data)

                # Apply sensitivity and scaling
                frequency_data = frequency_data * sensitivity

                # Apply logarithmic scaling if enabled
                if config.get('use_logarithmic_scale', True):
                    log_scale_factor = config.get('log_scale_factor', 0.5)
                    # Apply logarithmic scaling similar to the shader
                    frequency_data = np.power(frequency_data, log_scale_factor)

                frequency_data = np.clip(frequency_data, 0.0, 1.0)

            # Draw frequency bars
            for i in range(num_bars):
                freq = frequency_data[i] if i < len(frequency_data) else 0.0

                # Calculate bar position
                bar_center_x = start_x + i * (bar_width + actual_spacing) + bar_width / 2
                bar_height = freq * max_bar_height

                # Ensure minimum bar height
                bar_height = max(bar_height, bar_width)

                # Get bar color
                bar_color = self._get_bar_color(i, num_bars, color_scheme, config)

                # Draw the bar (rounded rectangle approximation)
                left = bar_center_x - bar_width / 2
                right = bar_center_x + bar_width / 2
                top = center_y - bar_height / 2
                bottom = center_y + bar_height / 2

                # Draw main bar to bars layer
                bars_draw.rectangle([left, top, right, bottom], fill=bar_color)

                # Add to glow layer if enabled (much more efficient!)
                if glow_layer and glow_draw:
                    glow_size = config.get('bloom_size', 12.0)
                    glow_expand = glow_size / 2
                    glow_left = left - glow_expand
                    glow_right = right + glow_expand
                    glow_top = top - glow_expand
                    glow_bottom = bottom + glow_expand

                    # Use a semi-transparent version of the bar color for glow
                    glow_alpha = int(255 * bloom_intensity * 0.8)
                    glow_color = bar_color[:3] + (glow_alpha,)

                    # Draw to glow layer (no blur yet - we'll blur the entire layer once)
                    glow_draw.rectangle([glow_left, glow_top, glow_right, glow_bottom], fill=glow_color)

            # Apply efficient glow effect (single blur operation for all bars!)
            if glow_layer:
                bloom_size = config.get('bloom_size', 12.0)
                glow_blurred = glow_layer.filter(ImageFilter.GaussianBlur(radius=bloom_size / 3))

                # Composite glow layer first (underneath bars)
                image = Image.alpha_composite(image, glow_blurred)

            # Composite bars layer on top
            image = Image.alpha_composite(image, bars_layer)

            # Ensure we're returning RGBA
            if image.mode != 'RGBA':
                image = image.convert('RGBA')

            # Debug: Log the image properties
            logger.info(f"Fallback renderer returning image: mode={image.mode}, size={image.size}")

            return image

        except Exception as e:
            logger.error(f"Error in fallback renderer: {e}")
            # Return a black image as fallback
            return Image.new('RGBA', (self.width, self.height), (0, 0, 0, 255))

    def _get_bar_color(self, bar_index, num_bars, color_scheme, config):
        """Get the color for a specific bar based on the color scheme."""
        t = bar_index / max(1, num_bars - 1)

        if color_scheme == 0:  # Gradient (Red-Yellow-Blue)
            color_low = self._hex_to_rgb(config.get('color_low', '#ff3319'))
            color_mid = self._hex_to_rgb(config.get('color_mid', '#ffff33'))
            color_high = self._hex_to_rgb(config.get('color_high', '#3366ff'))

            if t < 0.5:
                return self._lerp_color(color_low, color_mid, t * 2.0)
            else:
                return self._lerp_color(color_mid, color_high, (t - 0.5) * 2.0)

        elif color_scheme == 1:  # Single color
            return self._hex_to_rgb(config.get('single_color', '#ffffff'))

        elif color_scheme == 2:  # Rainbow
            return self._hsv_to_rgb(t * 0.8, 1.0, 1.0)

        elif color_scheme == 3:  # Purple gradient
            dark_purple = (77, 26, 128)
            bright_purple = (204, 102, 255)
            return self._lerp_color(dark_purple, bright_purple, t)

        elif color_scheme == 4:  # Green gradient
            dark_green = (26, 77, 26)
            bright_green = (102, 255, 102)
            return self._lerp_color(dark_green, bright_green, t)

        elif color_scheme == 5:  # Blue gradient
            dark_blue = (26, 51, 128)
            bright_blue = (102, 204, 255)
            return self._lerp_color(dark_blue, bright_blue, t)

        # Fallback
        return (255, 255, 255)

    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    def _lerp_color(self, color1, color2, t):
        """Linear interpolation between two colors."""
        t = max(0.0, min(1.0, t))
        return tuple(int(color1[i] + (color2[i] - color1[i]) * t) for i in range(3))

    def _hsv_to_rgb(self, h, s, v):
        """Convert HSV to RGB."""
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return (int(r * 255), int(g * 255), int(b * 255))

    def cleanup(self):
        """Clean up resources (no-op for PIL renderer)."""
        pass
