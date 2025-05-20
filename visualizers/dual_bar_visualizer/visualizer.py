"""
Dual Bar Visualizer implementation.
"""
import os
from PIL import Image
from core.base_visualizer import BaseVisualizer
from modules.media_handler import load_fonts
from visualizers.dual_bar_visualizer.config import process_config
from visualizers.dual_bar_visualizer.renderer import DualBarRenderer
import numpy as np

print("Loading DualBarVisualizer module")

class DualBarVisualizer(BaseVisualizer):
    """
    Dual Bar Visualizer with bars growing both up and down from the center.
    """

    def __init__(self):
        """Initialize the dual bar visualizer."""
        super().__init__()
        print("Initializing DualBarVisualizer")
        # Keep both name formats for compatibility
        self.name = "Dual Bar Visualizer"  # Changed to match display name for consistency
        self.display_name = "Dual Bar Visualizer"  # This is what will be shown to users
        self.description = "Visualizer with bars growing both up and down from the center."

        # Set thumbnail path - this should be a static image showing what the visualizer looks like
        thumbnail_path = os.path.join("static", "images", "thumbnails", "dual_bar_visualizer.jpg")
        if os.path.exists(thumbnail_path):
            self.thumbnail = thumbnail_path
        else:
            self.thumbnail = None
        print(f"DualBarVisualizer initialized with name={self.name}, display_name={self.display_name}")

    def process_config(self, config=None):
        """
        Process and validate the configuration.

        Args:
            config (dict, optional): User-provided configuration

        Returns:
            dict: Processed configuration with all required parameters
        """
        return process_config(config)

    def create_renderer(self, width, height, config):
        """
        Create a renderer for the dual bar visualizer.

        Args:
            width (int): Frame width
            height (int): Frame height
            config (dict): Configuration dictionary

        Returns:
            DualBarRenderer: Renderer instance
        """
        # For backward compatibility, call the new initialize_renderer method
        return self.initialize_renderer(width, height, config)

    def render_frame(self, renderer, frame_data, background_image, metadata):
        """
        Render a single frame.

        Args:
            renderer (DualBarRenderer): Renderer instance
            frame_data (dict): Frame data (spectrum, peaks, etc.)
            background_image (PIL.Image): Background image
            metadata (dict): Additional metadata (artist, title, etc.)

        Returns:
            PIL.Image: Rendered frame
        """
        # Extract data from frame_data
        smoothed_spectrum = frame_data["smoothed_spectrum"]
        peak_values = frame_data["peak_values"]

        # Extract metadata
        artist_name = metadata.get("artist_name", "")
        track_title = metadata.get("track_title", "")

        # Render frame
        return renderer.render_frame(
            smoothed_spectrum,
            peak_values,
            background_image,
            artist_name,
            track_title
        )

    def update_frame_data(self, frame_data, frame_idx, conf):
        """
        Update frame data for the current frame.

        Args:
            frame_data (dict): Frame data to update
            frame_idx (int): Current frame index
            conf (dict): Configuration dictionary
        """
        mel_spec_norm = frame_data["mel_spec_norm"]
        normalized_frame_energy = frame_data["normalized_frame_energy"]
        dynamic_thresholds = frame_data["dynamic_thresholds"]
        smoothed_spectrum = frame_data["smoothed_spectrum"]
        peak_values = frame_data["peak_values"]
        peak_hold_counters = frame_data["peak_hold_counters"]

        current_spectrum = mel_spec_norm[:, frame_idx].copy()
        is_silent = normalized_frame_energy[frame_idx] < conf.get("silence_threshold", 0.04) if frame_idx < len(normalized_frame_energy) else True

        if frame_idx % 100 == 0:
            print(f"Frame {frame_idx}: Max spectrum value: {np.max(current_spectrum):.4f}, Is silent: {is_silent}")

        n_bars = len(current_spectrum)
        for i in range(n_bars):
            if is_silent:
                smoothed_spectrum[i] *= conf.get("silence_decay_factor", 0.5)
                peak_values[i] *= conf.get("silence_decay_factor", 0.5)
            else:
                if current_spectrum[i] > dynamic_thresholds[i]:
                    strength = np.clip(
                        np.power((current_spectrum[i] - dynamic_thresholds[i]) / (1 - dynamic_thresholds[i] + 1e-6), 1.5),
                        0, 1
                    )

                    attack_speed = conf.get("attack_speed", 0.95)
                    smoothed_spectrum[i] = max(
                        smoothed_spectrum[i] * (1 - attack_speed),
                        attack_speed * strength + smoothed_spectrum[i] * (1 - attack_speed)
                    )
                else:
                    decay_speed = conf.get("decay_speed", 0.25)
                    smoothed_spectrum[i] = smoothed_spectrum[i] * (1 - decay_speed)

                if smoothed_spectrum[i] < conf.get("noise_gate", 0.04):
                    smoothed_spectrum[i] = 0.0

                if smoothed_spectrum[i] > peak_values[i]:
                    peak_values[i] = smoothed_spectrum[i]
                    peak_hold_counters[i] = conf.get("peak_hold_frames", 5)
                elif peak_hold_counters[i] > 0:
                    peak_hold_counters[i] -= 1
                else:
                    peak_values[i] = max(peak_values[i] * (1 - conf.get("peak_decay_speed", 0.15)), smoothed_spectrum[i])

                if peak_values[i] < conf.get("noise_gate", 0.04):
                    peak_values[i] = 0.0

        frame_data["smoothed_spectrum"] = smoothed_spectrum
        frame_data["peak_values"] = peak_values
        frame_data["peak_hold_counters"] = peak_hold_counters

    def get_config_template(self):
        """Returns the path to the visualizer's configuration template."""
        return "dual_bar_visualizer_form.html"

    def initialize_renderer(self, width, height, config):
        """
        Initialize the renderer for this visualizer.

        Args:
            width (int): Frame width
            height (int): Frame height
            config (dict): Configuration dictionary

        Returns:
            DualBarRenderer: Renderer instance
        """
        # Ensure analyzer_alpha is properly set
        if "analyzer_alpha" in config:
            # Make sure it's a float between 0 and 1
            config["analyzer_alpha"] = float(config.get("analyzer_alpha", 0.6))
            config["analyzer_alpha"] = max(0.0, min(1.0, config["analyzer_alpha"]))

            # Recalculate pil_alpha based on analyzer_alpha
            config["pil_alpha"] = int(config["analyzer_alpha"] * 255)
        else:
            # Set default values if analyzer_alpha is not in config
            config["analyzer_alpha"] = 0.6
            config["pil_alpha"] = 153  # 0.6 * 255

        # Load fonts
        text_size = config.get("text_size", "large")
        # Use the imported load_fonts function
        artist_font, title_font = load_fonts(text_size)

        # Create renderer
        return DualBarRenderer(width, height, config, artist_font, title_font)
