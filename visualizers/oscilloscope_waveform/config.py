# config.py for oscilloscope_waveform visualizer

from modules.utils import hex_to_rgb

def process_config(config=None):
    """Process and validate configuration for Oscilloscope Waveform visualizer."""
    # Default configuration for the oscilloscope waveform
    default_config = {
        "line_color": "#FFFFFF", # White color
        "line_thickness": 2,
        "scale": 1.0, # Amplitude scale
        "smoothing_factor": 0.2, # Factor for smoothing the waveform (reduced to allow more movement)
        "glow_effect": "black", # Enable glow effect with black color by default
        "glow_blur_radius": 3, # Blur radius for glow effect (same as other visualizers)
        "glow_intensity": 1.0, # Intensity of glow effect (full intensity)
        "anti_aliasing": True, # Enable anti-aliasing by default
        "text_size": "large", # Default text size
        "artist_color": "#FFFFFF", # White color for artist name
        "title_color": "#CCCCCC", # Light gray color for track title
    }

    # Merge user config with defaults
    merged_config = default_config.copy()
    if config and isinstance(config, dict):
        # Update with user-provided values
        for key, value in config.items():
            if key in default_config:
                # Convert string values to appropriate types
                if key in ["line_thickness", "grid_thickness", "grid_spacing"]:
                    try:
                        merged_config[key] = int(value)
                    except (ValueError, TypeError):
                        pass  # Keep default if conversion fails
                elif key in ["scale", "smoothing_factor", "glow_intensity"]:
                    try:
                        merged_config[key] = float(value)
                    except (ValueError, TypeError):
                        pass  # Keep default if conversion fails
                elif key in ["glow_blur_radius"]:
                    try:
                        merged_config[key] = int(value)
                    except (ValueError, TypeError):
                        pass  # Keep default if conversion fails
                elif key in ["show_grid", "anti_aliasing"]:
                    if isinstance(value, str):
                        merged_config[key] = value.lower() in ("true", "on", "yes", "1")
                    else:
                        merged_config[key] = bool(value)
                else:
                    merged_config[key] = value

    # Convert hex colors to RGB tuples
    merged_config["line_color_rgb"] = hex_to_rgb(merged_config["line_color"])
    merged_config["artist_color_rgb"] = hex_to_rgb(merged_config["artist_color"])
    merged_config["title_color_rgb"] = hex_to_rgb(merged_config["title_color"])

    # Process glow effect parameters
    merged_config["glow_color_rgb"] = None
    if merged_config["glow_effect"] == "white":
        merged_config["glow_color_rgb"] = (255, 255, 255)
    elif merged_config["glow_effect"] == "black":
        merged_config["glow_color_rgb"] = (0, 0, 0)
    elif merged_config["glow_effect"] == "match_line":
        merged_config["glow_color_rgb"] = merged_config["line_color_rgb"]

    return merged_config