"""
Configuration processing for the Circular Spectrum visualizer.
"""

def process_config(config=None):
    """
    Process and validate the configuration for the Circular Spectrum visualizer.

    Args:
        config (dict, optional): User-provided configuration

    Returns:
        dict: Processed configuration with all required parameters
    """
    # Default configuration
    default_config = {
        # Circular spectrum parameters
        "num_bars": 36,                  # Number of bars around the circle
        "segments_per_bar": 15,          # Number of segments per bar
        "inner_radius": 0.20,            # Inner radius of the circle (0-1)
        "outer_radius": 0.40,            # Outer radius of the circle (0-1)
        "bar_width": 0.8,                # Width of bars (0-1, where 1 means bars touch, lower values create gaps)
        "segment_spacing": 2,            # Spacing between segments in pixels (0 = no spacing)
        "rectangular_bars": True,        # Use rectangular bars (True) or radial/trapezoid bars (False)
        "use_round_segments": True,      # Use round segments (filled circles) instead of rectangular segments

        # Glow effect parameters
        "glow_effect": True,             # Enable glow effect for segments and text
        "glow_radius": 0.2,              # Glow radius (0-1)
        "glow_intensity": 0.5,           # Glow intensity (0-1)
        "glow_color": "#FFFFFF",         # Glow color (defaults to segment color if not specified)
        "glow_blur_radius": 3,           # Blur radius for text glow effect

        # Sensitivity and gain settings
        "overall_master_gain": 1.0,      # Overall gain multiplier
        "freq_gain_min_mult": 0.4,       # Gain multiplier for lowest freq bar
        "freq_gain_max_mult": 1.8,       # Gain multiplier for highest freq bar
        "freq_gain_curve_power": 0.6,    # Shapes the transition curve
        "bar_height_power": 1.1,         # Non-linear height mapping
        "amplitude_compression_power": 1.0, # Amplitude compression

        # Color settings
        "color_lit_dark": (0.4, 0.4, 0.4),    # Base color for lit segments (inner)
        "color_lit_bright": (1.0, 1.0, 1.0),  # Color for lit segments (outer)
        "color_unlit": (0.08, 0.08, 0.08),    # Color for unlit segments
        "color_border": (0.0, 0.0, 0.0),      # Color for borders
        "lit_brightness_multiplier": 1.3,     # Brightness multiplier for lit segments
        "border_size": 0.08,                  # Border size (0-0.2, where 0.1 means 10% of segment is border)

        # Text settings
        "artist_color": "#FFFFFF",       # Artist name color
        "title_color": "#FFFFFF",        # Track title color
        "font_size": 24,                 # Font size for text
        "text_padding": 20,              # Padding for text

        # General settings
        "background_color": (0, 0, 0),   # Background color
        "debug_mode": False,             # Enable debug mode with test pattern
        "debug_level": 0,                # Debug level (0=off, 0.3=test pattern, 0.7=bar identification, 2=full debug)
    }

    # Update with user-provided config
    if config:
        default_config.update(config)

    # Set the number of bars for audio analysis based on the configured number of bars
    try:
        # Ensure num_bars is an integer
        default_config['num_bars'] = int(default_config.get('num_bars', 36))
        default_config['n_bars'] = default_config['num_bars']
    except (TypeError, ValueError) as e:
        print(f"Error converting num_bars to int: {e}")
        # Fallback to default
        default_config['num_bars'] = 36
        default_config['n_bars'] = 36

    # Ensure other numeric parameters are the correct type
    try:
        default_config['segments_per_bar'] = int(default_config.get('segments_per_bar', 15))
        default_config['inner_radius'] = float(default_config.get('inner_radius', 0.20))
        default_config['outer_radius'] = float(default_config.get('outer_radius', 0.40))
        default_config['bar_width'] = float(default_config.get('bar_width', 0.8))
        default_config['segment_spacing'] = int(default_config.get('segment_spacing', 2))
        default_config['border_size'] = float(default_config.get('border_size', 0.08))
        # Convert debug_level to float to handle decimal values like 0.7
        debug_level_value = default_config.get('debug_level', 0)
        try:
            default_config['debug_level'] = float(debug_level_value)
        except (ValueError, TypeError):
            print(f"Warning: Invalid debug_level value: {debug_level_value}, using default 0")
            default_config['debug_level'] = 0.0

        # Convert rectangular_bars to boolean
        rectangular_bars = default_config.get('rectangular_bars', True)
        if isinstance(rectangular_bars, str):
            rectangular_bars = rectangular_bars.lower() in ('true', 'yes', '1', 'on')
        default_config['rectangular_bars'] = bool(rectangular_bars)

        # Convert use_round_segments to boolean
        use_round_segments = default_config.get('use_round_segments', True)
        if isinstance(use_round_segments, str):
            use_round_segments = use_round_segments.lower() in ('true', 'yes', '1', 'on')
        default_config['use_round_segments'] = bool(use_round_segments)

        # Convert glow_effect to boolean
        glow_effect = default_config.get('glow_effect', True)
        if isinstance(glow_effect, str):
            glow_effect = glow_effect.lower() in ('true', 'yes', '1', 'on')
        default_config['glow_effect'] = bool(glow_effect)

        # Process glow parameters
        default_config['glow_radius'] = float(default_config.get('glow_radius', 0.2))
        default_config['glow_intensity'] = float(default_config.get('glow_intensity', 0.5))
        default_config['glow_blur_radius'] = int(default_config.get('glow_blur_radius', 3))
        default_config['overall_master_gain'] = float(default_config.get('overall_master_gain', 1.0))
        default_config['freq_gain_min_mult'] = float(default_config.get('freq_gain_min_mult', 0.4))
        default_config['freq_gain_max_mult'] = float(default_config.get('freq_gain_max_mult', 1.8))
        default_config['freq_gain_curve_power'] = float(default_config.get('freq_gain_curve_power', 0.6))
        default_config['bar_height_power'] = float(default_config.get('bar_height_power', 1.1))
        default_config['amplitude_compression_power'] = float(default_config.get('amplitude_compression_power', 1.0))
    except (TypeError, ValueError) as e:
        print(f"Error converting numeric parameters: {e}")

    return default_config
