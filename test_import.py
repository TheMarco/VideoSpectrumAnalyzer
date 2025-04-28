"""
Test script to verify the refactored code.
"""
try:
    import visualizer
    print("Visualizer module imported successfully!")
    
    # Test importing from modules
    from modules import utils, config_handler, audio_processor, media_handler, renderer, ffmpeg_handler
    print("All modules imported successfully!")
    
    # Test a simple function
    rgb = utils.hex_to_rgb("#FFFFFF")
    print(f"Hex to RGB conversion: #FFFFFF -> {rgb}")
    
    print("All tests passed!")
except Exception as e:
    print(f"Error: {e}")
