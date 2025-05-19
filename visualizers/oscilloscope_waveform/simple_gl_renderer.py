"""
Simplified GL renderer for the Oscilloscope Waveform visualizer.
This renderer uses ModernGL standalone context to render the waveform using a GLSL shader.
"""
import os
import time
import numpy as np
from PIL import Image
import moderngl

class SimpleGLOscilloscopeRenderer:
    """
    Class for rendering Oscilloscope Waveform frames using ModernGL standalone context.
    This is a simplified version that doesn't rely on GLFW.
    """

    def __init__(self, width, height, config):
        """
        Initialize the GL renderer.

        Args:
            width (int): Frame width.
            height (int): Frame height.
            config (dict): Configuration dictionary.
        """
        self.width = width
        self.height = height
        self.config = config
        self.start_time = time.time()

        # Get parameters from config with enhanced defaults to match the screenshot
        self.line_thickness = config.get("line_thickness", 2)
        self.scale = config.get("scale", 1.8)  # Increased from 1.0 to match shader change
        self.thickness_scale = config.get("thickness_scale", 0.25)  # Reduced from 0.3 to match shader change

        # Get line color from config
        self.line_color = config.get("line_color_rgb", (255, 255, 255))
        # Convert RGB tuple to normalized float values for shader
        self.line_color_normalized = tuple(c / 255.0 for c in self.line_color)

        # Get smoothing factor from config - reduced for more detail
        self.smoothing_factor = config.get("smoothing_factor", 0.15)  # Reduced from 0.2 for more detail

        # Get persistence factor for trailing effect
        self.persistence = config.get("persistence", 0.7)  # Default to 0.7 for a moderate trailing effect

        # Get vertical offset for waveform position
        self.vertical_offset = config.get("vertical_offset", -0.4)  # Default to -0.4 to lower the waveform
        print(f"Initialized vertical_offset to {self.vertical_offset} from config")

        # Check if we should use the standard settings (renamed from original settings)
        self.use_standard_settings = config.get("use_standard_settings", True)

        # Print initialization info for debugging
        print(f"Initializing Simple GL Oscilloscope Renderer with width={width}, height={height}")

        try:
            # Create standalone ModernGL context
            self.ctx = moderngl.create_standalone_context()
            print("ModernGL standalone context created successfully")

            # Load shader with background support
            self.shader_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "glsl", "ar_glowing_scope_with_bg.glsl")
            print(f"Loading shader from: {self.shader_path}")

            if not os.path.exists(self.shader_path):
                # Fall back to original shader if the background-enabled one doesn't exist
                print(f"Background-enabled shader not found, falling back to original shader")
                self.shader_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "glsl", "ar_glowing_scope.glsl")
                print(f"Falling back to: {self.shader_path}")

                if not os.path.exists(self.shader_path):
                    raise FileNotFoundError(f"Shader file not found: {self.shader_path}")

            self.prog = self._build_shader_program()
            print("Shader program built successfully")

            # Create vertex buffer and VAO
            self.quad = self.ctx.buffer(np.array([
                -1, -1,   1, -1,   -1, 1,
                -1,  1,   1, -1,    1, 1,
            ], dtype='f4').tobytes())
            self.vao = self.ctx.simple_vertex_array(self.prog, self.quad, 'in_vert')

            # Set uniforms
            self.prog['iResolution'].value = (width, height, 1.0)
            if 'iMouse' in self.prog:
                self.prog['iMouse'].value = (0.0, 0.0, 0.0, 0.0)

            # Create framebuffer and texture for rendering
            self.fbo_texture = self.ctx.texture((width, height), 4)
            self.fbo = self.ctx.framebuffer(self.fbo_texture)

            # Create audio texture (iChannel0)
            self.create_audio_texture()

            # Create previous frame texture (iChannel1)
            self.create_previous_frame_texture()

            # Create background texture (iChannel2)
            self.create_background_texture()

            print("Simple GL renderer initialization completed successfully")
        except Exception as e:
            print(f"Error during Simple GL renderer initialization: {e}")
            self.cleanup()
            raise

    def create_audio_texture(self):
        """Create a texture for audio data (iChannel0)."""
        # Create a texture for audio data
        self.audio_texture = self.ctx.texture((512, 2), 4)
        self.audio_texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.audio_texture.repeat_x = False
        self.audio_texture.repeat_y = False

        # Initialize with zeros
        self.audio_texture.write(np.zeros((512, 2, 4), dtype=np.uint8))

    def create_previous_frame_texture(self):
        """Create a texture for the previous frame (iChannel1)."""
        # Create a texture for the previous frame
        self.previous_frame_texture = self.ctx.texture((self.width, self.height), 4)
        self.previous_frame_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.previous_frame_texture.repeat_x = False
        self.previous_frame_texture.repeat_y = False

        # Initialize with black transparent texture
        self.previous_frame_texture.write(np.zeros((self.height, self.width, 4), dtype=np.uint8))

        # Flag to track if we have a previous frame
        self.has_previous_frame = False

    def create_background_texture(self):
        """Create a texture for background image (iChannel2)."""
        # Create a texture for background image
        self.background_texture = self.ctx.texture((self.width, self.height), 4)
        self.background_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.background_texture.repeat_x = False
        self.background_texture.repeat_y = False

        # Initialize with black transparent texture
        self.background_texture.write(np.zeros((self.height, self.width, 4), dtype=np.uint8))

    def update_background_texture(self, background_image):
        """
        Update the background texture with a new image.

        Args:
            background_image (PIL.Image): Background image to use
        """
        if background_image is None:
            # If no background image, use black
            self.background_texture.write(np.zeros((self.height, self.width, 4), dtype=np.uint8))
            return

        # Ensure background_image is in RGBA mode
        if background_image.mode != 'RGBA':
            background_image = background_image.convert('RGBA')

        # Ensure background_image has the correct size
        if background_image.size != (self.width, self.height):
            background_image = background_image.resize((self.width, self.height), Image.LANCZOS)

        # Convert PIL image to numpy array
        img_data = np.array(background_image)

        # Write the image data to the texture
        self.background_texture.write(img_data)

    def update_audio_texture(self, audio_data):
        """
        Update the audio texture with new audio data.

        Args:
            audio_data (numpy.ndarray): Audio data array (1D)
        """
        # Process audio data exactly like the original shader
        # The original shader expects audio data in the range [-1, 1]
        # We'll just ensure it's in that range without changing its characteristics

        # Clip to [-1, 1] range to prevent extreme values
        clipped_data = np.clip(audio_data, -1.0, 1.0)

        # Normalize audio data to 0-1 range for texture (required for GL texture)
        normalized_data = np.clip((clipped_data + 1.0) / 2.0, 0, 1)

        # Create a 2D texture with audio data
        texture_width = 512  # Width of the texture
        texture_data = np.zeros((texture_width, 2, 4), dtype=np.uint8)

        # Fill the texture with audio data
        for i in range(min(texture_width, len(normalized_data))):
            value = int(normalized_data[i] * 255)
            texture_data[i, 0, 0] = value  # R channel
            texture_data[i, 0, 1] = value  # G channel
            texture_data[i, 0, 2] = value  # B channel
            texture_data[i, 0, 3] = 255    # A channel

            texture_data[i, 1, 0] = value  # R channel
            texture_data[i, 1, 1] = value  # G channel
            texture_data[i, 1, 2] = value  # B channel
            texture_data[i, 1, 3] = 255    # A channel

        # Update the texture
        self.audio_texture.write(texture_data)

    def _build_shader_program(self):
        """
        Build the shader program from the GLSL file.

        Returns:
            moderngl.Program: Compiled shader program
        """
        # Read the shader file
        with open(self.shader_path, 'r') as f:
            shader_source = f.read()

        # Define vertex shader
        vertex_shader = """
        #version 330

        in vec2 in_vert;
        out vec2 v_text;

        void main() {
            v_text = in_vert * 0.5 + 0.5;
            gl_Position = vec4(in_vert, 0.0, 1.0);
        }
        """

        # Define fragment shader template
        fragment_shader_template = """
        #version 330

        in vec2 v_text;
        out vec4 f_color;

        uniform vec3 iResolution;
        uniform float iTime;
        uniform vec4 iMouse;
        uniform sampler2D iChannel0;  // Audio data
        uniform sampler2D iChannel1;  // Previous frame for persistence effect
        uniform sampler2D iChannel2;  // Background image

        // Custom uniforms for oscilloscope settings
        uniform vec4 iLineColor;        // Line color (RGBA)
        uniform float iThicknessScale;  // Thickness scale (smaller = thicker)
        uniform float iLineThickness;   // Line thickness (1-5, higher = thicker)
        uniform float iAmplitudeScale;  // Amplitude scale (larger = taller waveform)
        uniform float iSmoothingFactor; // Smoothing factor (0.0 - 1.0)
        uniform float iUseOriginalSettings; // Whether to use all original settings (1.0) or user settings (0.0)
        uniform float iPersistence;     // Persistence factor for trailing effect (0.0 - 1.0)
        uniform float iVerticalOffset;  // Vertical offset for the waveform position

        {shader_body}

        void main() {{
            vec4 fragColor;
            mainImage(fragColor, v_text * iResolution.xy);
            f_color = fragColor;
        }}
        """

        # Insert the shader body into the template
        fragment_shader = fragment_shader_template.format(shader_body=shader_source)

        try:
            # Create the program
            program = self.ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)
            return program
        except Exception as e:
            print(f"Error compiling shader program: {e}")
            raise

    def render_frame(self, audio_data, background_image=None, current_time=None):
        """
        Render a frame with the current audio data.

        Args:
            audio_data (numpy.ndarray): Audio data for the current frame
            background_image (PIL.Image, optional): Background image to composite with
            current_time (float, optional): Current time value

        Returns:
            PIL.Image: Rendered frame
        """
        try:
            # Calculate time if not provided
            if current_time is None:
                current_time = time.time() - self.start_time

            # Debug logging for background image
            if background_image is not None:
                print(f"GL renderer received background image: size={background_image.size}, mode={background_image.mode}")
            else:
                print("GL renderer received no background image")

            # Make sure audio_data is not empty
            if audio_data is None or len(audio_data) == 0:
                print("Warning: Empty audio data provided to GL renderer")
                # Create a dummy audio data array with zeros
                audio_data = np.zeros(512)

            # Ensure audio_data is the right shape
            if len(audio_data) < 512:
                # Pad with zeros if too short
                audio_data = np.pad(audio_data, (0, 512 - len(audio_data)), 'constant')
            elif len(audio_data) > 512:
                # Truncate if too long
                audio_data = audio_data[:512]

            # Update audio texture (iChannel0)
            self.update_audio_texture(audio_data)

            # Update background texture (iChannel1)
            self.update_background_texture(background_image)

            # Set time uniform
            if 'iTime' in self.prog:
                self.prog['iTime'].value = current_time

            # Set custom uniforms for oscilloscope settings
            if 'iLineColor' in self.prog:
                # Convert RGB tuple to RGBA with alpha=1.0
                self.prog['iLineColor'].value = (*self.line_color_normalized, 1.0)

            if 'iThicknessScale' in self.prog:
                self.prog['iThicknessScale'].value = self.thickness_scale
                print(f"Setting iThicknessScale uniform to {self.thickness_scale}")
            else:
                print("WARNING: iThicknessScale uniform not found in shader program")

            if 'iLineThickness' in self.prog:
                self.prog['iLineThickness'].value = float(self.line_thickness)
                print(f"Setting iLineThickness uniform to {self.line_thickness}")
            else:
                print("WARNING: iLineThickness uniform not found in shader program")

            if 'iAmplitudeScale' in self.prog:
                self.prog['iAmplitudeScale'].value = self.scale
                print(f"Setting iAmplitudeScale uniform to {self.scale}")
            else:
                print("WARNING: iAmplitudeScale uniform not found in shader program")

            if 'iSmoothingFactor' in self.prog:
                self.prog['iSmoothingFactor'].value = self.smoothing_factor
                print(f"Setting iSmoothingFactor uniform to {self.smoothing_factor}")
            else:
                print("WARNING: iSmoothingFactor uniform not found in shader program")

            if 'iUseOriginalSettings' in self.prog:
                # For backward compatibility, we still use the iUseOriginalSettings uniform
                # but now it represents whether to use standard settings
                self.prog['iUseOriginalSettings'].value = 1.0 if self.use_standard_settings else 0.0
                print(f"Setting iUseOriginalSettings uniform to {1.0 if self.use_standard_settings else 0.0} (using standard settings: {self.use_standard_settings})")

            if 'iPersistence' in self.prog:
                self.prog['iPersistence'].value = self.persistence

            if 'iVerticalOffset' in self.prog:
                self.prog['iVerticalOffset'].value = self.vertical_offset
                print(f"Setting iVerticalOffset uniform to {self.vertical_offset}")
            else:
                print("WARNING: iVerticalOffset uniform not found in shader program")

            # Bind the framebuffer
            self.fbo.use()

            # Clear the framebuffer
            self.ctx.clear(0.0, 0.0, 0.0, 0.0)

            # Bind the audio texture to texture unit 0
            self.audio_texture.use(0)
            self.prog['iChannel0'].value = 0

            # Bind the previous frame texture to texture unit 1
            self.previous_frame_texture.use(1)
            if 'iChannel1' in self.prog:
                self.prog['iChannel1'].value = 1
                print("Set iChannel1 uniform for previous frame texture")

            # Bind the background texture to texture unit 2
            self.background_texture.use(2)
            if 'iChannel2' in self.prog:
                self.prog['iChannel2'].value = 2
                print("Set iChannel2 uniform for background texture")

            # Render the quad
            self.vao.render(moderngl.TRIANGLES)

            # Read the pixels from the framebuffer
            pixels = self.fbo.read(components=4)

            # Convert to PIL Image
            result_image = Image.frombytes('RGBA', (self.width, self.height), pixels).transpose(Image.FLIP_TOP_BOTTOM)
            print(f"Rendered result image: size={result_image.size}, mode={result_image.mode}")

            # Store the current frame as the previous frame for the next render
            if self.has_previous_frame:
                # Copy the current frame to the previous frame texture
                self.fbo.use()
                self.previous_frame_texture.write(pixels)
            else:
                # First frame, set the flag to true for subsequent frames
                self.has_previous_frame = True
                self.previous_frame_texture.write(pixels)

            return result_image
        except Exception as e:
            print(f"Error rendering frame: {e}")
            import traceback
            traceback.print_exc()
            # Return the background image as fallback if available
            if background_image is not None:
                print("Returning background image as fallback due to error")
                return background_image.copy()
            else:
                # Return a blank image as fallback
                print("Returning blank image as fallback due to error")
                return Image.new('RGBA', (self.width, self.height), (0, 0, 0, 255))

    def cleanup(self):
        """
        Clean up GL resources.
        """
        try:
            # Release ModernGL resources
            if hasattr(self, 'prog') and self.prog:
                self.prog.release()
                self.prog = None

            if hasattr(self, 'vao') and self.vao:
                self.vao.release()
                self.vao = None

            if hasattr(self, 'quad') and self.quad:
                self.quad.release()
                self.quad = None

            if hasattr(self, 'fbo') and self.fbo:
                self.fbo.release()
                self.fbo = None

            if hasattr(self, 'fbo_texture') and self.fbo_texture:
                self.fbo_texture.release()
                self.fbo_texture = None

            if hasattr(self, 'audio_texture') and self.audio_texture:
                self.audio_texture.release()
                self.audio_texture = None

            if hasattr(self, 'previous_frame_texture') and self.previous_frame_texture:
                self.previous_frame_texture.release()
                self.previous_frame_texture = None

            if hasattr(self, 'background_texture') and self.background_texture:
                self.background_texture.release()
                self.background_texture = None

            if hasattr(self, 'ctx') and self.ctx:
                self.ctx.release()
                self.ctx = None

        except Exception as e:
            print(f"Error during cleanup: {e}")
            import traceback
            traceback.print_exc()
