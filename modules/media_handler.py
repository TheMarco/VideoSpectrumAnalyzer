"""
Media handling functions for the spectrum analyzer.
"""
import os
import cv2
from PIL import Image, ImageFont
import subprocess
import numpy as np
import sys
import importlib.util
import logging
from modules.shader_error import ShaderError

logger = logging.getLogger('audio_visualizer.media_handler')

# Define the vertex shader for GLSL rendering
VERTEX_SHADER = """
#version 330

in vec2 in_vert;
out vec2 v_text;

void main() {
    v_text = in_vert * 0.5 + 0.5;
    gl_Position = vec4(in_vert, 0.0, 1.0);
}
"""

def prerender_shader_background(shader_path, duration, fps, width, height, progress_callback=None):
    """
    Pre-render a shader animation as a video file using a separate process.

    Args:
        shader_path (str): Path to the shader file
        duration (float): Duration of the video in seconds
        fps (int): Frames per second
        width (int): Width of the video
        height (int): Height of the video
        progress_callback (callable, optional): Callback function for progress updates

    Returns:
        str: Path to the rendered video file, or None if rendering failed
    """
    try:
        print(f"Pre-rendering shader background: {shader_path}")
        print(f"Duration: {duration}s, FPS: {fps}, Resolution: {width}x{height}")
        print(f"DEBUG: progress_callback is {'provided' if progress_callback else 'NOT provided'}")
        if progress_callback:
            print(f"DEBUG: progress_callback type: {type(progress_callback)}")
            # Test the callback
            progress_callback(1, "Starting shader pre-rendering...")

        # Create a temporary file for the pre-rendered video
        import tempfile
        import json
        import subprocess
        import threading
        import time

        output_path = tempfile.mktemp(suffix='.mp4')
        status_file = tempfile.mktemp(suffix='.json')

        # Create the initial status file
        with open(status_file, 'w') as f:
            json.dump({"progress": 0, "message": "Initializing shader pre-rendering...", "timestamp": time.time()}, f)

        # Build the command to run the shader pre-rendering process
        cmd = [
            sys.executable,
            "shader_prerender_process.py",
            shader_path,
            output_path,
            status_file,
            "--duration", str(duration),
            "--fps", str(fps),
            "--width", str(width),
            "--height", str(height)
        ]

        # Start the shader pre-rendering process
        print(f"Starting shader pre-rendering process: {' '.join(cmd)}")
        process = subprocess.Popen(cmd)

        # Start a thread to monitor the status file and update the progress
        def monitor_status():
            last_progress = 0
            last_message = ""

            while process.poll() is None:
                try:
                    if os.path.exists(status_file):
                        with open(status_file, 'r') as f:
                            status = json.load(f)

                        progress = status.get("progress", 0)
                        message = status.get("message", "")

                        if progress != last_progress or message != last_message:
                            print(f"Shader pre-rendering progress: {progress}%, {message}")
                            if progress_callback:
                                progress_callback(progress, message)

                            last_progress = progress
                            last_message = message
                except Exception as e:
                    print(f"Error reading status file: {e}")

                time.sleep(0.5)

        # Start the monitoring thread
        monitor_thread = threading.Thread(target=monitor_status)
        monitor_thread.daemon = True
        monitor_thread.start()

        # Wait for the process to complete
        process.wait()

        # Check if the process was successful
        if process.returncode != 0:
            print(f"Shader pre-rendering process failed with return code {process.returncode}")
            return None

        # Wait for the monitoring thread to finish
        monitor_thread.join(timeout=1.0)

        # Check if the output file was created
        if os.path.exists(output_path):
            print(f"Shader background pre-rendered successfully: {output_path}")
            return output_path
        else:
            print("Shader pre-rendering failed: output file not found")
            return None
    except Exception as e:
        print(f"Error pre-rendering shader background: {e}")
        import traceback
        traceback.print_exc()
        return None

def load_background_media(background_image_path, background_video_path, background_shader_path, width, height, duration=10.0, fps=30, progress_callback=None):
    """
    Load background media (image, video, or shader).

    Args:
        background_image_path (str): Path to background image
        background_video_path (str): Path to background video
        background_shader_path (str): Path to background shader
        width (int): Width of the output
        height (int): Height of the output
        duration (float, optional): Duration of the audio in seconds. Defaults to 10.0.
        fps (int, optional): Frames per second. Defaults to 30.
        progress_callback (callable, optional): Callback function for progress updates.

    Returns:
        tuple: (background_pil, video_capture, bg_frame_count, bg_fps, shader_renderer)
    """
    import cv2
    from PIL import Image
    import os
    import importlib.util
    import sys

    background_pil = None
    video_capture = None
    bg_frame_count = 0
    bg_fps = 30
    shader_renderer = None

    # Try to load shader first if specified
    if background_shader_path and os.path.exists(background_shader_path):
        if progress_callback:
            progress_callback(10, f"Loading background shader: {os.path.basename(background_shader_path)}")

        print(f"Loading background shader: {background_shader_path}")

        # Try to pre-render the shader as a video
        try:
            print(f"Pre-rendering shader as video: {background_shader_path}")
            if progress_callback:
                progress_callback(20, f"Starting shader pre-rendering: {os.path.basename(background_shader_path)}...")

            # Create a temporary file for the pre-rendered video
            import tempfile
            temp_output_path = tempfile.mktemp(suffix='.mp4')
            print(f"Using temporary output path: {temp_output_path}")

            # Pre-render the shader as a video
            prerendered_video_path = prerender_shader_background(
                background_shader_path,
                duration,
                fps,
                width,
                height,
                progress_callback
            )

            # If pre-rendering was successful, treat it as a regular video
            if prerendered_video_path and os.path.exists(prerendered_video_path):
                # Check if the file has content (not empty)
                if os.path.getsize(prerendered_video_path) > 0:
                    print(f"Pre-rendering successful, using video: {prerendered_video_path}")
                    if progress_callback:
                        progress_callback(60, "Shader pre-rendering complete, loading video...")

                    # Set the background_video_path to the pre-rendered video
                    background_video_path = prerendered_video_path

                    # Clear the shader path to ensure we don't try to use real-time rendering
                    background_shader_path = None
                else:
                    print("Pre-rendered video file is empty, falling back to real-time rendering")
                    if progress_callback:
                        progress_callback(60, "Pre-rendered video is empty, trying real-time rendering...")
            else:
                print("Pre-rendering failed, falling back to real-time rendering")
                if progress_callback:
                    progress_callback(60, "Pre-rendering failed, trying real-time rendering...")
        except Exception as e:
            print(f"Error pre-rendering shader: {e}")
            print("Falling back to real-time rendering")
            if progress_callback:
                progress_callback(60, f"Error pre-rendering shader: {str(e)[:50]}...")
            # Don't propagate pre-rendering errors, just fall back to real-time rendering

        # If pre-rendering failed or was skipped, try real-time rendering
        if background_shader_path:
            # No try-except here - let errors propagate to the caller
            print("Attempting to use separate process GPU-based OpenGL renderer...")
            if progress_callback:
                progress_callback(70, "Initializing real-time shader renderer...")

            # Import the ProcessShaderRenderer
            from modules.process_shader_renderer import ProcessShaderRenderer

            # Create the GPU-based renderer - let exceptions propagate
            print(f"Creating ProcessShaderRenderer for {background_shader_path}...")
            shader_renderer = ProcessShaderRenderer(background_shader_path, width, height)
            print("ProcessShaderRenderer instance created successfully")

            if progress_callback:
                progress_callback(80, "Testing shader renderer...")

            print(f"Background shader loaded: {background_shader_path}")

            # Test render a frame to make sure it works - let exceptions propagate
            test_frame = shader_renderer.render_frame(0.0)
            print(f"Test frame rendered: {test_frame.size}, mode: {test_frame.mode}")

            # Save test frame for debugging
            test_frame.save("shader_test_frame.png")
            print("Test frame saved to shader_test_frame.png")

            if progress_callback:
                progress_callback(100, "Shader renderer initialized successfully")

            return background_pil, video_capture, bg_frame_count, bg_fps, shader_renderer

    # Try to load video if shader failed or not specified
    if not shader_renderer and background_video_path and os.path.exists(background_video_path):
        try:
            if progress_callback:
                progress_callback(60, f"Loading background video: {os.path.basename(background_video_path)}...")

            print(f"Loading background video: {background_video_path}")
            print(f"File exists: {os.path.exists(background_video_path)}")
            print(f"File size: {os.path.getsize(background_video_path)} bytes")

            # Try to open the video file
            video_capture = cv2.VideoCapture(background_video_path)
            print(f"Video capture created: {video_capture}")
            print(f"Video capture isOpened: {video_capture.isOpened()}")

            if not video_capture.isOpened():
                raise IOError(f"Cannot open video file: {background_video_path}")

            if progress_callback:
                progress_callback(70, "Reading video properties...")

            # Get video properties
            bg_fps = video_capture.get(cv2.CAP_PROP_FPS)
            bg_frame_count = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))
            bg_width = int(video_capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            bg_height = int(video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"Video properties: FPS={bg_fps}, FRAME_COUNT={bg_frame_count}, WIDTH={bg_width}, HEIGHT={bg_height}")

            if progress_callback:
                progress_callback(80, "Testing video playback...")

            # Test reading a frame
            ret, test_frame = video_capture.read()
            print(f"Test frame read: ret={ret}, frame_shape={test_frame.shape if ret else 'None'}")

            # Reset the video to the beginning
            video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            print(f"Reset video position to 0")

            if bg_frame_count <= 0 or bg_fps <= 0:
                print(f"Warning: Could not read properties from video {background_video_path}.")
                ret, _ = video_capture.read()
                if not ret:
                    raise IOError(f"Cannot read first frame from video: {background_video_path}")
                # Reset the video to the beginning again
                video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)

            print(f"Background video loaded successfully: {bg_width}x{bg_height} @ {bg_fps:.2f} FPS, {bg_frame_count} frames")
            background_pil = None  # Ensure PIL image isn't used

            if progress_callback:
                progress_callback(100, f"Background video loaded: {bg_width}x{bg_height} @ {bg_fps:.2f} FPS")

        except Exception as e:
            print(f"Warning: Could not load background video: {e}. Checking image fallback.")
            if video_capture:
                video_capture.release()
            video_capture = None
            background_video_path = None  # Clear video path if loading failed

            if progress_callback:
                progress_callback(60, f"Video loading failed: {str(e)[:50]}... Trying image fallback.")

    # If video loading failed or no video specified, try to load image
    if not shader_renderer and not video_capture and background_image_path and os.path.exists(background_image_path):
        try:
            if progress_callback:
                progress_callback(70, f"Loading background image: {os.path.basename(background_image_path)}...")

            print(f"Loading background image: {background_image_path}")
            with Image.open(background_image_path) as _img:
                background_pil = _img.convert("RGBA")

            # Resize image to match output dimensions
            if background_pil.width != width or background_pil.height != height:
                if progress_callback:
                    progress_callback(80, f"Resizing image to {width}x{height}...")

                print(f"Resizing background image from {background_pil.width}x{background_pil.height} to {width}x{height}")
                # Use Resampling.LANCZOS if available (PIL >= 9.1.0), otherwise use LANCZOS
                try:
                    background_pil = background_pil.resize((width, height), Image.Resampling.LANCZOS)
                except AttributeError:
                    # Fallback for older PIL versions
                    background_pil = background_pil.resize((width, height), Image.LANCZOS)

            print(f"Background image loaded: {background_pil.width}x{background_pil.height}")

            if progress_callback:
                progress_callback(100, f"Background image loaded: {background_pil.width}x{background_pil.height}")

        except Exception as e:
            print(f"Warning: Could not load background image: {e}")
            background_pil = None

            if progress_callback:
                progress_callback(100, f"Failed to load background image: {str(e)[:50]}...")

    return background_pil, video_capture, bg_frame_count, bg_fps, shader_renderer

class ShaderRenderer:
    """
    Class to render GLSL shaders as background frames.
    This implementation is based on the working shader.py in the glsl directory.
    """
    def __init__(self, shader_module, shader_path, width, height):
        """
        Initialize the shader renderer.

        Args:
            shader_module: The imported shader.py module
            shader_path (str): Path to the GLSL shader file
            width (int): Width of the output
            height (int): Height of the output
        """
        import moderngl
        import numpy as np
        import glfw
        import time
        import os
        import sys

        self.shader_path = shader_path
        self.width = width
        self.height = height
        self.start_time = time.time()

        print(f"Initializing M3 Mac-compatible shader renderer for {shader_path} at {width}x{height}")

        # Add glsl directory to path to ensure we can import the shader module
        glsl_dir = os.path.dirname(os.path.abspath(shader_path))
        if glsl_dir not in sys.path:
            sys.path.append(glsl_dir)
            print(f"Added {glsl_dir} to Python path")

        # Initialize GLFW
        if not glfw.init():
            raise RuntimeError("GLFW initialization failed")

        # Configure GLFW window hints for offscreen rendering
        glfw.window_hint(glfw.VISIBLE, glfw.FALSE)  # Hidden window
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)  # Required for macOS
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

        # Create an invisible window
        self.window = glfw.create_window(width, height, "Shader Renderer", None, None)
        if not self.window:
            glfw.terminate()
            raise RuntimeError("GLFW window creation failed")

        glfw.make_context_current(self.window)
        print("GLFW window created successfully")

        # Create ModernGL context
        self.ctx = moderngl.create_context()
        print(f"ModernGL context created: {self.ctx}")

        # Load shader from file using shader_module's functions
        has_main, body, inline = shader_module.load_snippet(shader_path)
        print(f"Shader loaded: has_main={has_main}, body length={len(body)}")

        # Build the shader program
        try:
            self.prog = shader_module.build_program(self.ctx, has_main, body, inline)
            print("Shader program built successfully")
        except Exception as e:
            print(f"Error building shader program: {e}")
            glfw.terminate()
            raise

        # Create vertex buffer and VAO
        self.quad = self.ctx.buffer(np.array([
            -1, -1,   1, -1,   -1, 1,
            -1,  1,   1, -1,    1, 1,
        ], dtype='f4').tobytes())

        try:
            self.vao = self.ctx.simple_vertex_array(self.prog, self.quad, 'in_vert')
            print("Created vertex array object")
        except Exception as e:
            print(f"Error creating VAO: {e}")
            glfw.terminate()
            raise

        # Set uniforms
        try:
            # Set iResolution uniform
            if 'iResolution' in self.prog:
                self.prog['iResolution'].value = (width, height, 1.0)
                print("Set iResolution uniform")

            # Set empty mouse uniform
            if 'iMouse' in self.prog:
                self.prog['iMouse'].value = (0.0, 0.0, 0.0, 0.0)
                print("Set iMouse uniform")
        except Exception as e:
            print(f"Error setting uniforms: {e}")
            glfw.terminate()
            raise

        # Create framebuffer for offscreen rendering
        try:
            self.fbo = self.ctx.framebuffer(
                color_attachments=[self.ctx.texture((width, height), 4)]
            )
            print("Created framebuffer for offscreen rendering")
        except Exception as e:
            print(f"Error creating framebuffer: {e}")
            glfw.terminate()
            raise

        print(f"Shader initialization complete at time {self.start_time}")

    def render_frame(self, current_time=None):
        """
        Render a frame from the shader at the given time.

        Args:
            current_time (float, optional): Time to use for rendering. If None, uses elapsed time.

        Returns:
            PIL.Image: Rendered frame
        """
        import time
        from PIL import Image
        import numpy as np
        import glfw

        # Calculate time if not provided
        if current_time is None:
            current_time = time.time() - self.start_time

        # Set time uniform
        if 'iTime' in self.prog:
            self.prog['iTime'].value = current_time

        # Process GLFW events to keep the context alive
        glfw.poll_events()

        # Render to framebuffer
        self.fbo.use()
        self.ctx.clear(0.0, 0.0, 0.0, 1.0)
        self.vao.render()

        # Read pixels
        data = self.fbo.read(components=4)

        # Check if data is all zeros or nearly all zeros (black screen)
        pixel_data = np.frombuffer(data, dtype=np.uint8)

        # Calculate the average brightness of the image
        # This is more robust than checking if all pixels are exactly 0
        avg_brightness = np.mean(pixel_data)

        # Check if the image is completely black or nearly black
        if avg_brightness < 1.0:
            print(f"Error: Rendered frame is completely or nearly black (avg brightness: {avg_brightness})")

            # Save the black image for debugging
            debug_image = Image.frombytes('RGBA', (self.width, self.height), data).transpose(Image.FLIP_TOP_BOTTOM)
            debug_path = f"shader_debug_black_{os.path.basename(self.shader_path)}.png"
            debug_image.save(debug_path)
            print(f"Saved debug black image to {debug_path}")

            # Create a detailed error message
            error_message = f"""
The shader '{self.shader_path}' was compiled successfully but produced a black or nearly black image.
This usually indicates a problem with the shader code.

Error details:
- Shader path: {self.shader_path}
- Dimensions: {self.width}x{self.height}
- Time value: {current_time}
- Average brightness: {avg_brightness}

Possible solutions:
1. Check if the shader has logic errors
"""
            # Log the error
            print(error_message)

            # Create an error image for the UI
            from PIL import ImageDraw, ImageFont
            error_image = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 255))
            draw = ImageDraw.Draw(error_image)

            # Add error text
            try:
                # Try to load a font
                font = ImageFont.truetype("Arial.ttf", 24)
            except:
                # Fall back to default font
                font = ImageFont.load_default()

            # Draw the error message
            shader_name = os.path.basename(self.shader_path)
            draw.text((self.width//2, self.height//2 - 50), f"SHADER ERROR: {shader_name}",
                     fill=(255, 0, 0), anchor="mm", font=font)
            draw.text((self.width//2, self.height//2), f"Shader produced a black image (brightness: {avg_brightness:.2f})",
                     fill=(255, 0, 0), anchor="mm", font=font)
            draw.text((self.width//2, self.height//2 + 50), "See logs for details",
                     fill=(255, 0, 0), anchor="mm", font=font)

            # Save the error image for reference
            error_image_path = f"shader_error_black_{os.path.basename(self.shader_path)}.png"
            error_image.save(error_image_path)
            print(f"Saved error image to {error_image_path}")

            # Raise our custom ShaderError exception
            raise ShaderError(
                message=f"Shader produced a black image (brightness: {avg_brightness:.2f})",
                shader_path=self.shader_path,
                details=error_message
            )

        # Convert to PIL Image
        image = Image.frombytes('RGBA', (self.width, self.height), data).transpose(Image.FLIP_TOP_BOTTOM)
        return image

    def cleanup(self):
        """Clean up resources."""
        import glfw

        try:
            # Clean up ModernGL resources
            if hasattr(self, 'fbo'):
                self.fbo.release()
            if hasattr(self, 'quad'):
                self.quad.release()
            if hasattr(self, 'prog'):
                self.prog.release()

            # Clean up GLFW
            if hasattr(self, 'window') and self.window:
                glfw.destroy_window(self.window)
                glfw.terminate()
                print("GLFW resources cleaned up")
        except Exception as e:
            print(f"Error during cleanup: {e}")
            pass

    def __del__(self):
        """Ensure cleanup when the object is garbage collected."""
        self.cleanup()

class SimpleShaderRenderer:
    """
    A shader renderer that throws immediate errors instead of using fallback patterns.
    This replaces the previous CPU-based renderer that used checkerboard patterns.
    """
    def __init__(self, shader_path, width, height):
        """
        Initialize the shader renderer.

        Args:
            shader_path (str): Path to the shader file
            width (int): Width of the output
            height (int): Height of the output

        Raises:
            RuntimeError: Always raises an error with detailed information about the shader failure
        """
        import os
        import traceback
        import time
        from PIL import Image, ImageDraw, ImageFont

        self.shader_path = shader_path
        self.width = width
        self.height = height

        # Get the shader name for the error message
        shader_name = os.path.basename(shader_path)

        # Collect error information
        error_info = {
            "shader_path": shader_path,
            "shader_name": shader_name,
            "width": width,
            "height": height,
            "traceback": traceback.format_exc()
        }

        # Create a detailed error message
        error_message = f"""
SHADER ERROR: Failed to render shader '{shader_name}'

The shader '{shader_path}' could not be rendered using the GPU-based renderer.
Instead of falling back to a CPU-based renderer with checkerboard patterns,
this error is being thrown immediately to provide better feedback.

Error details:
- Shader path: {shader_path}
- Dimensions: {width}x{height}
- Traceback: {error_info['traceback']}

Possible solutions:
1. Check if the shader has syntax errors
"""

        # Log the error
        print(error_message)

        # Create an error image for the UI
        error_image = Image.new("RGBA", (width, height), (0, 0, 0, 255))
        draw = ImageDraw.Draw(error_image)

        # Add error text
        try:
            # Try to load a font
            font = ImageFont.truetype("Arial.ttf", 24)
        except:
            # Fall back to default font
            font = ImageFont.load_default()

        # Draw the error message
        draw.text((width//2, height//2 - 50), f"SHADER ERROR: {shader_name}",
                 fill=(255, 0, 0), anchor="mm", font=font)
        draw.text((width//2, height//2), "Shader could not be rendered",
                 fill=(255, 0, 0), anchor="mm", font=font)
        draw.text((width//2, height//2 + 50), "See logs for details",
                 fill=(255, 0, 0), anchor="mm", font=font)

        # Save the error image for reference
        error_image_path = f"shader_error_{shader_name}.png"
        error_image.save(error_image_path)
        print(f"Saved error image to {error_image_path}")

        # Raise the error
        raise RuntimeError(f"Shader '{shader_name}' failed to render. See logs for details.")

    def render_frame(self, current_time=None):
        """
        This method should never be called since the constructor always raises an error.

        Raises:
            RuntimeError: Always raises an error
        """
        raise RuntimeError("SimpleShaderRenderer.render_frame() should never be called")

    def cleanup(self):
        """Clean up resources (no-op for this renderer)."""
        pass

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

def process_video_frame(video_capture, shader_renderer, width, height, current_time, last_good_frame):
    """
    Process a video frame for the current time.

    Args:
        video_capture: OpenCV video capture object
        shader_renderer: Shader renderer object
        width (int): Frame width
        height (int): Frame height
        current_time (float): Current time in seconds
        last_good_frame: Last successfully rendered frame

    Returns:
        tuple: (current_frame_pil, last_good_frame_pil)
    """
    current_frame_pil = None
    from PIL import Image  # Import Image here to ensure it's available

    # First check if video_capture is available (prioritize pre-rendered video)
    if video_capture:
        try:
            # Calculate the frame position based on current_time and FPS
            fps = video_capture.get(cv2.CAP_PROP_FPS)
            total_frames = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))

            if fps > 0 and total_frames > 0:
                # Calculate the frame index based on time
                frame_idx = int(current_time * fps) % total_frames

                # Set the frame position directly instead of reading sequentially
                video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)

            # Get the frame from the video
            ret, frame_bgr = video_capture.read()

            # If we reached the end of the video, loop back to the beginning
            if not ret:
                video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame_bgr = video_capture.read()

            if ret:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

                # Resize if needed
                if frame_rgb.shape[1] != width or frame_rgb.shape[0] != height:
                    frame_rgb = cv2.resize(frame_rgb, (width, height), interpolation=cv2.INTER_LANCZOS4)

                # Convert to PIL Image
                current_frame_pil = Image.fromarray(frame_rgb).convert("RGBA")

                # Update last good frame
                last_good_frame = current_frame_pil.copy()
                return current_frame_pil, last_good_frame
            else:
                print("Failed to read video frame after looping. Falling back to shader renderer if available.")
                # Fall through to shader renderer if video read fails
        except Exception as e:
            print(f"Error processing video frame: {e}")
            # Fall through to shader renderer if video processing fails

    # If video capture failed or is not available, try shader renderer
    if shader_renderer:
        # Render the frame - don't catch exceptions here to allow them to propagate
        # This ensures that shader errors are properly displayed to the user
        current_frame_pil = shader_renderer.render_frame(current_time)

        # Update last good frame
        last_good_frame = current_frame_pil.copy()
        return current_frame_pil, last_good_frame

    # If we get here, neither video_capture nor shader_renderer worked
    if last_good_frame:
        return last_good_frame.copy(), last_good_frame
    else:
        # Create a fallback frame
        print("Creating fallback frame - no video or shader available")
        from PIL import Image, ImageDraw
        fallback = Image.new("RGBA", (width, height), (0, 0, 0, 255))
        draw = ImageDraw.Draw(fallback)
        draw.text((width//2, height//2), "No Background Available", fill=(255, 255, 255), anchor="mm")
        return fallback, fallback
