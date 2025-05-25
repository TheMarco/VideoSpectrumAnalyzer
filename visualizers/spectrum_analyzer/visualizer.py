"""
Spectrum Analyzer visualizer implementation.
"""
import os
from PIL import Image
from core.base_visualizer import BaseVisualizer
from modules.media_handler import load_fonts
from visualizers.spectrum_analyzer.config import process_config
from visualizers.spectrum_analyzer.renderer import SpectrumRenderer
import numpy as np

class SpectrumAnalyzer(BaseVisualizer):
    """
    Spectrum Analyzer visualizer.
    """
    
    def __init__(self):
        """Initialize the spectrum analyzer visualizer."""
        super().__init__()
        self.name = "Spectrum Analyzer"
        self.description = "Classic spectrum analyzer with customizable bars and peaks."
        
        # Set thumbnail path - this should be a static image showing what the visualizer looks like
        thumbnail_path = os.path.join("static", "images", "thumbnails", "spectrum_analyzer.jpg")
        if os.path.exists(thumbnail_path):
            self.thumbnail = thumbnail_path
        else:
            self.thumbnail = None
    
    def process_config(self, config=None):
        """
        Process and validate the configuration.
        
        Args:
            config (dict, optional): User-provided configuration
            
        Returns:
            dict: Processed configuration with all required parameters
        """
        return process_config(config)
    
    def initialize_renderer(self, width, height, config):
        """
        Initialize the renderer for this visualizer.
        
        Args:
            width (int): Frame width
            height (int): Frame height
            config (dict): Configuration dictionary
            
        Returns:
            SpectrumRenderer: Renderer instance
        """
        # Load fonts with the text size from config
        text_size = config.get("text_size", "large")
        print(f"Initializing renderer with text_size: {text_size}")
        artist_font, title_font = load_fonts(text_size=text_size)
        
        # Initialize renderer
        return SpectrumRenderer(width, height, config, artist_font, title_font)
    
    def render_frame(self, renderer, frame_data, background_image, metadata):
        """
        Render a single frame.
        
        Args:
            renderer (SpectrumRenderer): Renderer instance
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
        return "spectrum_analyzer_form.html"
