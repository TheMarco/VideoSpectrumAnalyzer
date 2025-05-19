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
    }
    
    # Update with user-provided config
    if config:
        default_config.update(config)

    # Set the number of bars for audio analysis based on the configured number of bars
    try:
        default_config['n_bars'] = int(default_config.get('num_bars'))
    except (TypeError, ValueError):
        existing_n_bars = default_config.get('n_bars')
        if isinstance(existing_n_bars, (list, tuple)):
            default_config['n_bars'] = len(existing_n_bars)
        else:
            default_config['n_bars'] = default_config.get('num_bars')
    
    return default_config
