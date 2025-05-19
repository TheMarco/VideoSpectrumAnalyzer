"""
Simplified GL renderer for the Circular Spectrum visualizer.
This renderer uses ModernGL standalone context to render the circular spectrum using a GLSL shader.
"""
import os
import time
import numpy as np
from PIL import Image
import moderngl

class SimpleGLCircularRenderer:
    """
    Class for rendering Circular Spectrum frames using ModernGL standalone context.
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

        # Get parameters from config
        self.num_bars = config.get("num_bars", 36)
        self.segments_per_bar = config.get("segments_per_bar", 15)
        self.inner_radius = config.get("inner_radius", 0.20)
        self.outer_radius = config.get("outer_radius", 0.40)

        # Get sensitivity and gain settings
        self.overall_master_gain = config.get("overall_master_gain", 1.0)
        self.freq_gain_min_mult = config.get("freq_gain_min_mult", 0.4)
        self.freq_gain_max_mult = config.get("freq_gain_max_mult", 1.8)
        self.freq_gain_curve_power = config.get("freq_gain_curve_power", 0.6)
        self.bar_height_power = config.get("bar_height_power", 1.1)
        self.amplitude_compression_power = config.get("amplitude_compression_power", 1.0)

        # Print initialization info for debugging
        print(f"Initializing Simple GL Circular Renderer with width={width}, height={height}")

        try:
            # Create standalone ModernGL context
            self.ctx = moderngl.create_standalone_context()
            print("ModernGL standalone context created successfully")

            # Load Shadertoy-style circular spectrum shader
            self.shader_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "glsl",
                "circular_shadertoy.glsl"
            )
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

            # Create background texture
            self.create_background_texture()

            print("GL renderer initialization completed successfully")
        except Exception as e:
            print(f"Error during GL renderer initialization: {e}")
            self.cleanup()
            raise

    def create_audio_texture(self):
        """Create a texture for audio data."""
        # Create a texture for audio data with fixed width of 512 (like oscilloscope)
        width = 512
        self.audio_texture_width = width
        print(f"Creating audio texture with width={width}")

        # Create a texture with dimensions (width, 2) - width is the number of frequency bins
        # Use float32 format for better precision
        self.audio_texture = self.ctx.texture((width, 2), 4, dtype='f4')
        self.audio_texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
        self.audio_texture.repeat_x = False
        self.audio_texture.repeat_y = False

        # Initialize with zeros to ensure bars with no signal remain off
        init_data = np.zeros((width, 2, 4), dtype=np.float32)
        init_data[:, :, 3] = 1.0  # Set alpha to 1.0
        self.audio_texture.write(init_data)

        print(f"Audio texture initialized with zeros")

    def create_background_texture(self):
        """Create a texture for background image."""
        # Create a texture for background image
        self.background_texture = self.ctx.texture((self.width, self.height), 4)
        self.background_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.background_texture.repeat_x = False
        self.background_texture.repeat_y = False

        # Initialize with zeros
        self.background_texture.write(np.zeros((self.height, self.width, 4), dtype=np.uint8))

    def update_audio_texture(self, audio_data):
        """
        Update the audio texture with new audio data.

        Args:
            audio_data (numpy.ndarray): Audio data for the current frame
        """
        # Debug: Print min, max, and count of zero values in audio data
        zero_count = np.sum(audio_data == 0.0)
        print(f"Audio data stats - min: {np.min(audio_data):.6f}, max: {np.max(audio_data):.6f}, zeros: {zero_count}/{len(audio_data)}")

        # Debug: Print a few sample values to check distribution
        sample_indices = np.linspace(0, len(audio_data)-1, min(10, len(audio_data)), dtype=int)
        sample_values = [f"{i}: {audio_data[i]:.6f}" for i in sample_indices]
        print(f"Sample values: {', '.join(sample_values)}")

        # Normalize audio data to 0-1 range
        normalized_data = np.clip(audio_data, 0.0, 1.0)

        # Don't apply a noise floor - let zero values be zero
        # This ensures bars with no audio signal remain off

        # Amplify the values to make them more visible, but only for non-zero values
        # Find non-zero values
        non_zero_mask = normalized_data > 0.001

        # Apply power curve only to non-zero values
        normalized_data[non_zero_mask] = np.power(normalized_data[non_zero_mask], 0.5) * 1.5
        normalized_data = np.clip(normalized_data, 0.0, 1.0)

        # Create a 2D texture with audio data
        texture_width = 512  # Width of the texture (fixed like oscilloscope)
        texture_data = np.zeros((texture_width, 2, 4), dtype=np.float32)

        # Initialize texture with zeros - this ensures bars with no signal remain off
        texture_data.fill(0.0)
        texture_data[:, :, 3] = 1.0  # Set alpha channel to 1.0

        # Map the audio data to the texture
        # We need to map the audio data (which has num_bars values) to the texture (which has texture_width pixels)
        # For each bar, we'll fill a range of pixels in the texture

        num_bars = len(normalized_data)

        # Print some debug info about the audio data
        print(f"Audio data stats - min: {np.min(normalized_data):.6f}, max: {np.max(normalized_data):.6f}, zeros: {np.sum(normalized_data == 0)}/{len(normalized_data)}")

        # Sample a few values for debugging
        sample_indices = [0, int(texture_width/9), int(texture_width/4.5), int(texture_width/3),
                         int(texture_width/2.25), int(texture_width/1.8), int(texture_width/1.5),
                         int(texture_width/1.29), int(texture_width/1.125), texture_width-1]

        sample_values = []
        for idx in sample_indices:
            if idx < texture_width:
                sample_values.append(f"{idx}: {normalized_data[min(idx, len(normalized_data)-1)]:.6f}")

        print(f"Sample values: {', '.join(sample_values)}")

        # For each bar in the audio data
        for bar_idx in range(num_bars):
            # Get the amplitude for this bar
            amplitude = normalized_data[bar_idx]

            # Skip if amplitude is zero or very small
            if amplitude < 0.001:
                continue

            # Map this bar to a specific position in the texture
            # We want to ensure each bar gets exactly one texel in the texture
            # This makes sampling in the shader more precise
            texel_idx = int((bar_idx / num_bars) * texture_width)

            # Ensure we don't go out of bounds
            if texel_idx < texture_width:
                # Set the amplitude for this texel
                texture_data[texel_idx, 0, 0] = amplitude  # R channel
                texture_data[texel_idx, 0, 1] = amplitude  # G channel
                texture_data[texel_idx, 0, 2] = amplitude  # B channel

                # Also set the second row (for vertical redundancy)
                texture_data[texel_idx, 1, 0] = amplitude  # R channel
                texture_data[texel_idx, 1, 1] = amplitude  # G channel
                texture_data[texel_idx, 1, 2] = amplitude  # B channel

        # Update the texture
        self.audio_texture.write(texture_data)

    def update_background_texture(self, background_image):
        """
        Update the background texture with a new image.

        Args:
            background_image (PIL.Image): Background image
        """
        if background_image is None:
            # If no background image, use black
            self.background_texture.write(np.zeros((self.height, self.width, 4), dtype=np.uint8))
            return

        # Convert PIL image to numpy array
        if background_image.mode != 'RGBA':
            background_image = background_image.convert('RGBA')

        # Resize if needed
        if background_image.size != (self.width, self.height):
            background_image = background_image.resize((self.width, self.height))

        # Convert to numpy array and flip vertically for OpenGL
        bg_array = np.array(background_image)
        bg_array = np.flipud(bg_array)

        # Ensure the array is C-contiguous
        if not bg_array.flags['C_CONTIGUOUS']:
            bg_array = np.ascontiguousarray(bg_array)

        # Write to texture
        self.background_texture.write(bg_array)

    def _build_shader_program(self):
        """
        Build the shader program from the GLSL source.

        Returns:
            moderngl.Program: Compiled shader program
        """
        # Read shader source
        with open(self.shader_path, 'r') as f:
            shader_source = f.read()

        # Define vertex shader
        vertex_shader = """
        #version 330

        in vec2 in_vert;
        out vec2 v_text;

        void main() {
            gl_Position = vec4(in_vert, 0.0, 1.0);
            v_text = (in_vert + 1.0) / 2.0;
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
        uniform sampler2D iChannel1;

        // The shader body will be inserted here
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

            # Debug: Print the first few values of audio_data
            print(f"First 10 audio values: {audio_data[:10]}")

            # Process audio data to match ShaderToy behavior
            # Only amplify values that are actually present in the audio
            # Don't set a minimum floor for all values

            # Find the maximum value for normalization reference
            max_val = np.max(audio_data)
            if max_val > 0:
                # Normalize and apply a curve to make lower values more visible
                audio_data = audio_data / max_val
                audio_data = np.power(audio_data, 0.5) * 1.2

            # Don't set a minimum floor - let zero values be zero
            # This ensures bars with no audio signal remain off

            # Debug: Force specific values for testing
            # This helps identify if the issue is with the shader or the audio data
            debug_mode = False  # Set to True to test with fixed pattern
            if debug_mode:
                # Create a pattern where every 3rd bar is lit, others are partially lit or off
                for i in range(len(audio_data)):
                    if i % 3 == 0:
                        audio_data[i] = 1.0  # Full amplitude
                    elif i % 3 == 1:
                        audio_data[i] = 0.6  # Medium amplitude
                    else:
                        audio_data[i] = 0.0  # No amplitude (should be off)

            # Ensure audio_data is C-contiguous
            if not audio_data.flags['C_CONTIGUOUS']:
                audio_data = np.ascontiguousarray(audio_data)

            # Update audio texture (iChannel0)
            self.update_audio_texture(audio_data)

            # Update background texture (iChannel1)
            self.update_background_texture(background_image)

            # Set time uniform
            if 'iTime' in self.prog:
                self.prog['iTime'].value = current_time

            # Bind the framebuffer
            self.fbo.use()

            # Clear the framebuffer
            self.ctx.clear(0.0, 0.0, 0.0, 0.0)

            # Bind the audio texture to texture unit 0
            self.audio_texture.use(0)
            self.prog['iChannel0'].value = 0

            # Bind the background texture to texture unit 1
            self.background_texture.use(1)
            if 'iChannel1' in self.prog:
                self.prog['iChannel1'].value = 1
                print("Set iChannel1 uniform for background texture")

            # Render the quad
            self.vao.render(moderngl.TRIANGLES)

            # Read the pixels from the framebuffer
            pixels = self.fbo.read(components=4)

            # Ensure pixels data is C-contiguous
            if isinstance(pixels, np.ndarray) and not pixels.flags['C_CONTIGUOUS']:
                pixels = np.ascontiguousarray(pixels)

            # Convert to PIL Image
            result_image = Image.frombytes('RGBA', (self.width, self.height), pixels).transpose(Image.FLIP_TOP_BOTTOM)
            print(f"Rendered result image: size={result_image.size}, mode={result_image.mode}")

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
        """Clean up resources."""
        try:
            if hasattr(self, 'fbo') and self.fbo:
                self.fbo.release()
            if hasattr(self, 'fbo_texture') and self.fbo_texture:
                self.fbo_texture.release()
            if hasattr(self, 'audio_texture') and self.audio_texture:
                self.audio_texture.release()
            if hasattr(self, 'background_texture') and self.background_texture:
                self.background_texture.release()
            if hasattr(self, 'quad') and self.quad:
                self.quad.release()
            if hasattr(self, 'vao') and self.vao:
                self.vao.release()
            if hasattr(self, 'prog') and self.prog:
                self.prog.release()
            if hasattr(self, 'ctx') and self.ctx:
                self.ctx.release()
        except Exception as e:
            print(f"Error during cleanup: {e}")
