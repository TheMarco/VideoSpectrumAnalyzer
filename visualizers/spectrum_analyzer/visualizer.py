"""
Spectrum Analyzer visualizer implementation.
"""
import os
from PIL import Image
from core.base_visualizer import BaseVisualizer
from modules.media_handler import load_fonts
from visualizers.spectrum_analyzer.config import process_config
from visualizers.spectrum_analyzer.renderer import SpectrumRenderer

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
