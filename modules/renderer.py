"""
Rendering functions for the spectrum analyzer.
"""
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np

class SpectrumRenderer:
    """
    Class for rendering spectrum analyzer frames.
    """

    def __init__(self, width, height, config, artist_font, title_font):
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

        # Extract configuration values
        self.n_bars = config["n_bars"]
        self.bar_width = config["bar_width"]
        self.bar_gap = config["bar_gap"]
        self.segment_height = config["segment_height"]
        self.segment_gap = config["segment_gap"]
        self.corner_radius = min(config["corner_radius"], self.segment_height // 2, self.bar_width // 2)
        self.corner_radius = max(0, self.corner_radius)
        self.always_on_bottom = config["always_on_bottom"]
        self.noise_gate = config["noise_gate"]
        self.effective_amplitude_scale = config["effective_amplitude_scale"]
        self.pil_alpha = config["pil_alpha"]
        self.bar_color_rgb = config["bar_color_rgb"]
        self.artist_color_rgb = config["artist_color_rgb"]
        self.title_color_rgb = config["title_color_rgb"]
        self.background_color = config["background_color"]
        self.glow_effect = config["glow_effect"]
        self.glow_blur_radius = config["glow_blur_radius"]
        self.glow_color_rgb = config["glow_color_rgb"]
        self.visualizer_placement = config.get("visualizer_placement", "standard")
        
        # Add text spacing attribute
        self.text_spacing = 20  # Distance between visualizer and text in pixels

        # Calculate total text height (if both artist and title are present)
        # This is an estimate for layout calculations
        self.artist_font_size = getattr(self.artist_font, 'size', 36)
        self.title_font_size = getattr(self.title_font, 'size', 24)
        self.text_spacing_between = 10  # Space between artist and title text
        self.max_text_height = self.artist_font_size + self.title_font_size + self.text_spacing_between

        # Calculate visualization dimensions based on placement
        self.segment_unit = self.segment_height + self.segment_gap
        self.max_viz_height = int(height * 0.6)
        self.max_segments = max(1, self.max_viz_height // self.segment_unit) if self.segment_unit > 0 else 1
        self.visualizer_height = self.max_segments * self.segment_unit

        if self.visualizer_placement == "bottom":
            # For bottom placement:
            # We need to position the visualizer so that the entire set
            # (visualizer + text spacing + text) ends 20px from the bottom
            
            # Calculate from the bottom up:
            # 20px from bottom + max text height + text spacing + visualizer height
            bottom_margin = 20
            
            # Position the bottom of the visualizer
            self.viz_bottom = height - bottom_margin - self.max_text_height - self.text_spacing
        else:
            # Standard placement (center)
            self.viz_bottom = int(height * 0.65)
            
        self.total_bar_width_gap = self.bar_width + self.bar_gap
        self.total_bars_width = self.n_bars * self.total_bar_width_gap - self.bar_gap
        self.start_x = (width - self.total_bars_width) // 2

        # Segment dimensions
        self.seg_width = int(self.bar_width)
        self.seg_height = int(self.segment_height)
        if self.seg_width <= 0 or self.seg_height <= 0:
            raise ValueError(f"Invalid segment dimensions: {self.seg_width}x{self.seg_height}")

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
        Render a complete frame of the spectrum analyzer.

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
        glow_shapes_layer = None

        if self.glow_effect != "off" and self.glow_color_rgb:
            glow_shapes_layer = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))

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
            # Too much blur will make text unreadable, too little won't show the glow
            glow_layer_blurred = glow_shapes_layer.filter(ImageFilter.GaussianBlur(self.glow_blur_radius * 1.5))

            # Make sure white glow is actually white by using the glow color directly
            if self.glow_effect == "white":
                # For white glow, we'll create a new white layer with the alpha from the blurred glow

                # Get alpha channel from blurred glow
                alpha_mask = glow_layer_blurred.getchannel('A')

                # Create a white layer with the same alpha
                white_layer = Image.new("RGBA", (self.width, self.height), (255, 255, 255, 0))
                white_layer.putalpha(alpha_mask)

                # Use the white layer instead
                glow_layer_blurred = white_layer

            final_image = Image.alpha_composite(final_image, glow_layer_blurred)

        # Then apply content on top of the glow
        final_image = Image.alpha_composite(final_image, content_layer)

        # Finally, add the text on top of everything
        final_image = Image.alpha_composite(final_image, text_layer)

        return final_image

    def _draw_bars(self, image, glow_shapes_layer, smoothed_spectrum, peak_values):
        """
        Draw the spectrum analyzer bars.

        Args:
            image (PIL.Image): Image to draw on
            glow_shapes_layer (PIL.Image): Layer for glow effect shapes
            smoothed_spectrum (numpy.ndarray): Smoothed spectrum values
            peak_values (numpy.ndarray): Peak values for each bar
        """
        # Create drawing objects for the layers
        _ = ImageDraw.Draw(image)  # We don't use this directly but it's needed to initialize the drawing context

        for i in range(self.n_bars):
            bar_x = self.start_x + i * self.total_bar_width_gap
            signal = smoothed_spectrum[i]
            peak_signal = peak_values[i]

            # Draw static bottom segment if enabled
            if self.always_on_bottom and self.max_segments >= 1:
                self._draw_static_bottom_segment(image, glow_shapes_layer, bar_x)

            # Draw dynamic segments
            self._draw_dynamic_segments(image, glow_shapes_layer, bar_x, signal)

            # Draw peak segment
            if peak_signal > self.noise_gate:
                self._draw_peak_segment(image, glow_shapes_layer, bar_x, peak_signal)

    def _draw_static_bottom_segment(self, image, glow_shapes_layer, bar_x):
        """
        Draw the static bottom segment of a bar.

        Args:
            image (PIL.Image): Image to draw on
            glow_shapes_layer (PIL.Image): Layer for glow effect shapes
            bar_x (int): X-coordinate of the bar
        """
        static_bottom_y = self.viz_bottom - self.segment_height
        static_dest_xy = (int(bar_x), int(static_bottom_y))
        static_color_rgba = self.bar_color_rgb + (self.pil_alpha,)

        # Create segment image
        static_seg_img = Image.new("RGBA", (self.seg_width, self.seg_height), (0, 0, 0, 0))
        static_seg_draw = ImageDraw.Draw(static_seg_img)

        if self.corner_radius == 0:
            static_seg_draw.rectangle((0, 0, self.seg_width, self.seg_height), fill=static_color_rgba)
        else:
            static_seg_draw.rounded_rectangle(
                (0, 0, self.seg_width, self.seg_height),
                radius=self.corner_radius,
                fill=static_color_rgba
            )

        # Composite onto main image
        image.alpha_composite(static_seg_img, static_dest_xy)

        # Add to glow layer if needed
        if glow_shapes_layer and self.glow_effect != "off" and self.glow_color_rgb:
            static_seg_img_glow = Image.new("RGBA", (self.seg_width, self.seg_height), (0, 0, 0, 0))
            static_seg_draw_glow = ImageDraw.Draw(static_seg_img_glow)
            glow_color_rgba = self.glow_color_rgb + (self.pil_alpha,)

            if self.corner_radius == 0:
                static_seg_draw_glow.rectangle((0, 0, self.seg_width, self.seg_height), fill=glow_color_rgba)
            else:
                static_seg_draw_glow.rounded_rectangle(
                    (0, 0, self.seg_width, self.seg_height),
                    radius=self.corner_radius,
                    fill=glow_color_rgba
                )

            glow_shapes_layer.alpha_composite(static_seg_img_glow, static_dest_xy)

    def _draw_dynamic_segments(self, image, glow_shapes_layer, bar_x, signal):
        """
        Draw the dynamic segments of a bar.

        Args:
            image (PIL.Image): Image to draw on
            glow_shapes_layer (PIL.Image): Layer for glow effect shapes
            bar_x (int): X-coordinate of the bar
            signal (float): Signal strength (0-1)
        """
        # Calculate number of segments to draw
        num_segments_available_above = max(0, self.max_segments - 1) if self.always_on_bottom else self.max_segments
        num_dynamic_segments_to_draw = 0

        if signal > self.noise_gate and num_segments_available_above > 0:
            dynamic_segments_float = signal * num_segments_available_above * self.effective_amplitude_scale
            num_dynamic_segments_to_draw = min(int(np.ceil(dynamic_segments_float)), num_segments_available_above)

        # Draw each segment
        for k in range(num_dynamic_segments_to_draw):
            j = k + 1 if self.always_on_bottom else k
            
            # For bottom placement, segments grow upward from the bottom
            segment_y = self.viz_bottom - (j + 1) * self.segment_height - j * self.segment_gap
            dest_xy = (int(bar_x), int(segment_y))

            # Create segment image
            segment_img = Image.new("RGBA", (self.seg_width, self.seg_height), (0, 0, 0, 0))
            segment_draw = ImageDraw.Draw(segment_img)
            color_rgba = self.bar_color_rgb + (self.pil_alpha,)

            if self.corner_radius == 0:
                segment_draw.rectangle((0, 0, self.seg_width, self.seg_height), fill=color_rgba)
            else:
                segment_draw.rounded_rectangle(
                    (0, 0, self.seg_width, self.seg_height),
                    radius=self.corner_radius,
                    fill=color_rgba
                )

            # Composite onto main image
            image.alpha_composite(segment_img, dest_xy)

            # Add to glow layer if needed
            if glow_shapes_layer and self.glow_effect != "off" and self.glow_color_rgb:
                segment_img_glow = Image.new("RGBA", (self.seg_width, self.seg_height), (0, 0, 0, 0))
                segment_draw_glow = ImageDraw.Draw(segment_img_glow)
                glow_color_rgba = self.glow_color_rgb + (self.pil_alpha,)

                if self.corner_radius == 0:
                    segment_draw_glow.rectangle((0, 0, self.seg_width, self.seg_height), fill=glow_color_rgba)
                else:
                    segment_draw_glow.rounded_rectangle(
                        (0, 0, self.seg_width, self.seg_height),
                        radius=self.corner_radius,
                        fill=glow_color_rgba
                    )

                glow_shapes_layer.alpha_composite(segment_img_glow, dest_xy)

    def _draw_peak_segment(self, image, glow_shapes_layer, bar_x, peak_signal):
        """
        Draw the peak segment of a bar.

        Args:
            image (PIL.Image): Image to draw on
            glow_shapes_layer (PIL.Image): Layer for glow effect shapes
            bar_x (int): X-coordinate of the bar
            peak_signal (float): Peak signal strength (0-1)
        """
        # Calculate peak position
        num_segments_available = self.max_segments - 1 if self.always_on_bottom else self.max_segments
        peak_segments_float = peak_signal * num_segments_available * self.effective_amplitude_scale
        peak_segment_idx = min(int(np.ceil(peak_segments_float)), num_segments_available)

        if peak_segment_idx <= 0:
            return

        j = peak_segment_idx if self.always_on_bottom else peak_segment_idx - 1
        peak_y = self.viz_bottom - (j + 1) * self.segment_height - j * self.segment_gap
        peak_dest_xy = (int(bar_x), int(peak_y))

        # Create peak segment image
        peak_seg_img = Image.new("RGBA", (self.seg_width, self.seg_height), (0, 0, 0, 0))
        peak_seg_draw = ImageDraw.Draw(peak_seg_img)
        peak_color_rgba = self.bar_color_rgb + (self.pil_alpha,)

        if self.corner_radius == 0:
            peak_seg_draw.rectangle((0, 0, self.seg_width, self.seg_height), fill=peak_color_rgba)
        else:
            peak_seg_draw.rounded_rectangle(
                (0, 0, self.seg_width, self.seg_height),
                radius=self.corner_radius,
                fill=peak_color_rgba
            )

        # Composite onto main image
        image.alpha_composite(peak_seg_img, peak_dest_xy)

        # Add to glow layer if needed
        if glow_shapes_layer and self.glow_effect != "off" and self.glow_color_rgb:
            peak_seg_img_glow = Image.new("RGBA", (self.seg_width, self.seg_height), (0, 0, 0, 0))
            peak_seg_draw_glow = ImageDraw.Draw(peak_seg_img_glow)
            glow_color_rgba = self.glow_color_rgb + (self.pil_alpha,)

            if self.corner_radius == 0:
                peak_seg_draw_glow.rectangle((0, 0, self.seg_width, self.seg_height), fill=glow_color_rgba)
            else:
                peak_seg_draw_glow.rounded_rectangle(
                    (0, 0, self.seg_width, self.seg_height),
                    radius=self.corner_radius,
                    fill=glow_color_rgba
                )

            glow_shapes_layer.alpha_composite(peak_seg_img_glow, peak_dest_xy)

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

        # Position text below visualizer in all cases
        # The visualizer bottom position has already been calculated to leave room for text
        artist_y = self.viz_bottom + self.text_spacing

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
        artist_y = self.viz_bottom + self.text_spacing

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
