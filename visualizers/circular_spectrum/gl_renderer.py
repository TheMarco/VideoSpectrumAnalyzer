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

        # Get parameters from config - ensure numeric values are the correct type
        self.num_bars = int(config.get("num_bars", 36))
        self.segments_per_bar = int(config.get("segments_per_bar", 15))
        self.inner_radius = float(config.get("inner_radius", 0.20))
        self.outer_radius = float(config.get("outer_radius", 0.40))

        # Store debug mode setting
        self.debug_mode = bool(config.get("debug_mode", False))

        # Set debug level (0=off, 1=basic debug, 2=full debug)
        # Convert to float first to handle decimal values like 0.7
        debug_level_value = config.get("debug_level", 0)
        try:
            self.debug_level = float(debug_level_value)
        except (ValueError, TypeError):
            print(f"Warning: Invalid debug_level value: {debug_level_value}, using default 0")
            self.debug_level = 0.0

        # Set bar shape (rectangular vs radial)
        self.rectangular_bars = bool(config.get("rectangular_bars", True))

        # Get sensitivity and gain settings - ensure they're floats
        self.overall_master_gain = float(config.get("overall_master_gain", 1.0))
        self.freq_gain_min_mult = float(config.get("freq_gain_min_mult", 0.4))
        self.freq_gain_max_mult = float(config.get("freq_gain_max_mult", 1.8))
        self.freq_gain_curve_power = float(config.get("freq_gain_curve_power", 0.6))
        self.bar_height_power = float(config.get("bar_height_power", 1.1))
        self.amplitude_compression_power = float(config.get("amplitude_compression_power", 1.0))

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

        # The audio data should already be normalized from render_frame
        # Just ensure it's in the 0-1 range
        normalized_data = np.clip(audio_data, 0.0, 1.0)

        # Don't apply additional amplification here - we already did that in render_frame
        # This prevents double-amplification which could cause maxed-out bars

        # Create a 2D texture with audio data
        texture_width = 512  # Width of the texture (fixed like oscilloscope)
        texture_data = np.zeros((texture_width, 2, 4), dtype=np.float32)

        # Initialize texture with zeros - this ensures bars with no signal remain off
        texture_data.fill(0.0)
        texture_data[:, :, 3] = 1.0  # Set alpha channel to 1.0

        # Map the audio data to the texture
        # We need to map the audio data (which has num_bars values) to the texture (which has texture_width pixels)
        num_bars = len(normalized_data)

        # Print some debug info about the audio data
        print(f"Audio data stats - min: {np.min(normalized_data):.6f}, max: {np.max(normalized_data):.6f}, zeros: {np.sum(normalized_data == 0)}/{len(normalized_data)}")
        print(f"Number of bars: {num_bars}, Texture width: {texture_width}")

        # IMPROVED MAPPING: Instead of mapping each bar to a single texel, we'll distribute the bars
        # evenly across the texture width, ensuring each bar gets represented in the texture

        # Calculate how many texels each bar should occupy
        try:
            texels_per_bar = float(texture_width) / float(num_bars)
        except Exception as e:
            print(f"Error calculating texels_per_bar: {e}")
            print(f"texture_width: {texture_width}, type: {type(texture_width)}")
            print(f"num_bars: {num_bars}, type: {type(num_bars)}")
            # Default to a safe value
            texels_per_bar = 10.0

        # For each bar in the audio data
        for bar_idx in range(num_bars):
            try:
                # Get the amplitude for this bar
                amplitude = float(normalized_data[bar_idx])

                # Calculate the start and end texel indices for this bar
                start_texel = int(float(bar_idx) * texels_per_bar)
                end_texel = int(float(bar_idx + 1) * texels_per_bar)

                # Ensure we don't go out of bounds
                end_texel = min(end_texel, texture_width)
            except Exception as e:
                print(f"Error processing bar {bar_idx}: {e}")
                # Skip this bar
                continue

            # Fill all texels for this bar with the amplitude value
            for texel_idx in range(start_texel, end_texel):
                # Set the amplitude for this texel
                texture_data[texel_idx, 0, 0] = amplitude  # R channel
                texture_data[texel_idx, 0, 1] = amplitude  # G channel
                texture_data[texel_idx, 0, 2] = amplitude  # B channel

                # Also set the second row (for vertical redundancy)
                texture_data[texel_idx, 1, 0] = amplitude  # R channel
                texture_data[texel_idx, 1, 1] = amplitude  # G channel
                texture_data[texel_idx, 1, 2] = amplitude  # B channel

        # Debug: Sample a few values from the texture to verify
        sample_indices = [0, int(texture_width/9), int(texture_width/4.5), int(texture_width/3),
                         int(texture_width/2.25), int(texture_width/1.8), int(texture_width/1.5),
                         int(texture_width/1.29), int(texture_width/1.125), texture_width-1]

        sample_values = []
        for idx in sample_indices:
            if idx < texture_width:
                sample_values.append(f"{idx}: {texture_data[idx, 0, 0]:.6f}")

        print(f"Texture sample values: {', '.join(sample_values)}")

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
                import time
                current_time = time.time() - self.start_time

            # Debug logging for background image
            if background_image is not None:
                print(f"GL renderer received background image: size={background_image.size}, mode={background_image.mode}")
            else:
                print("GL renderer received no background image")

            # Make sure audio_data is not empty and is a numpy array
            if audio_data is None:
                print("Warning: None audio data provided to GL renderer")
                # Create a dummy audio data array with zeros
                audio_data = np.zeros(self.num_bars, dtype=np.float32)
            elif not isinstance(audio_data, np.ndarray):
                print(f"Warning: Converting audio_data from {type(audio_data)} to numpy array")
                try:
                    # Try to convert to numpy array
                    audio_data = np.array(audio_data, dtype=np.float32)
                except Exception as e:
                    print(f"Error converting audio_data to numpy array: {e}")
                    # Create a dummy audio data array with zeros
                    audio_data = np.zeros(self.num_bars, dtype=np.float32)

            # Check if the array is empty
            if len(audio_data) == 0:
                print("Warning: Empty audio data provided to GL renderer")
                # Create a dummy audio data array with zeros
                audio_data = np.zeros(self.num_bars, dtype=np.float32)

            # Ensure audio_data matches the number of bars
            # This is important for proper mapping to the texture
            try:
                if len(audio_data) < self.num_bars:
                    # Pad with zeros if too short
                    audio_data = np.pad(audio_data, (0, self.num_bars - len(audio_data)), 'constant')
                elif len(audio_data) > self.num_bars:
                    # Truncate if too long
                    audio_data = audio_data[:self.num_bars]
            except Exception as e:
                print(f"Error resizing audio_data: {e}")
                # Create a new array with the correct size
                audio_data = np.zeros(self.num_bars, dtype=np.float32)

            # Debug: Print the first few values of audio_data
            print(f"First 10 audio values: {audio_data[:10]}")
            print(f"Last 10 audio values: {audio_data[-10:]}")
            print(f"Audio data shape: {audio_data.shape}, num_bars: {self.num_bars}")

            # Print specific bar values to help identify problematic bars
            if self.debug_level > 0.5:
                print("Bar values for debugging:")
                for i in range(len(audio_data)):
                    if i < 3 or i >= len(audio_data) - 3:  # First 3 and last 3 bars
                        print(f"  Bar {i}: {audio_data[i]:.6f}")

            # Process audio data to match ShaderToy behavior
            # Only amplify values that are actually present in the audio
            # Don't set a minimum floor for all values

            # Find the maximum value for normalization reference
            max_val = np.max(audio_data)
            if max_val > 0:
                # Normalize but with a more conservative approach to prevent maxing out
                audio_data = audio_data / max_val

                # Apply a noise gate to filter out very low values
                noise_gate = 0.05
                audio_data[audio_data < noise_gate] = 0.0

                # Apply a curve with reduced gain to prevent maxing out
                # Use a lower power value to make the curve more gradual
                # and a lower multiplier to reduce overall amplitude
                audio_data = np.power(audio_data, 0.7) * 0.8

                # Ensure we don't exceed 1.0
                audio_data = np.clip(audio_data, 0.0, 1.0)

                # Simple handling for first and last bars
                if len(audio_data) > 2:
                    # First bar - mix with second bar
                    audio_data[0] = 0.7 * audio_data[0] + 0.3 * audio_data[1]
                    # Last bar - mix with second-to-last bar
                    audio_data[-1] = 0.7 * audio_data[-1] + 0.3 * audio_data[-2]

                # Print stats about the processed audio data
                print(f"Processed audio data - min: {np.min(audio_data):.6f}, max: {np.max(audio_data):.6f}")
                non_zero = np.sum(audio_data > 0.0)
                print(f"Non-zero values: {non_zero}/{len(audio_data)} ({non_zero/len(audio_data)*100:.1f}%)")

            # Don't set a minimum floor - let zero values be zero
            # This ensures bars with no audio signal remain off

            # Debug mode can be enabled for testing
            self.debug_mode = False  # Disable debug mode to use real audio data
            self.debug_level = 0.0  # Set debug level to 0.0

            # Only use test pattern if debug mode is enabled
            if self.debug_mode:
                print(f"DEBUG MODE ENABLED: Using test pattern for audio data (level: {self.debug_level})")

                # Create a pattern where bars have varying amplitudes based on time
                # This ensures the bars are always moving
                import math
                import time

                # Get current time for animation
                animation_time = time.time()

                # Create a pattern where bars have varying amplitudes
                for i in range(len(audio_data)):
                    # Create a moving pattern based on time
                    phase = (i / len(audio_data)) * 2 * math.pi  # Spread phases across bars
                    # Use sine wave with time-based offset for animation
                    audio_data[i] = 0.5 + 0.5 * math.sin(animation_time * 2 + phase)

                # Print the first few values to verify they're changing
                print(f"First 3 audio values: {audio_data[:3]}")

            # Ensure audio_data is C-contiguous
            if not audio_data.flags['C_CONTIGUOUS']:
                audio_data = np.ascontiguousarray(audio_data)

            # Update audio texture (iChannel0)
            self.update_audio_texture(audio_data)

            # Update background texture (iChannel1)
            self.update_background_texture(background_image)

            # Set time uniform - VERY IMPORTANT for animation
            if 'iTime' in self.prog:
                self.prog['iTime'].value = current_time
                print(f"Setting iTime to {current_time}")

            # Also set uTime if it exists
            if 'uTime' in self.prog:
                self.prog['uTime'].value = current_time
                print(f"Setting uTime to {current_time}")

            # Set debug mode uniform if it exists in the shader
            # Note: We use uDebugMode, not iDebugMode in our shader

            # Also set uDebugMode if it exists
            if 'uDebugMode' in self.prog:
                self.prog['uDebugMode'].value = 0.0  # Disable debug mode to show actual visualization

            # Set all the configuration uniforms
            self._set_shader_uniforms()

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

    def _set_shader_uniforms(self):
        """
        Set all the configuration uniforms in the shader.
        """
        # Set number of bars and segments
        if 'uNumBars' in self.prog:
            self.prog['uNumBars'].value = self.num_bars

        if 'uSegmentsPerBar' in self.prog:
            self.prog['uSegmentsPerBar'].value = self.segments_per_bar

        # Set radius values
        if 'uInnerRadius' in self.prog:
            self.prog['uInnerRadius'].value = self.inner_radius

        if 'uOuterRadius' in self.prog:
            self.prog['uOuterRadius'].value = self.outer_radius

        # Set border size
        if 'uBorderSize' in self.prog:
            self.prog['uBorderSize'].value = self.config.get("border_size", 0.08)

        # Set bar width
        if 'uBarWidth' in self.prog:
            self.prog['uBarWidth'].value = self.config.get("bar_width", 0.8)

        # Set time uniform for animation
        if 'uTime' in self.prog:
            import time
            current_time = time.time() - self.start_time
            self.prog['uTime'].value = current_time
            print(f"Setting uTime to {current_time}")

        # Set debug mode
        if 'uDebugMode' in self.prog:
            self.prog['uDebugMode'].value = 0.0  # Disable debug mode to show actual visualization

        # Set bar shape (rectangular vs radial)
        if 'uRectangularBars' in self.prog:
            self.prog['uRectangularBars'].value = 1.0 if self.rectangular_bars else 0.0

        # Set sensitivity and gain settings
        if 'uOverallMasterGain' in self.prog:
            self.prog['uOverallMasterGain'].value = self.overall_master_gain

        if 'uFreqGainMinMult' in self.prog:
            self.prog['uFreqGainMinMult'].value = self.freq_gain_min_mult

        if 'uFreqGainMaxMult' in self.prog:
            self.prog['uFreqGainMaxMult'].value = self.freq_gain_max_mult

        if 'uFreqGainCurvePower' in self.prog:
            self.prog['uFreqGainCurvePower'].value = self.freq_gain_curve_power

        if 'uBarHeightPower' in self.prog:
            self.prog['uBarHeightPower'].value = self.bar_height_power

        if 'uAmplitudeCompressionPower' in self.prog:
            self.prog['uAmplitudeCompressionPower'].value = self.amplitude_compression_power

        # Print the values being set for debugging
        print(f"Setting shader uniforms:")
        print(f"  uNumBars: {self.num_bars}")
        print(f"  uSegmentsPerBar: {self.segments_per_bar}")
        print(f"  uInnerRadius: {self.inner_radius}")
        print(f"  uOuterRadius: {self.outer_radius}")
        print(f"  uBorderSize: {self.config.get('border_size', 0.08)}")
        print(f"  uBarWidth: {self.config.get('bar_width', 0.8)}")
        print(f"  uDebugMode: 0.0 (debug mode disabled)")
        print(f"  uRectangularBars: {1.0 if self.rectangular_bars else 0.0}")

        # Show time uniform value
        import time
        current_time = time.time() - self.start_time
        print(f"  uTime: {current_time} (for animation)")
        print(f"  uOverallMasterGain: {self.overall_master_gain}")
        print(f"  uFreqGainMinMult: {self.freq_gain_min_mult}")
        print(f"  uFreqGainMaxMult: {self.freq_gain_max_mult}")
        print(f"  uFreqGainCurvePower: {self.freq_gain_curve_power}")
        print(f"  uBarHeightPower: {self.bar_height_power}")
        print(f"  uAmplitudeCompressionPower: {self.amplitude_compression_power}")

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
