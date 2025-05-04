"""
Utility functions for the Video Spectrum Analyzer.
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

def get_file_extension(filename):
    """
    Get the extension of a file.
    
    Args:
        filename (str): Filename
        
    Returns:
        str: File extension (lowercase, without the dot)
    """
    if not filename:
        return ""
    parts = filename.split(".")
    if len(parts) > 1:
        return parts[-1].lower()
    return ""

def is_audio_file(filename):
    """
    Check if a file is an audio file based on its extension.
    
    Args:
        filename (str): Filename
        
    Returns:
        bool: True if the file is an audio file, False otherwise
    """
    audio_extensions = {"mp3", "wav", "flac", "ogg", "m4a", "aac"}
    return get_file_extension(filename) in audio_extensions

def is_image_file(filename):
    """
    Check if a file is an image file based on its extension.
    
    Args:
        filename (str): Filename
        
    Returns:
        bool: True if the file is an image file, False otherwise
    """
    image_extensions = {"jpg", "jpeg", "png", "gif", "bmp", "webp"}
    return get_file_extension(filename) in image_extensions

def is_video_file(filename):
    """
    Check if a file is a video file based on its extension.
    
    Args:
        filename (str): Filename
        
    Returns:
        bool: True if the file is a video file, False otherwise
    """
    video_extensions = {"mp4", "mov", "avi", "mkv", "webm", "flv"}
    return get_file_extension(filename) in video_extensions
