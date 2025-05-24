"""
Configuration processing for the Smooth Curves visualizer.
"""

def process_config(config=None):
    """Process and validate configuration for Smooth Curves visualizer."""
    # Default configuration
    default_config = {
        # Line settings - exact Shadertoy values
        "line_thickness": 3.0,  # Line thickness in pixels
        "line_color": "#ffccff",  # Default line color (pink/magenta)

        # Glow settings - exact Shadertoy values
        "bloom_size": 20.0,  # Bloom/glow size
        "bloom_intensity": 0.5,  # Bloom intensity
        "bloom_falloff": 1.5,  # Bloom falloff rate

        # Fill settings - exact Shadertoy values
        "fill_enabled": True,  # Enable/disable semi-transparent fill
        "fill_opacity": 0.5,  # Fill opacity (0.0 to 1.0)

        # Other settings - exact Shadertoy values
        "scale": 0.2,  # Scale factor for the curves
        "shift": 0.08,  # Shift between channels (relative to screen width)
        "width": 0.04,  # Width of each curve (relative to screen width)
        "amp": 1.0,  # Amplitude multiplier

        # Reactivity settings - exact Shadertoy values
        "decay_speed": 0.2,  # How quickly the visualization decays (0.0-1.0, higher = faster)
        "attack_speed": 1.0,  # How quickly the visualization responds to new audio (0.0-1.0)
        "noise_gate": 0.03,  # Minimum audio level to respond to (0.0-1.0)

        # Colors for the three channels
        "color1": "#cb2480",  # Pink/Magenta (203, 36, 128)
        "color2": "#29c8c0",  # Cyan (41, 200, 192)
        "color3": "#1889da",  # Blue (24, 137, 218)

        # Text settings
        "show_text": True,  # Show artist and track title
        "text_size": "large",  # Text size (small, medium, large)
        "text_color": "#ffffff",  # Text color
        "glow_effect": "black",  # Text glow effect color
        "glow_blur_radius": 3,  # Blur radius for text glow effect
        "glow_intensity": 1.0,  # Intensity of text glow effect

        # Video settings
        "fps": 30,  # Frames per second
    }

    # If no config is provided, use the default
    if config is None:
        return default_config

    # Merge provided config with default
    merged_config = default_config.copy()
    merged_config.update(config)

    # Convert hex colors to RGB tuples for the shader
    for color_key in ["color1", "color2", "color3"]:
        if color_key in merged_config:
            hex_color = merged_config[color_key]
            if hex_color.startswith("#"):
                # Convert hex to RGB tuple
                r = int(hex_color[1:3], 16)
                g = int(hex_color[3:5], 16)
                b = int(hex_color[5:7], 16)
                merged_config[f"{color_key}_rgb"] = (r, g, b)

    # Convert line_color to RGB tuple
    if "line_color" in merged_config:
        hex_color = merged_config["line_color"]
        if hex_color.startswith("#"):
            # Convert hex to RGB tuple
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            merged_config["line_color_rgb"] = (r, g, b)

    return merged_config
