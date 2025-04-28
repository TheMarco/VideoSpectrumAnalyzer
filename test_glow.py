"""
Test script to verify the glow effect rendering.
"""
import numpy as np
from PIL import Image
from modules.renderer import SpectrumRenderer
from modules.config_handler import process_config

def test_glow_effect():
    # Create a simple test configuration with glow effect enabled
    config = {
        "n_bars": 10,
        "bar_width": 40,
        "bar_gap": 5,
        "segment_height": 20,
        "segment_gap": 5,
        "corner_radius": 5,
        "bar_color": "#FFFFFF",
        "glow_effect": "white",  # Enable white glow
        "analyzer_alpha": 1.0,
        "amplitude_scale": 1.0,
        "sensitivity": 1.0,
        "always_on_bottom": True,
        "noise_gate": 0.0,
    }
    
    # Process the configuration
    processed_config = process_config(config)
    
    # Create a renderer
    width, height = 800, 600
    renderer = SpectrumRenderer(
        width, height, processed_config, 
        artist_font=None, title_font=None
    )
    
    # Create test data
    smoothed_spectrum = np.ones(10) * 0.8  # All bars at 80% height
    peak_values = np.ones(10) * 0.9  # All peaks at 90% height
    
    # Create a black background
    background = Image.new("RGBA", (width, height), (0, 0, 0, 255))
    
    # Render a frame
    frame = renderer.render_frame(
        smoothed_spectrum, peak_values, background, 
        artist_name="Test Artist", track_title="Test Track"
    )
    
    # Save the frame
    frame.save("test_glow_effect.png")
    print("Test image saved to test_glow_effect.png")

if __name__ == "__main__":
    test_glow_effect()
