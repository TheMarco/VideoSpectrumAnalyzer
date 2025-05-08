"""
Configuration processing for the Audioreactive Shader visualizer.
"""

def process_config(config=None):
    """
    Process and validate the configuration for the Audioreactive Shader visualizer.
    
    Args:
        config (dict, optional): User-provided configuration
        
    Returns:
        dict: Processed configuration with all required parameters
    """
    if config is None:
        config = {}
    
    # Set default values if not provided
    defaults = {
        # Basic settings
        "artist_name": "",
        "track_title": "",
        "artist_color": "#FFFFFF",
        "title_color": "#FFFFFF",
        "text_size": "medium",
        
        # Video output settings
        "width": 1280,
        "height": 720,
        "fps": 30,
        "duration": None,
        
        # Audio processing settings
        "min_freq": 30,
        "max_freq": 16000,
        "n_bars": 40,  # Number of frequency bands for audio analysis
    }
    
    # Apply defaults for missing values
    for key, value in defaults.items():
        if key not in config:
            config[key] = value
    
    # Convert hex color codes to RGB tuples
    if "artist_color" in config and isinstance(config["artist_color"], str) and config["artist_color"].startswith("#"):
        r = int(config["artist_color"][1:3], 16)
        g = int(config["artist_color"][3:5], 16)
        b = int(config["artist_color"][5:7], 16)
        config["artist_color"] = (r, g, b)
    
    if "title_color" in config and isinstance(config["title_color"], str) and config["title_color"].startswith("#"):
        r = int(config["title_color"][1:3], 16)
        g = int(config["title_color"][3:5], 16)
        b = int(config["title_color"][5:7], 16)
        config["title_color"] = (r, g, b)
    
    return config
