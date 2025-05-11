"""
Configuration handling for the spectrum analyzer.
"""
from modules.utils import hex_to_rgb
import logging
logger = logging.getLogger('audio_visualizer.config')

def process_config(config=None):
    """
    Process and validate the configuration for the spectrum analyzer.

    Args:
        config (dict, optional): User-provided configuration dictionary

    Returns:
        dict: Processed configuration with all required parameters
    """
    # Default configuration
    default_config = {
        "n_bars": 40,
        "bar_width": 25,
        "bar_gap": 2,
        "bar_color": "#FFFFFF",
        "glow_effect": "off",
        "background_color": (0, 0, 0),
        "artist_color": "#FFFFFF",
        "title_color": "#FFFFFF",
        "amplitude_scale": 0.6,
        "sensitivity": 1.0,
        "analyzer_alpha": 1.0,
        "segment_height": 6,
        "segment_gap": 6,
        "corner_radius": 2,
        "min_freq": 30,
        "max_freq": 16000,
        "threshold_factor": 0.3,
        "attack_speed": 0.95,
        "decay_speed": 0.25,
        "always_on_bottom": True,
        "peak_hold_frames": 5,
        "peak_decay_speed": 0.15,
        "bass_threshold_adjust": 1.2,
        "mid_threshold_adjust": 1.0,
        "high_threshold_adjust": 0.9,
        "silence_threshold": 0.04,
        "silence_decay_factor": 0.5,
        "noise_gate": 0.08,
        "text_size": "large",  # Options: "small", "medium", "large"
        "visualizer_placement": "standard",  # Options: "standard", "bottom"
        "max_segments": 40  # Default number of segments per bar
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
        bool_keys = ["always_on_bottom"]
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
            "n_bars", "bar_width", "bar_gap", "segment_height", "segment_gap",
            "corner_radius", "min_freq", "max_freq", "peak_hold_frames", "max_segments"
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

    # Debug print to verify text_size is being preserved
    logger.debug(f"Config processed: text_size={conf.get('text_size', 'not found')}")

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

    # Additional derived values
    conf["effective_amplitude_scale"] = conf["amplitude_scale"] * conf["sensitivity"]
    conf["pil_alpha"] = int(conf["analyzer_alpha"] * 255)

    return conf

def process_dual_bar_config(config=None):
    """
    Process and validate the configuration for the dual bar visualizer.
    
    Args:
        config (dict, optional): User-provided configuration dictionary
        
    Returns:
        dict: Processed configuration with all required parameters
    """
    # Default configuration
    default_config = {
        "n_bars": 120,
        "bar_width": 3,
        "bar_gap": 5,
        "bar_color": "#FFFFFF",
        "max_amplitude": 250,
        "glow_effect": "black",
        "background_color": (0, 0, 0),
        "artist_color": "#FFFFFF",
        "title_color": "#FFFFFF",
        "amplitude_scale": 0.5,
        "sensitivity": 0.8,
        "analyzer_alpha": 0.6,
        "corner_radius": 0,
        "min_freq": 30,
        "max_freq": 16000,
        "threshold_factor": 0.3,
        "attack_speed": 0.95,
        "decay_speed": 0.25,
        "peak_hold_frames": 5,
        "peak_decay_speed": 0.15,
        "bass_threshold_adjust": 1.0,
        "mid_threshold_adjust": 1.0,
        "high_threshold_adjust": 0.9,
        "silence_threshold": 0.04,
        "silence_decay_factor": 0.5,
        "noise_gate": 0.08,
        "text_size": "large",
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
        bool_keys = ["always_on_bottom"]
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
            "n_bars", "bar_width", "bar_gap", "segment_height", "segment_gap",
            "corner_radius", "min_freq", "max_freq", "peak_hold_frames", "max_segments"
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

    # Debug print to verify text_size is being preserved
    logger.debug(f"Config processed: text_size={conf.get('text_size', 'not found')}")

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

    # Additional derived values
    conf["effective_amplitude_scale"] = conf["amplitude_scale"] * conf["sensitivity"]
    conf["pil_alpha"] = int(conf["analyzer_alpha"] * 255)

    return conf
