"""
Rendering functions for the dual bar visualizer.
"""
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np
from core.utils import hex_to_rgb

class DualBarRenderer:
    """
    Class for rendering dual bar visualizer frames.
    """

    def __init__(self, width, height, config, artist_font=None, title_font=None):
        """
        Initialize the renderer.

        Args:
            width (int): Frame width
            height (int): Frame height
            config (dict): Configuration dictionary
            artist_font: Font for artist name
            title_font: Font for track title
        """
        self.width = width
        self.height = height
        self.config = config
        self.artist_font = artist_font
        self.title_font = title_font

        # Add resolution scaling factor
        self.base_resolution = 1280  # Base width for scaling calculations
        self.scale_factor = width / self.base_resolution
        
        # Scale parameters based on resolution
        self.bar_width = int(config["bar_width"] * self.scale_factor)
        self.bar_gap = int(config["bar_gap"] * self.scale_factor)
        self.max_amplitude = int(config["max_amplitude"] * self.scale_factor)
        
        # Scale text sizes based on resolution
        self.text_spacing = int(20 * self.scale_factor)  # Distance between visualizer and text
        
        # Scale font sizes if fonts are provided
        if artist_font:
            self.artist_font_size = int(getattr(artist_font, 'size', 36) * self.scale_factor)
            # Create new font with scaled size
            artist_font_path = artist_font.path if hasattr(artist_font, 'path') else None
            if artist_font_path:
                self.artist_font = ImageFont.truetype(artist_font_path, self.artist_font_size)
        else:
            self.artist_font_size = int(36 * self.scale_factor)
            
        if title_font:
            self.title_font_size = int(getattr(title_font, 'size', 24) * self.scale_factor)
            # Create new font with scaled size
            title_font_path = title_font.path if hasattr(title_font, 'path') else None
            if title_font_path:
                self.title_font = ImageFont.truetype(title_font_path, self.title_font_size)
        else:
            self.title_font_size = int(24 * self.scale_factor)
            
        self.text_spacing_between = int(10 * self.scale_factor)  # Space between artist and title text
        self.max_text_height = self.artist_font_size + self.title_font_size + self.text_spacing_between

        # Extract configuration values
        self.n_bars = config["n_bars"]
        self.corner_radius = min(config["corner_radius"], self.bar_width // 2)
        self.corner_radius = max(0, self.corner_radius)
        self.noise_gate = config["noise_gate"]
        self.effective_amplitude_scale = config["effective_amplitude_scale"]
        
        # Ensure pil_alpha is properly set
        self.pil_alpha = config.get("pil_alpha", 153)  # Default to 0.6 * 255 if not set
        
        self.bar_color_rgb = config["bar_color_rgb"]
        self.artist_color_rgb = config["artist_color_rgb"]
        self.title_color_rgb = config["title_color_rgb"]
        self.background_color = config["background_color"]
        self.glow_effect = config["glow_effect"]
        self.glow_blur_radius = config["glow_blur_radius"]
        self.signal_power = config.get("signal_power", 2.5)  # Get the signal power parameter
        self.glow_color_rgb = config["glow_color_rgb"]
        self.visualizer_placement = config.get("visualizer_placement", "center")

        # Center line configuration
        center_line_color = config.get("center_line_color", "match_bar")
        if center_line_color == "match_bar":
            self.center_line_color = self.bar_color_rgb
        else:
            self.center_line_color = hex_to_rgb(center_line_color)
        self.center_line_thickness = config.get("center_line_thickness", 3)
        self.center_line_extension = config.get("center_line_extension", 25)

        # Edge rolloff configuration
        self.edge_rolloff = config.get("edge_rolloff", True)
        self.edge_rolloff_factor = config.get("edge_rolloff_factor", 0.4)

        # Calculate total width of all bars
        self.total_bar_width_gap = self.bar_width + self.bar_gap
        total_width = self.n_bars * self.total_bar_width_gap - self.bar_gap

        # Center the bars horizontally
        self.start_x = (width - total_width) // 2

        # Determine vertical position based on placement
        # Always reserve space for text
        text_height = self.max_text_height + self.text_spacing * 2

        if self.visualizer_placement == "bottom":
            # Position at bottom with space for text
            self.center_y = height - 50 - text_height - self.max_amplitude // 2
        else:
            # Center placement
            self.center_y = height // 2 - text_height // 2

        # Calculate text position
        self.text_y = self.center_y + self.max_amplitude // 2 + self.text_spacing

    def create_base_frame(self, background_pil, background_color):
        """
        Create a base frame with background.

        Args:
            background_pil (PIL.Image): Background image
            background_color (tuple): Background color (R, G, B)

        Returns:
            PIL.Image: Base frame
        """
        if background_pil:
            # Use provided background image
            image = background_pil.copy()
        else:
            # Create solid color background
            image = Image.new("RGBA", (self.width, self.height), color=background_color + (255,))

        return image

    def render_frame(self, smoothed_spectrum, peak_values, background_pil, artist_name, track_title):
        """
        Render a complete frame of the dual bar visualizer.

        Args:
            smoothed_spectrum (numpy.ndarray): Smoothed spectrum values
            peak_values (numpy.ndarray): Peak values for each bar
            background_pil (PIL.Image): Background image
            artist_name (str): Artist name to display
            track_title (str): Track title to display

        Returns:
            PIL.Image: Rendered frame
        """
        # Create base image
        base_image = self.create_base_frame(background_pil, self.background_color)

        # Create separate layers for content and glow
        content_layer = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        text_layer = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        center_line_layer = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        glow_shapes_layer = None

        if self.glow_effect != "off" and self.glow_color_rgb:
            glow_shapes_layer = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))

        # Draw center line
        self._draw_center_line(center_line_layer)

        # Draw bars to both content and glow layers
        self._draw_bars(content_layer, glow_shapes_layer, smoothed_spectrum, peak_values)

        # Draw text on text layer
        self._draw_text(text_layer, artist_name, track_title)

        # Add text to glow layer if enabled
        if glow_shapes_layer:
            # Create a white mask of the text for the glow
            text_mask_for_glow = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
            self._draw_text_mask(text_mask_for_glow, artist_name, track_title)
            glow_shapes_layer = Image.alpha_composite(glow_shapes_layer, text_mask_for_glow)

        # Final composite image (starts with base image)
        final_image = base_image.copy()

        # Apply glow effect first (underneath content) if enabled
        if glow_shapes_layer:
            # Apply blur for glow effect - use a moderate blur radius
            glow_layer_blurred = glow_shapes_layer.filter(ImageFilter.GaussianBlur(self.glow_blur_radius * 1.5))

            # Composite the blurred glow layer onto the final image
            final_image = Image.alpha_composite(final_image, glow_layer_blurred)

        # Add center line
        final_image = Image.alpha_composite(final_image, center_line_layer)

        # Then apply content on top of the glow and center line
        final_image = Image.alpha_composite(final_image, content_layer)

        # Finally, add the text on top of everything
        final_image = Image.alpha_composite(final_image, text_layer)

        return final_image

    def _draw_center_line(self, image):
        """
        Draw the center horizontal line.

        Args:
            image (PIL.Image): Image to draw on
        """
        draw = ImageDraw.Draw(image)

        # Calculate line start and end positions
        # Extend the line by the specified amount on both sides
        line_start_x = self.start_x - self.center_line_extension
        line_end_x = self.start_x + (self.n_bars * self.total_bar_width_gap) - self.bar_gap + self.center_line_extension

        # Ensure the line doesn't go outside the image boundaries
        line_start_x = max(0, line_start_x)
        line_end_x = min(self.width, line_end_x)

        # Draw the center line
        center_line_color_rgba = self.center_line_color + (255,)  # Full opacity for the line

        # For thicker lines, it's better to draw a rectangle than multiple lines
        half_thickness = self.center_line_thickness // 2

        # Draw a rectangle for the center line
        draw.rectangle(
            [
                (line_start_x, self.center_y - half_thickness),
                (line_end_x, self.center_y + half_thickness + (self.center_line_thickness % 2))
            ],
            fill=center_line_color_rgba
        )

    def _draw_bars(self, image, glow_shapes_layer, smoothed_spectrum, peak_values):
        """
        Draw the dual bars.

        Args:
            image (PIL.Image): Image to draw on
            glow_shapes_layer (PIL.Image): Layer for glow effect shapes
            smoothed_spectrum (numpy.ndarray): Smoothed spectrum values
            peak_values (numpy.ndarray): Peak values for each bar (not used in this visualizer)
        """
        # Create drawing objects for the layers
        _ = ImageDraw.Draw(image)  # We don't use this directly but it's needed to initialize the drawing context

        # Apply a logarithmic distribution to make the visualization more natural
        # This will emphasize the differences between low and high frequencies
        log_spectrum = np.copy(smoothed_spectrum)
        for i in range(len(log_spectrum)):
            # Apply frequency-dependent scaling with higher boost for high frequencies
            freq_factor = 1.0
            if i < self.n_bars * 0.2:  # Bass (first 20%)
                freq_factor = 1.5  # Keep bass boost the same
            elif i < self.n_bars * 0.6:  # Mid-range (next 40%)
                freq_factor = 1.8  # Keep mids boost the same
            else:  # High frequencies (last 40%)
                freq_factor = 2.2  # Significantly increased from 1.2 to make highs more pronounced

            # Apply the frequency factor
            log_spectrum[i] = log_spectrum[i] * freq_factor

            # Apply non-linear transformation to boost high signals and suppress low signals
            # Using a power function with the signal_power parameter
            if log_spectrum[i] > 0:
                # Apply power function to create more extreme contrast
                # Use a more aggressive power function for high frequencies
                if i >= self.n_bars * 0.6:  # High frequencies (last 40%)
                    # Use a lower power value for high frequencies to boost them more
                    high_freq_power = max(1.0, self.signal_power - 0.8)
                    log_spectrum[i] = np.power(log_spectrum[i], high_freq_power)
                else:
                    log_spectrum[i] = np.power(log_spectrum[i], self.signal_power)

        # Draw each bar
        for i in range(self.n_bars):
            bar_x = self.start_x + i * self.total_bar_width_gap
            signal = log_spectrum[i]

            # Skip drawing if signal is below noise gate
            if signal <= self.noise_gate:
                continue

            # Calculate bar height based on signal strength
            # Apply amplitude scale and clamp to max amplitude
            enhanced_amplitude_scale = self.effective_amplitude_scale * 2.0  # Reduced from 2.5 to prevent maxing out
            bar_height = min(int(signal * self.max_amplitude * enhanced_amplitude_scale), self.max_amplitude)

            # Ensure minimum visible height for active bars
            if signal > self.noise_gate:
                bar_height = max(bar_height, 4)  # Minimum 4px height for visibility

            # Edge rolloff is now disabled in the config, so we skip that code

            # Draw the bar (growing both up and down from center)
            self._draw_dual_bar(image, glow_shapes_layer, bar_x, bar_height)

    def _draw_dual_bar(self, image, glow_shapes_layer, bar_x, bar_height):
        """
        Draw a single dual bar that grows both up and down from the center.

        Args:
            image (PIL.Image): Image to draw on
            glow_shapes_layer (PIL.Image): Layer for glow effect shapes
            bar_x (int): X-coordinate of the bar
            bar_height (int): Height of the bar (total height will be 2x this value)
        """
        # Calculate half height for top and bottom parts
        half_height = bar_height // 2

        # Calculate top position (center - half_height)
        top_y = self.center_y - half_height

        # Create bar image
        bar_img = Image.new("RGBA", (self.bar_width, bar_height), (0, 0, 0, 0))
        bar_draw = ImageDraw.Draw(bar_img)
        color_rgba = self.bar_color_rgb + (self.pil_alpha,)

        if self.corner_radius == 0:
            bar_draw.rectangle((0, 0, self.bar_width, bar_height), fill=color_rgba)
        else:
            # For very short bars, reduce corner radius to avoid visual artifacts
            effective_radius = min(self.corner_radius, bar_height // 4)
            bar_draw.rounded_rectangle(
                (0, 0, self.bar_width, bar_height),
                radius=effective_radius,
                fill=color_rgba
            )

        # Composite onto main image
        image.alpha_composite(bar_img, (int(bar_x), int(top_y)))

        # Add to glow layer if needed
        if glow_shapes_layer and self.glow_effect != "off" and self.glow_color_rgb:
            bar_img_glow = Image.new("RGBA", (self.bar_width, bar_height), (0, 0, 0, 0))
            bar_draw_glow = ImageDraw.Draw(bar_img_glow)
            glow_color_rgba = self.glow_color_rgb + (self.pil_alpha,)

            if self.corner_radius == 0:
                bar_draw_glow.rectangle((0, 0, self.bar_width, bar_height), fill=glow_color_rgba)
            else:
                # Use same effective radius as above
                effective_radius = min(self.corner_radius, bar_height // 4)
                bar_draw_glow.rounded_rectangle(
                    (0, 0, self.bar_width, bar_height),
                    radius=effective_radius,
                    fill=glow_color_rgba
                )

            glow_shapes_layer.alpha_composite(bar_img_glow, (int(bar_x), int(top_y)))

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

        # Position text below visualizer
        artist_y = self.text_y

        # Draw artist name
        if artist_name:
            artist_color_rgba = self.artist_color_rgb + (255,)
            try:
                # For newer PIL versions
                artist_text_width = draw.textlength(artist_name, font=self.artist_font)
            except AttributeError:
                # For older PIL versions
                artist_text_width = self.artist_font.getlength(artist_name)
            artist_x = (self.width - artist_text_width) // 2
            draw.text((artist_x, artist_y), artist_name, fill=artist_color_rgba, font=self.artist_font)

        # Draw track title
        if track_title:
            title_color_rgba = self.title_color_rgb + (255,)
            try:
                # For newer PIL versions
                title_text_width = draw.textlength(track_title, font=self.title_font)
            except AttributeError:
                # For older PIL versions
                title_text_width = self.title_font.getlength(track_title)
            title_x = (self.width - title_text_width) // 2

            # Adjust spacing between artist and title based on font size
            spacing = 5 if self.artist_font.size < 40 else 10
            title_y = artist_y + (self.artist_font.size + spacing if artist_name else 0)

            draw.text((title_x, title_y), track_title, fill=title_color_rgba, font=self.title_font)

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

        # Position text below visualizer - MUST MATCH _draw_text method
        artist_y = self.text_y

        # Use the glow color with full opacity for the mask
        glow_color = self.glow_color_rgb + (255,) if self.glow_color_rgb else (255, 255, 255, 255)

        # Draw artist name
        if artist_name and self.artist_font:
            try:
                # For newer PIL versions
                artist_text_width = draw.textlength(artist_name, font=self.artist_font)
            except AttributeError:
                # For older PIL versions
                artist_text_width = self.artist_font.getlength(artist_name)
            artist_x = (self.width - artist_text_width) // 2
            draw.text((artist_x, artist_y), artist_name, fill=glow_color, font=self.artist_font)

        # Draw track title
        if track_title and self.title_font:
            try:
                # For newer PIL versions
                title_text_width = draw.textlength(track_title, font=self.title_font)
            except AttributeError:
                # For older PIL versions
                title_text_width = self.title_font.getlength(track_title)
            title_x = (self.width - title_text_width) // 2

            # Adjust spacing between artist and title based on font size
            spacing = 5 if self.artist_font.size < 40 else 10
            title_y = artist_y + (self.artist_font.size + spacing if artist_name else 0)

            draw.text((title_x, title_y), track_title, fill=glow_color, font=self.title_font)
