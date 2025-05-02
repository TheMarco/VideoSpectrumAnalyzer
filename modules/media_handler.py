"""
Media handling functions for the spectrum analyzer.
"""
import os
import cv2
from PIL import Image, ImageFont

def load_background_media(background_image_path, background_video_path, width, height):
    """
    Load background media (image or video) for the visualizer.
    
    Args:
        background_image_path (str): Path to background image file
        background_video_path (str): Path to background video file
        width (int): Target width for the background
        height (int): Target height for the background
        
    Returns:
        tuple: (background_pil, video_capture, bg_frame_count, bg_fps)
    """
    background_pil = None
    video_capture = None
    bg_frame_count = 0
    bg_fps = 30
    
    # Try to load video first
    if background_video_path and os.path.exists(background_video_path):
        try:
            print(f"Loading background video: {background_video_path}")
            video_capture = cv2.VideoCapture(background_video_path)
            
            if not video_capture.isOpened():
                raise IOError(f"Cannot open video file: {background_video_path}")
            
            bg_fps = video_capture.get(cv2.CAP_PROP_FPS)
            bg_frame_count = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
            bg_width = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            bg_height = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if bg_frame_count <= 0 or bg_fps <= 0:
                print(f"Warning: Could not read properties from video {background_video_path}.")
                ret, _ = video_capture.read()
                if not ret:
                    raise IOError(f"Cannot read first frame from video: {background_video_path}")
            
            print(f"Background video loaded: {bg_width}x{bg_height} @ {bg_fps:.2f} FPS, {bg_frame_count} frames")
            background_pil = None  # Ensure PIL image isn't used
            
        except Exception as e:
            print(f"Warning: Could not load background video: {e}. Checking image fallback.")
            if video_capture:
                video_capture.release()
            video_capture = None
            background_video_path = None  # Clear video path if loading failed
    
    # If video loading failed or no video specified, try to load image
    if not video_capture and background_image_path and os.path.exists(background_image_path):
        try:
            print(f"Loading background image: {background_image_path}")
            with Image.open(background_image_path) as _img:
                background_pil = _img.convert("RGBA")
                
            # Resize image to match output dimensions
            if background_pil.width != width or background_pil.height != height:
                print(f"Resizing background image from {background_pil.width}x{background_pil.height} to {width}x{height}")
                # Use Resampling.LANCZOS if available (PIL >= 9.1.0), otherwise use LANCZOS
                try:
                    background_pil = background_pil.resize((width, height), Image.Resampling.LANCZOS)
                except AttributeError:
                    # Fallback for older PIL versions
                    background_pil = background_pil.resize((width, height), Image.LANCZOS)
                
            print(f"Background image loaded: {background_pil.width}x{background_pil.height}")
            
        except Exception as e:
            print(f"Warning: Could not load background image: {e}")
            background_pil = None
    
    return background_pil, video_capture, bg_frame_count, bg_fps

def load_fonts(text_size="large"):
    """
    Load fonts for artist name and track title.
    
    Args:
        text_size (str): Size preset - "small", "medium", or "large"
        
    Returns:
        tuple: (artist_font, title_font)
    """
    print("--- FONT LOADING ---")
    
    # Define font sizes based on the text_size parameter - make them more distinct
    if text_size == "small":
        font_size_artist = 28  # Smaller
        font_size_title = 16   # Smaller
    elif text_size == "medium":
        font_size_artist = 48  # Medium
        font_size_title = 24   # Medium
    else:  # "large" or any other value as fallback
        font_size_artist = 72  # Current large size
        font_size_title = 36   # Current large size
    
    print(f"   Using text size preset: {text_size} (Artist: {font_size_artist}px, Title: {font_size_title}px)")
    
    artist_font = None
    title_font = None
    font_load_success = False
    
    local_font_path_bold = "DejaVuSans-Bold.ttf"
    local_font_path_regular = "DejaVuSans.ttf"
    fallback_font_paths = [
        ("arialbd.ttf", "arial.ttf"), 
        ("Arial Bold.ttf", "Arial.ttf"), 
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    ]
    
    # Try to load fonts with the specified sizes
    try:
        if os.path.exists(local_font_path_bold) and os.path.exists(local_font_path_regular):
            artist_font = ImageFont.truetype(local_font_path_bold, font_size_artist)
            title_font = ImageFont.truetype(local_font_path_regular, font_size_title)
            font_load_success = True
            print(f"   Success loading local fonts with sizes: Artist {font_size_artist}px, Title {font_size_title}px")
        else:
            raise IOError("Local fonts not found")
    except Exception as e:
        print(f"   Error loading local fonts: {e}\nAttempting fallback system fonts...")
        for bold_path, regular_path in fallback_font_paths:
            if font_load_success:
                break
            try:
                artist_font = ImageFont.truetype(bold_path, font_size_artist)
                title_font = ImageFont.truetype(regular_path, font_size_title)
                font_load_success = True
                print(f"   Success loading fallback pair: {bold_path}, {regular_path} with sizes: Artist {font_size_artist}px, Title {font_size_title}px")
                break
            except Exception as e:
                print(f"   Failed to load font pair: {bold_path}, {regular_path}. Error: {e}")
    
    if not font_load_success:
        print("--- All font loading attempts failed. Falling back to default font. ---")
        # Default font doesn't support custom sizes well, so we'll still have size issues
        artist_font = ImageFont.load_default()
        title_font = ImageFont.load_default()
    
    # Verify the font sizes were applied correctly
    print(f"   Final font sizes - Artist: {getattr(artist_font, 'size', 'unknown')}px, Title: {getattr(title_font, 'size', 'unknown')}px")
    print("--- FONT LOADING COMPLETE ---")
    
    return artist_font, title_font

def process_video_frame(video_capture, width, height, last_good_frame=None):
    """
    Read and process a frame from a video capture.
    
    Args:
        video_capture: OpenCV video capture object
        width (int): Target width for the frame
        height (int): Target height for the frame
        last_good_frame (PIL.Image, optional): Last successfully read frame
        
    Returns:
        tuple: (current_frame_pil, last_good_frame_pil)
    """
    current_frame_pil = None
    
    if not video_capture:
        return None, last_good_frame
    
    ret, frame_bgr = video_capture.read()
    
    if not ret:
        print("End of background video or read error. Looping...")
        video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame_bgr = video_capture.read()
    
    if not ret:
        print("ERROR: Failed read after looping. Using fallback.")
        return last_good_frame.copy() if last_good_frame else None, last_good_frame
    
    try:
        # Convert BGR to RGB
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        
        # Resize if needed
        if frame_rgb.shape[1] != width or frame_rgb.shape[0] != height:
            frame_rgb = cv2.resize(frame_rgb, (width, height), interpolation=cv2.INTER_LANCZOS4)
        
        # Convert to PIL Image
        current_frame_pil = Image.fromarray(frame_rgb).convert("RGBA")
        
        # Update last good frame
        last_good_frame = current_frame_pil.copy()
        
    except Exception as e:
        print(f"Error processing video frame: {e}")
        if last_good_frame:
            current_frame_pil = last_good_frame.copy()
    
    return current_frame_pil, last_good_frame
