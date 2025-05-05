# renderer.py for oscilloscope_waveform visualizer

from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np

class OscilloscopeWaveformRenderer:
    def __init__(self, width, height, config, artist_font=None, title_font=None):
        self.width = width
        self.height = height
        self.config = config
        self.line_color = config.get("line_color_rgb", (0, 255, 0))
        self.line_thickness = config.get("line_thickness", 2)
        self.scale = config.get("scale", 1.0)
        self.smoothing_factor = config.get("smoothing_factor", 0.5)

        # Glow effect parameters
        self.glow_effect = config.get("glow_effect", "white") != "off"
        self.glow_color = config.get("glow_color_rgb")

        # Ensure glow_blur_radius is an integer
        blur_radius = config.get("glow_blur_radius", 3)
        if isinstance(blur_radius, str):
            try:
                blur_radius = int(blur_radius)
            except (ValueError, TypeError):
                blur_radius = 3
        self.glow_blur_radius = blur_radius

        # Ensure glow_intensity is a float
        intensity = config.get("glow_intensity", 1.0)
        if isinstance(intensity, str):
            try:
                intensity = float(intensity)
            except (ValueError, TypeError):
                intensity = 1.0
        self.glow_intensity = intensity

        # Anti-aliasing parameters - using a more efficient approach
        self.anti_aliasing = True

        # Text rendering parameters
        self.artist_font = artist_font
        self.title_font = title_font
        self.artist_color_rgb = config.get("artist_color_rgb", (255, 255, 255))
        self.title_color_rgb = config.get("title_color_rgb", (204, 204, 204))
        self.text_spacing = 20  # Distance between visualizer and text in pixels

        # Keep track of the previous frame's waveform for smoothing
        self._previous_waveform = None

    def render_frame(self, audio_data, background_image, metadata=None):
        """
        Renders a single frame of the oscilloscope waveform visualization.

        Args:
            audio_data (np.ndarray): A numpy array containing the audio data for the current frame.
                                     Expected shape is (num_samples, num_channels).
            background_image (PIL.Image.Image): The background image for the frame.
            metadata (dict, optional): Additional metadata (e.g., artist, title). Defaults to None.

        Returns:
            PIL.Image.Image: The rendered frame as a PIL Image.
        """
        # Create a transparent layer for the waveform
        waveform_layer = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(waveform_layer)

        # Create a separate layer for the glow effect if enabled
        glow_layer = None
        if self.glow_effect and self.glow_color:
            glow_layer = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow_layer)

        # Process audio data and draw waveform
        if audio_data is not None and len(audio_data) > 0:
            # Convert stereo to mono if necessary by taking the average
            if audio_data.ndim > 1 and audio_data.shape[1] > 1:
                mono_audio_data = np.mean(audio_data, axis=1)
            else:
                mono_audio_data = audio_data.flatten()

            # Normalize and scale the audio data
            # Avoid division by zero if audio_data is all zeros
            max_amplitude = np.max(np.abs(mono_audio_data)) if np.max(np.abs(mono_audio_data)) > 0 else 1.0
            scaled_audio_data = (mono_audio_data / max_amplitude) * (self.height / 2) * self.scale

            # For anti-aliasing, we'll use more points than we need and apply smoothing
            if self.anti_aliasing:
                # Use more points for smoother curves - oversample by 4x for even smoother results
                # This is more efficient than rendering at higher resolution
                oversample_factor = 4
                # Reduce the number of points to avoid performance issues
                max_points = 1500  # Maximum number of points to use for initial sampling
                step = max(1, len(scaled_audio_data) // max_points)

                # Use a subset of the audio data
                sampled_audio_data = scaled_audio_data[::step]

                # Apply a light smoothing filter to reduce jaggedness
                # Use a simple moving average filter
                window_size = 3
                if len(sampled_audio_data) > window_size:
                    # Create a padded array to handle edge cases
                    padded_data = np.pad(sampled_audio_data, (window_size//2, window_size//2), mode='edge')
                    # Apply moving average
                    smoothed_data = np.zeros_like(sampled_audio_data)
                    for i in range(len(sampled_audio_data)):
                        smoothed_data[i] = np.mean(padded_data[i:i+window_size])
                    sampled_audio_data = smoothed_data

                # Interpolate to get more points for smoother curves
                x_indices = np.arange(0, len(sampled_audio_data))
                x_indices_upsampled = np.linspace(0, len(sampled_audio_data) - 1, len(sampled_audio_data) * oversample_factor)

                # Use cubic interpolation for smoother curves when possible
                if len(sampled_audio_data) > 3:
                    try:
                        # Try to import scipy - it might not be available
                        from scipy import interpolate
                        # Try to use cubic spline interpolation for smoother curves
                        cs = interpolate.CubicSpline(x_indices, sampled_audio_data)
                        upsampled_audio_data = cs(x_indices_upsampled)
                    except (ImportError, Exception):
                        # Fall back to linear interpolation if scipy is not available or cubic fails
                        upsampled_audio_data = np.interp(x_indices_upsampled, x_indices, sampled_audio_data)
                else:
                    # Use linear interpolation for small datasets
                    upsampled_audio_data = np.interp(x_indices_upsampled, x_indices, sampled_audio_data)

                # Calculate waveform points with sub-pixel precision
                points = []
                x_step = self.width / len(upsampled_audio_data)
                for i, sample in enumerate(upsampled_audio_data):
                    x = i * x_step
                    y = (self.height / 2) - sample  # Center the waveform vertically
                    points.append((x, y))
            else:
                # Calculate waveform points without oversampling
                points = []
                x_step = self.width / len(scaled_audio_data)
                for i, sample in enumerate(scaled_audio_data):
                    x = i * x_step
                    y = (self.height / 2) - sample  # Center the waveform vertically
                    points.append((x, y))

            # Apply smoothing - but limit it to ensure the waveform still moves
            if self._previous_waveform is not None and self.smoothing_factor > 0:
                # Use a dynamic smoothing factor that decreases for larger differences
                # This ensures that big changes in the waveform are still visible

                # Ensure waveforms have the same length before smoothing
                min_len = min(len(points), len(self._previous_waveform))
                smoothed_points = []

                # Calculate average difference between current and previous waveform
                # This helps us adjust smoothing dynamically
                if min_len > 0:
                    y_diffs = []
                    for i in range(min_len):
                        y_diff = abs(points[i][1] - self._previous_waveform[i][1])
                        y_diffs.append(y_diff)

                    avg_diff = sum(y_diffs) / len(y_diffs) if y_diffs else 0
                    # Reduce smoothing factor for larger differences
                    # This ensures that significant changes are more visible
                    dynamic_smoothing = max(0.0, min(self.smoothing_factor,
                                                    self.smoothing_factor / (1 + avg_diff * 10)))
                else:
                    dynamic_smoothing = self.smoothing_factor

                # Apply the dynamic smoothing
                for i in range(min_len):
                    # Keep x coordinates the same (they shouldn't change)
                    # Only smooth the y coordinates (amplitude)
                    smoothed_x = points[i][0]
                    smoothed_y = (points[i][1] * (1 - dynamic_smoothing)) + (self._previous_waveform[i][1] * dynamic_smoothing)
                    smoothed_points.append((smoothed_x, smoothed_y))

                # Append any remaining points from the current waveform if it's longer
                smoothed_points.extend(points[min_len:])
                points = smoothed_points

            # Store the current waveform for the next frame
            # Make a deep copy to avoid reference issues
            self._previous_waveform = points.copy() if points else None

            # Draw the waveform as a line
            if len(points) > 1:
                # For smoother lines, we'll draw multiple lines with decreasing thickness
                if self.anti_aliasing and self.line_thickness > 1:
                    # Draw the glow effect first if enabled
                    if self.glow_effect and glow_layer and glow_draw:
                        # Draw the same line but with a larger thickness for the glow
                        glow_thickness = self.line_thickness * 2
                        glow_draw.line(points, fill=self.glow_color, width=glow_thickness)

                        # For thicker lines, add a slightly larger blur for smoother edges
                        if glow_thickness > 3:
                            # Add a second, thinner line with higher opacity for a smoother edge
                            glow_color_with_alpha = self.glow_color + (200,) if len(self.glow_color) == 3 else self.glow_color[0:3] + (200,)
                            glow_draw.line(points, fill=glow_color_with_alpha, width=glow_thickness + 2)

                    # Draw the main waveform with a multi-pass approach for smoother appearance
                    # First draw a slightly thicker line with lower opacity
                    if self.line_thickness > 2:
                        # Create a semi-transparent version of the line color for the outer line
                        line_color_with_alpha = self.line_color + (150,) if len(self.line_color) == 3 else self.line_color[0:3] + (150,)
                        draw.line(points, fill=line_color_with_alpha, width=self.line_thickness + 1)

                    # Then draw the main line at full opacity
                    draw.line(points, fill=self.line_color, width=self.line_thickness)

                    # Finally, draw a thinner line with full opacity for a sharper center
                    if self.line_thickness > 2:
                        draw.line(points, fill=self.line_color, width=max(1, self.line_thickness - 1))
                else:
                    # Draw the glow effect first if enabled
                    if self.glow_effect and glow_layer and glow_draw:
                        # Draw the same line but with a larger thickness for the glow
                        glow_thickness = self.line_thickness * 2
                        glow_draw.line(points, fill=self.glow_color, width=glow_thickness)

                    # Draw the main waveform line
                    draw.line(points, fill=self.line_color, width=self.line_thickness)

        # Ensure background_image is in RGBA mode for alpha_composite
        if background_image.mode != 'RGBA':
            background_image = background_image.convert('RGBA')

        # Start with the background image
        result = background_image.copy()

        # Apply glow effect if enabled
        if self.glow_effect and glow_layer:
            # For a smoother glow, apply multiple blur passes with different radii
            if self.anti_aliasing:
                # First pass - larger blur radius for the outer glow
                outer_glow = glow_layer.filter(ImageFilter.GaussianBlur(self.glow_blur_radius * 1.5))

                # Second pass - medium blur radius for the middle glow
                middle_glow = glow_layer.filter(ImageFilter.GaussianBlur(self.glow_blur_radius))

                # Third pass - smaller blur radius for the inner glow
                inner_glow = glow_layer.filter(ImageFilter.GaussianBlur(max(1, self.glow_blur_radius * 0.5)))

                # Composite the glow layers with different opacities
                # Start with the outer glow (lowest opacity)
                outer_glow_with_opacity = Image.new("RGBA", outer_glow.size, (0, 0, 0, 0))
                outer_glow_with_opacity.paste(outer_glow, (0, 0), mask=Image.new("L", outer_glow.size, 100))
                result = Image.alpha_composite(result, outer_glow_with_opacity)

                # Add the middle glow (medium opacity)
                middle_glow_with_opacity = Image.new("RGBA", middle_glow.size, (0, 0, 0, 0))
                middle_glow_with_opacity.paste(middle_glow, (0, 0), mask=Image.new("L", middle_glow.size, 150))
                result = Image.alpha_composite(result, middle_glow_with_opacity)

                # Add the inner glow (highest opacity)
                inner_glow_with_opacity = Image.new("RGBA", inner_glow.size, (0, 0, 0, 0))
                inner_glow_with_opacity.paste(inner_glow, (0, 0), mask=Image.new("L", inner_glow.size, 200))
                result = Image.alpha_composite(result, inner_glow_with_opacity)
            else:
                # Simple blur for non-anti-aliased mode
                glow_layer_blurred = glow_layer.filter(ImageFilter.GaussianBlur(self.glow_blur_radius))
                result = Image.alpha_composite(result, glow_layer_blurred)

        # Composite the waveform layer on top
        result = Image.alpha_composite(result, waveform_layer)

        # Add artist and track title if provided in metadata
        if metadata and ('artist_name' in metadata or 'track_title' in metadata):
            artist_name = metadata.get('artist_name', '')
            track_title = metadata.get('track_title', '')

            if (artist_name or track_title) and (self.artist_font or self.title_font):
                # Create a text layer
                text_layer = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
                self._draw_text(text_layer, artist_name, track_title)

                # Create a text glow layer if glow effect is enabled
                if self.glow_effect and self.glow_color:
                    text_glow_layer = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
                    self._draw_text_mask(text_glow_layer, artist_name, track_title)

                    # Apply blur to the text glow layer
                    text_glow_blurred = text_glow_layer.filter(ImageFilter.GaussianBlur(self.glow_blur_radius))

                    # Composite the text glow layer onto the result
                    result = Image.alpha_composite(result, text_glow_blurred)

                # Composite the text layer on top
                result = Image.alpha_composite(result, text_layer)

        return result

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

        # Position text at the bottom of the image with some padding
        bottom_padding = 50
        artist_y = self.height - bottom_padding - (self.title_font.size if self.title_font and track_title else 0) - (self.artist_font.size if self.artist_font else 0)

        # Draw artist name
        if artist_name and self.artist_font:
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
        if track_title and self.title_font:
            title_color_rgba = self.title_color_rgb + (255,)
            try:
                # For newer PIL versions
                title_text_width = draw.textlength(track_title, font=self.title_font)
            except AttributeError:
                # For older PIL versions
                title_text_width = self.title_font.getlength(track_title)
            title_x = (self.width - title_text_width) // 2

            # Adjust spacing between artist and title based on font size
            spacing = 5 if self.artist_font and self.artist_font.size < 40 else 10
            title_y = artist_y + (self.artist_font.size + spacing if artist_name and self.artist_font else 0)

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

        # Position text at the bottom of the image with some padding - MUST MATCH _draw_text method
        bottom_padding = 50
        artist_y = self.height - bottom_padding - (self.title_font.size if self.title_font and track_title else 0) - (self.artist_font.size if self.artist_font else 0)

        # Use the glow color with full opacity for the mask
        glow_color = self.glow_color + (255,) if self.glow_color else (255, 255, 255, 255)

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

            # Adjust spacing between artist and title based on font size - MUST MATCH _draw_text method
            spacing = 5 if self.artist_font and self.artist_font.size < 40 else 10
            title_y = artist_y + (self.artist_font.size + spacing if artist_name and self.artist_font else 0)

            draw.text((title_x, title_y), track_title, fill=glow_color, font=self.title_font)

