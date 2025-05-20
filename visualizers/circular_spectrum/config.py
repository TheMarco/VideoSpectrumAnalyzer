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
        "border_size": 0.08,             # Border size for segments (0-1)
        "bar_width": 0.8,                # Width of bars (0-1, where 1 means bars touch, lower values create gaps)
        "rectangular_bars": False,       # Use rectangular bars (True) or radial/trapezoid bars (False)

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
        "color_border": (0.0, 0.0, 0.0),      # Border color
        "lit_brightness_multiplier": 1.3,     # Brightness multiplier for lit segments

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
        default_config['border_size'] = float(default_config.get('border_size', 0.08))
        default_config['bar_width'] = float(default_config.get('bar_width', 0.8))
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
        default_config['overall_master_gain'] = float(default_config.get('overall_master_gain', 1.0))
        default_config['freq_gain_min_mult'] = float(default_config.get('freq_gain_min_mult', 0.4))
        default_config['freq_gain_max_mult'] = float(default_config.get('freq_gain_max_mult', 1.8))
        default_config['freq_gain_curve_power'] = float(default_config.get('freq_gain_curve_power', 0.6))
        default_config['bar_height_power'] = float(default_config.get('bar_height_power', 1.1))
        default_config['amplitude_compression_power'] = float(default_config.get('amplitude_compression_power', 1.0))
    except (TypeError, ValueError) as e:
        print(f"Error converting numeric parameters: {e}")

    return default_config
