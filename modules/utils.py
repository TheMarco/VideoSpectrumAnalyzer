"""
Utility functions for the spectrum analyzer.
"""

def hex_to_rgb(hex_color, default=(255, 255, 255)):
    """
    Convert a hex color string to an RGB tuple.
    
    Args:
        hex_color (str): Hex color string (e.g., "#FFFFFF")
        default (tuple): Default RGB tuple to return if conversion fails
        
    Returns:
        tuple: RGB tuple (e.g., (255, 255, 255))
    """
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 6:
        try:
            return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
        except ValueError:
            pass
    return default
