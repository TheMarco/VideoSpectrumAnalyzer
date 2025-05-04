"""
Configuration handling for the dual bar visualizer.
"""
from core.utils import hex_to_rgb

def process_config(config=None):
    """
    Process and validate the configuration for the dual bar visualizer.

    Args:
        config (dict, optional): User-provided configuration dictionary

    Returns:
        dict: Processed configuration with all required parameters
    """
    # Default configuration
    default_config = {
        "n_bars": 60,
        "bar_width": 5,
        "bar_gap": 5,            # Increased gap between bars to 5px
        "bar_color": "#FFFFFF",
        "max_amplitude": 250,    # Increased to 250px as requested
        "glow_effect": "off",
        "background_color": (0, 0, 0),
        "artist_color": "#FFFFFF",
        "title_color": "#FFFFFF",
        "amplitude_scale": 1.0,  # Increased for more extreme visualization
        "sensitivity": 2.0,      # Significantly increased for extreme responsiveness
        "analyzer_alpha": 1.0,
        "corner_radius": 0,      # Default to no rounded corners for a cleaner look
        "min_freq": 30,
        "max_freq": 16000,
        "threshold_factor": 0.35, # Increased to make low signals less visible
        "attack_speed": 0.98,    # Faster attack for more immediate response
        "decay_speed": 0.5,      # Even faster decay for quicker response
        "peak_hold_frames": 3,   # Reduced peak hold frames
        "peak_decay_speed": 0.3, # Faster peak decay
        "bass_threshold_adjust": 1.3,  # More aggressive bass threshold
        "mid_threshold_adjust": 1.1,   # More aggressive mid threshold
        "high_threshold_adjust": 0.6,  # Reduced high threshold to make highs more responsive
        "silence_threshold": 0.03, # Slightly higher silence threshold
        "silence_decay_factor": 0.8, # Faster silence decay
        "noise_gate": 0.08,      # Higher noise gate to suppress more low signals
        "text_size": "large",    # Options: "small", "medium", "large"
        "visualizer_placement": "center", # Options: "center", "bottom"
        "center_line_color": "match_bar", # Center line color matches bar color
        "center_line_thickness": 3,     # Reduced to 3px thickness as requested
        "center_line_extension": 25,    # Extend the center line by 25px on each side
        "edge_rolloff": True,    # Enable edge rolloff effect
        "edge_rolloff_factor": 0.4, # More aggressive rolloff (lower value = more rolloff)
        "signal_power": 2.5,     # New parameter: power function exponent for signal boosting
    }

    # Merge user config with defaults
    conf = default_config.copy()
    if config and isinstance(config, dict):
        # Process string values that should be preserved as-is
        string_keys = ["text_size", "visualizer_placement", "glow_effect", "bar_color", "artist_color", "title_color"]
        for key in string_keys:
            if key in config:
                conf[key] = config[key]

        # Process boolean values
        bool_keys = []
        for key in bool_keys:
            if key in config:
                if isinstance(config[key], str):
                    conf[key] = config[key].lower() in ("true", "on", "yes", "1")
                else:
                    conf[key] = bool(config[key])

        # Process float values
        float_keys = [
            "amplitude_scale", "sensitivity", "analyzer_alpha", "threshold_factor",
            "attack_speed", "decay_speed", "peak_decay_speed", "bass_threshold_adjust",
            "mid_threshold_adjust", "high_threshold_adjust", "silence_threshold",
            "silence_decay_factor", "noise_gate"
        ]
        for key in float_keys:
            if key in config:
                try:
                    conf[key] = float(config[key])
                except (ValueError, TypeError):
                    pass  # Keep default if conversion fails

        # Process integer values
        int_keys = [
            "n_bars", "bar_width", "bar_gap", "corner_radius",
            "min_freq", "max_freq", "peak_hold_frames", "max_amplitude"
        ]
        for key in int_keys:
            if key in config:
                try:
                    conf[key] = int(config[key])
                except (ValueError, TypeError):
                    pass  # Keep default if conversion fails

        # Process color values
        if "bar_color" in config:
            conf["bar_color"] = config["bar_color"]
        if "artist_color" in config:
            conf["artist_color"] = config["artist_color"]
        if "title_color" in config:
            conf["title_color"] = config["title_color"]
        if "background_color" in config:
            conf["background_color"] = config["background_color"]
        if "glow_effect" in config:
            conf["glow_effect"] = config["glow_effect"]

    # Validate max_amplitude (between 100 and 300)
    conf["max_amplitude"] = max(100, min(300, conf["max_amplitude"]))

    # Debug print to verify text_size is being preserved
    print(f"Text size after config processing: {conf.get('text_size', 'not found')}")

    # Derived configuration values
    conf["bar_color_rgb"] = hex_to_rgb(conf.get("bar_color", "#FFFFFF"))
    conf["artist_color_rgb"] = hex_to_rgb(conf.get("artist_color", "#FFFFFF"))
    conf["title_color_rgb"] = hex_to_rgb(conf.get("title_color", "#FFFFFF"))

    # Glow effect configuration
    conf["glow_blur_radius"] = 3
    conf["glow_color_rgb"] = None
    if conf["glow_effect"] == "white":
        conf["glow_color_rgb"] = (255, 255, 255)
    elif conf["glow_effect"] == "black":
        conf["glow_color_rgb"] = (0, 0, 0)
    elif conf["glow_effect"] == "match_bar":
        conf["glow_color_rgb"] = conf["bar_color_rgb"]

    # Additional derived values
    conf["effective_amplitude_scale"] = conf["amplitude_scale"] * conf["sensitivity"]
    conf["pil_alpha"] = int(conf["analyzer_alpha"] * 255)

    return conf
