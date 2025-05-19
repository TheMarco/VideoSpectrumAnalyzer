"""
GL renderer for the Oscilloscope Waveform visualizer.
This renderer uses ModernGL to render the waveform using a GLSL shader.
"""
import os
import time
import numpy as np
from PIL import Image
import moderngl
import glfw

class GLOscilloscopeRenderer:
    """
    Class for rendering Oscilloscope Waveform frames using ModernGL.
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

        # Get parameters from config
        self.line_thickness = config.get("line_thickness", 2)
        self.scale = config.get("scale", 1.0)
        self.thickness_scale = config.get("thickness_scale", 0.3)

        # Print initialization info for debugging
        print(f"Initializing GL Oscilloscope Renderer with width={width}, height={height}")

        try:
            # Initialize GLFW
            if not glfw.init():
                raise RuntimeError("GLFW initialization failed")

            # Configure GLFW window hints
            glfw.window_hint(glfw.VISIBLE, glfw.FALSE)  # Hidden window
            glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
            glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
            glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)  # Required for macOS
            glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

            # Create an invisible window
            self.window = glfw.create_window(width, height, "Oscilloscope Renderer", None, None)
            if not self.window:
                glfw.terminate()
                raise RuntimeError("GLFW window creation failed")

            glfw.make_context_current(self.window)
            print("GLFW window created successfully")
        except Exception as e:
            print(f"Error initializing GLFW: {e}")
            raise

        try:
            # Create ModernGL context
            self.ctx = moderngl.create_context()
            print("ModernGL context created successfully")

            # Load shader
            self.shader_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "glsl", "ar_glowing_scope.glsl")
            print(f"Loading shader from: {self.shader_path}")

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

            # Create audio texture
            self.create_audio_texture()
            print("GL renderer initialization completed successfully")
        except Exception as e:
            print(f"Error during GL renderer initialization: {e}")
            self.cleanup()
            raise

    def create_audio_texture(self):
        """Create a texture for audio data."""
        # Create a texture for audio data
        self.audio_texture = self.ctx.texture((512, 2), 4)
        self.audio_texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.audio_texture.repeat_x = False
        self.audio_texture.repeat_y = False

        # Initialize with zeros
        self.audio_texture.write(np.zeros((512, 2, 4), dtype=np.uint8))

    def update_audio_texture(self, audio_data):
        """
        Update the audio texture with new audio data.

        Args:
            audio_data (numpy.ndarray): Audio data array (1D)
        """
        # Normalize audio data to 0-1 range
        normalized_data = np.clip((audio_data + 1.0) / 2.0, 0, 1)

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
        uniform sampler2D iChannel0;

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

    def render_frame(self, audio_data, current_time=None):
        """
        Render a frame with the current audio data.

        Args:
            audio_data (numpy.ndarray): Audio data for the current frame
            current_time (float, optional): Current time value

        Returns:
            PIL.Image: Rendered frame
        """
        try:
            # Calculate time if not provided
            if current_time is None:
                current_time = time.time() - self.start_time

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

            # Update audio texture
            self.update_audio_texture(audio_data)

            # Set time uniform
            if 'iTime' in self.prog:
                self.prog['iTime'].value = current_time

            # Bind the framebuffer
            self.fbo.use()

            # Clear the framebuffer
            self.ctx.clear(0.0, 0.0, 0.0, 0.0)

            # Bind the audio texture
            self.audio_texture.use(0)
            self.prog['iChannel0'].value = 0

            # Render the quad
            self.vao.render(moderngl.TRIANGLES)

            # Read the pixels from the framebuffer
            pixels = self.fbo.read(components=4)

            # Convert to PIL Image
            image = Image.frombytes('RGBA', (self.width, self.height), pixels).transpose(Image.FLIP_TOP_BOTTOM)

            return image
        except Exception as e:
            print(f"Error rendering frame: {e}")
            # Return a blank image as fallback
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

            # Terminate GLFW if initialized
            if hasattr(self, 'window') and self.window:
                try:
                    glfw.destroy_window(self.window)
                    self.window = None
                except Exception as e:
                    print(f"Error destroying GLFW window: {e}")

            try:
                glfw.terminate()
                print("GLFW terminated successfully")
            except Exception as e:
                print(f"Error terminating GLFW: {e}")

        except Exception as e:
            print(f"Error during cleanup: {e}")
