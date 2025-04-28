"""
Test script to verify the glow effect rendering.
"""
import numpy as np
from PIL import Image, ImageFont
from modules.renderer import SpectrumRenderer
from modules.config_handler import process_config
import os

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
        "artist_color": "#FFFFFF",
        "title_color": "#FFFFFF",
    }

    # Process the configuration
    processed_config = process_config(config)

    # Load fonts
    font_size_artist = 72
    font_size_title = 36
    artist_font = None
    title_font = None

    # Try to load system fonts
    try:
        # Try DejaVu Sans first
        if os.path.exists("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
            artist_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size_artist)
            title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size_title)
        # Try Arial next
        elif os.path.exists("/Library/Fonts/Arial.ttf"):
            artist_font = ImageFont.truetype("/Library/Fonts/Arial Bold.ttf", font_size_artist)
            title_font = ImageFont.truetype("/Library/Fonts/Arial.ttf", font_size_title)
        # Fallback to default
        else:
            artist_font = ImageFont.load_default()
            title_font = ImageFont.load_default()
    except Exception:
        # If all else fails, use default font
        artist_font = ImageFont.load_default()
        title_font = ImageFont.load_default()

    # Create a renderer
    width, height = 800, 600
    renderer = SpectrumRenderer(
        width, height, processed_config,
        artist_font=artist_font, title_font=title_font
    )

    # Create test data
    smoothed_spectrum = np.ones(10) * 0.8  # All bars at 80% height
    peak_values = np.ones(10) * 0.9  # All peaks at 90% height

    # Create a black background
    background = Image.new("RGBA", (width, height), (0, 0, 0, 255))

    # Test with white glow
    frame_white = renderer.render_frame(
        smoothed_spectrum, peak_values, background,
        artist_name="Test Artist", track_title="Test Track"
    )
    frame_white.save("test_white_glow.png")
    print("Test image with white glow saved to test_white_glow.png")

    # Test with black glow
    processed_config["glow_effect"] = "black"
    processed_config["glow_color_rgb"] = (0, 0, 0)
    renderer_black = SpectrumRenderer(
        width, height, processed_config,
        artist_font=artist_font, title_font=title_font
    )
    frame_black = renderer_black.render_frame(
        smoothed_spectrum, peak_values, background,
        artist_name="Test Artist", track_title="Test Track"
    )
    frame_black.save("test_black_glow.png")
    print("Test image with black glow saved to test_black_glow.png")

    # Test with no glow
    processed_config["glow_effect"] = "off"
    processed_config["glow_color_rgb"] = None
    renderer_no_glow = SpectrumRenderer(
        width, height, processed_config,
        artist_font=artist_font, title_font=title_font
    )
    frame_no_glow = renderer_no_glow.render_frame(
        smoothed_spectrum, peak_values, background,
        artist_name="Test Artist", track_title="Test Track"
    )
    frame_no_glow.save("test_no_glow.png")
    print("Test image with no glow saved to test_no_glow.png")

if __name__ == "__main__":
    test_glow_effect()
