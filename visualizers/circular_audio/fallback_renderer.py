"""
Fallback PIL-based renderer for circular audio visualizer when GL fails.
"""

import numpy as np
import math
from PIL import Image, ImageDraw, ImageFilter
import logging

logger = logging.getLogger(__name__)

class CircularAudioFallbackRenderer:
    """Fallback PIL-based renderer for circular audio visualization"""

    def __init__(self, width, height):
        self.width = int(width)
        self.height = int(height)
        logger.info(f"Initialized fallback PIL renderer: {self.width}x{self.height}")

    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple (0-255 range)"""
        if isinstance(hex_color, str) and hex_color:
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        elif isinstance(hex_color, (list, tuple)) and len(hex_color) >= 3:
            return tuple(int(x) for x in hex_color[:3])
        else:
            # Fallback to white if no valid color provided
            logger.warning(f"Invalid color value: {hex_color}, using white fallback")
            return (255, 255, 255)  # Default to white

    def render_frame(self, frequency_data, config, time_seconds=0.0, background_frame=None):
        """Render a single frame using PIL"""
        try:
            # Create base image
            if background_frame:
                img = background_frame.copy()
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                if img.size != (self.width, self.height):
                    img = img.resize((self.width, self.height), Image.LANCZOS)
            else:
                img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 255))

            # Create overlay for the visualization
            overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            # Get configuration
            sensitivity = config.get('sensitivity', 1.4)
            segment_size = config.get('segment_size', 1.0)
            brightness = config.get('brightness', 3.5)
            inner_radius = config.get('inner_radius', 0.05)
            scale = config.get('scale', 1.5)
            base_color = self.hex_to_rgb(config.get('base_color'))
            hot_color = self.hex_to_rgb(config.get('hot_color'))

            # Calculate center and scaling
            center_x = self.width // 2
            center_y = self.height // 2
            max_radius = min(self.width, self.height) // 2

            # Apply scale
            max_radius = int(max_radius / scale)

            # Visualization parameters
            num_bands = min(len(frequency_data), 64)
            num_segments = 15
            inner_radius_px = int(inner_radius * max_radius)
            segment_height = int(0.02 * segment_size * max_radius)

            # Draw each frequency band
            for band_idx in range(num_bands):
                if band_idx >= len(frequency_data):
                    continue

                # Get amplitude for this band
                amplitude = frequency_data[band_idx] * sensitivity
                amplitude = min(amplitude, 1.0)

                # Calculate angle for this band
                angle_start = (band_idx / num_bands) * 2 * math.pi
                angle_end = ((band_idx + 1) / num_bands) * 2 * math.pi
                angle_mid = (angle_start + angle_end) / 2

                # Calculate how many segments to light up
                lit_segments = int(amplitude * num_segments)

                # Draw segments for this band
                for seg in range(lit_segments):
                    # Calculate segment position
                    seg_inner = inner_radius_px + seg * segment_height
                    seg_outer = seg_inner + segment_height - 2  # Small gap

                    # Calculate color based on segment height and amplitude
                    height_ratio = seg / num_segments
                    color_mix_factor = amplitude * 0.8 + height_ratio * 0.2

                    # Mix colors
                    r = int(base_color[0] * (1 - color_mix_factor) + hot_color[0] * color_mix_factor)
                    g = int(base_color[1] * (1 - color_mix_factor) + hot_color[1] * color_mix_factor)
                    b = int(base_color[2] * (1 - color_mix_factor) + hot_color[2] * color_mix_factor)

                    # Apply brightness
                    brightness_factor = brightness * (0.5 + amplitude * 0.5) / 8.0
                    r = min(255, int(r * brightness_factor))
                    g = min(255, int(g * brightness_factor))
                    b = min(255, int(b * brightness_factor))

                    color = (r, g, b, 255)

                    # Draw arc segment
                    # Calculate bounding box for the arc
                    bbox_inner = [
                        center_x - seg_inner, center_y - seg_inner,
                        center_x + seg_inner, center_y + seg_inner
                    ]
                    bbox_outer = [
                        center_x - seg_outer, center_y - seg_outer,
                        center_x + seg_outer, center_y + seg_outer
                    ]

                    # Convert angles to degrees
                    start_deg = math.degrees(angle_start)
                    end_deg = math.degrees(angle_end)

                    # Draw the segment as a thick arc
                    # PIL doesn't have direct arc drawing, so we'll draw lines
                    num_lines = max(3, int((end_deg - start_deg) * 2))
                    for i in range(num_lines):
                        line_angle = angle_start + (angle_end - angle_start) * i / num_lines

                        # Calculate line endpoints
                        x1 = center_x + seg_inner * math.cos(line_angle)
                        y1 = center_y + seg_inner * math.sin(line_angle)
                        x2 = center_x + seg_outer * math.cos(line_angle)
                        y2 = center_y + seg_outer * math.sin(line_angle)

                        # Draw line with some width
                        line_width = max(1, segment_height // 4)
                        draw.line([(x1, y1), (x2, y2)], fill=color, width=line_width)

            # Apply bloom effect if enabled
            bloom_intensity = config.get('bloom_intensity', 0.7)
            bloom_size = config.get('bloom_size', 4.5)

            if bloom_intensity > 0:
                # Create bloom layer
                bloom_overlay = overlay.copy()
                bloom_overlay = bloom_overlay.filter(ImageFilter.GaussianBlur(bloom_size))

                # Reduce bloom opacity
                bloom_alpha = Image.new('L', bloom_overlay.size, int(255 * bloom_intensity * 0.5))
                bloom_overlay.putalpha(bloom_alpha)

                # Composite bloom under main overlay
                temp_img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
                temp_img = Image.alpha_composite(temp_img, bloom_overlay)
                overlay = Image.alpha_composite(temp_img, overlay)

            # Composite visualization onto background
            result = Image.alpha_composite(img, overlay)

            logger.debug(f"Fallback renderer: Generated frame with {num_bands} bands, max amplitude: {max(frequency_data) if len(frequency_data) > 0 else 0:.3f}")

            return result

        except Exception as e:
            logger.error(f"Error in fallback renderer: {e}")
            # Return black image on error
            return Image.new('RGBA', (self.width, self.height), (0, 0, 0, 255))

    def cleanup(self):
        """Clean up resources (nothing to clean up for PIL renderer)"""
        pass
