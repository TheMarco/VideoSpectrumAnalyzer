# config.py for oscilloscope_waveform visualizer

from modules.utils import hex_to_rgb

def process_config(config=None):
    """Process and validate configuration for Oscilloscope Waveform visualizer."""
    # Default configuration for the oscilloscope waveform
    default_config = {
        # Standard parameters based on user's preferred settings
        "line_color": "#ffffe5", # Light yellow color
        "line_thickness": 10, # Thicker line
        "scale": 4.0, # Higher amplitude scale for more pronounced waveform
        "smoothing_factor": 0.8, # Higher smoothing factor for smoother waveform
        "glow_effect": "black", # Enable text glow effect with black color by default (for artist/title text only)
        "glow_blur_radius": 3, # Blur radius for text glow effect (same as other visualizers)
        "glow_intensity": 1.0, # Intensity of text glow effect (full intensity)
        "anti_aliasing": True, # Enable anti-aliasing by default
        "text_size": "large", # Default text size
        "artist_color": "#fcffe5", # Light yellow color for artist name
        "title_color": "#ffffeb", # Light yellow color for track title

        # GL renderer specific parameters
        "use_gl_renderer": True, # Use the GL renderer instead of PIL
        "thickness_scale": 0.1, # Smaller thickness scale for thicker waveform
        "use_standard_settings": True, # Use standard settings by default (renamed from use_original_settings)
        "persistence": 0.7, # Persistence factor for trailing effect (0.0 = no persistence, 1.0 = maximum persistence)
        "vertical_offset": -1.5, # Lower vertical offset to position waveform lower in the viewport
        "fps": 30, # Standard frame rate for video output
        "waveform_update_rate": 15 # How many times per second the waveform updates (lower = less "double waveform" effect)
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
                elif key in ["scale", "smoothing_factor", "glow_intensity", "thickness_scale", "persistence", "vertical_offset"]:
                    try:
                        merged_config[key] = float(value)
                        print(f"Converted {key} from {value} to {merged_config[key]}")
                    except (ValueError, TypeError):
                        print(f"Failed to convert {key} from {value}, keeping default {merged_config[key]}")
                        pass  # Keep default if conversion fails
                elif key in ["glow_blur_radius", "waveform_update_rate", "fps"]:
                    try:
                        merged_config[key] = int(value)
                    except (ValueError, TypeError):
                        pass  # Keep default if conversion fails
                elif key in ["show_grid", "anti_aliasing", "use_original_settings", "use_standard_settings"]:
                    if isinstance(value, str):
                        merged_config[key] = value.lower() in ("true", "on", "yes", "1")
                    else:
                        merged_config[key] = bool(value)

                    # Handle backward compatibility - if use_original_settings is provided,
                    # set use_standard_settings to the same value
                    if key == "use_original_settings":
                        merged_config["use_standard_settings"] = merged_config[key]
                        print(f"Converting use_original_settings to use_standard_settings: {merged_config['use_standard_settings']}")
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