"""
Renderer for the Smooth Curves visualizer.
"""

import os
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import moderngl
from modules.media_handler import load_fonts

class SmoothCurvesRenderer:
    """
    GL renderer for the Smooth Curves visualizer.
    """

    def __init__(self, width, height, config):
        """
        Initialize the GL renderer.

        Args:
            width (int): Frame width.
            height (int): Frame height.
            config (dict): Configuration dictionary.
        """
        # Print debug info
        print(f"SmoothCurvesRenderer.__init__(width={width}, height={height}, config={config})")

        # Ensure width and height are integers for the frame dimensions
        try:
            self.width = int(width)
            self.height = int(height)
        except ValueError as e:
            print(f"Error converting width/height to int: {e}")
            # Use default values if conversion fails
            self.width = 1280
            self.height = 720

        self.config = config
        self.start_time = time.time()

        # Get parameters from config and convert to appropriate types
        try:
            self.line_thickness = float(config.get("line_thickness", 3.0))
            self.bloom_size = float(config.get("bloom_size", 20.0))
            self.bloom_intensity = float(config.get("bloom_intensity", 0.5))
            self.bloom_falloff = float(config.get("bloom_falloff", 1.5))
            self.fill_enabled = str(config.get("fill_enabled", True)).lower() in ("true", "1", "t", "y", "yes")
            self.fill_opacity = float(config.get("fill_opacity", 0.3))
            self.scale = float(config.get("scale", 0.2))
            self.shift = float(config.get("shift", 0.05))
            # Use width_param to avoid confusion with the frame width
            self.width_param = float(config.get("width", 0.06))
            self.amp = float(config.get("amp", 1.0))

            # Reactivity parameters
            self.decay_speed = float(config.get("decay_speed", 0.7))
            self.attack_speed = float(config.get("attack_speed", 0.9))
            self.noise_gate = float(config.get("noise_gate", 0.05))
        except ValueError as e:
            print(f"Error converting config values to float: {e}")
            # Use default values if conversion fails
            self.line_thickness = 3.0
            self.bloom_size = 20.0
            self.bloom_intensity = 0.5
            self.bloom_falloff = 1.5
            self.fill_enabled = True
            self.fill_opacity = 0.3
            self.scale = 0.2
            self.shift = 0.05
            self.width_param = 0.06
            self.amp = 1.0
            self.decay_speed = 0.7
            self.attack_speed = 0.9
            self.noise_gate = 0.05

        # Get colors from config
        self.color1 = config.get("color1_rgb", (203, 36, 128))
        self.color2 = config.get("color2_rgb", (41, 200, 192))
        self.color3 = config.get("color3_rgb", (24, 137, 218))

        # Convert RGB tuples to normalized float values for shader
        self.color1_normalized = tuple(c / 255.0 for c in self.color1)
        self.color2_normalized = tuple(c / 255.0 for c in self.color2)
        self.color3_normalized = tuple(c / 255.0 for c in self.color3)

        # Load fonts for text rendering
        text_size = config.get("text_size", "large")
        self.artist_font, self.title_font = load_fonts(text_size=text_size)

        # Print initialization info for debugging
        print(f"Initializing Smooth Curves Renderer with width={self.width}, height={self.height}, width_param={self.width_param}")

        try:
            # Create standalone ModernGL context with performance optimizations
            self.ctx = moderngl.create_standalone_context(require=330)
            # Enable performance optimizations
            self.ctx.enable(moderngl.BLEND)
            self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
            print("ModernGL standalone context created successfully with performance optimizations")

            # Load shader
            self.shader_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "glsl", "ar_smooth_curves.glsl")
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

            # Set uniforms - ensure width and height are floats
            self.prog['iResolution'].value = (float(width), float(height), 1.0)
            if 'iMouse' in self.prog:
                self.prog['iMouse'].value = (0.0, 0.0, 0.0, 0.0)

            # Create framebuffer and texture for rendering
            self.texture = self.ctx.texture((width, height), 4)
            self.fbo = self.ctx.framebuffer(self.texture)

            # Create audio texture with optimized settings
            self.audio_texture = self.ctx.texture((512, 1), 4)
            self.audio_texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
            self.audio_texture.repeat_x = False
            self.audio_texture.repeat_y = False

            # Create previous audio texture for decay effect with optimized settings
            self.prev_audio_texture = self.ctx.texture((512, 1), 4)
            self.prev_audio_texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
            self.prev_audio_texture.repeat_x = False
            self.prev_audio_texture.repeat_y = False

            # Create background texture with optimized settings
            self.background_texture = self.ctx.texture((width, height), 4)
            self.background_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            self.background_texture.repeat_x = False
            self.background_texture.repeat_y = False

            # Create previous frame texture for persistence effect with optimized settings
            self.previous_frame_texture = self.ctx.texture((width, height), 4)
            self.previous_frame_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            self.previous_frame_texture.repeat_x = False
            self.previous_frame_texture.repeat_y = False

            # Initialize textures with black - use optimized data format
            empty_audio_data = np.zeros((512, 1, 4), dtype=np.uint8)
            empty_frame_data = np.zeros((height, width, 4), dtype=np.uint8)

            self.audio_texture.write(empty_audio_data.tobytes())
            self.prev_audio_texture.write(empty_audio_data.tobytes())
            self.background_texture.write(empty_frame_data.tobytes())
            self.previous_frame_texture.write(empty_frame_data.tobytes())

        except Exception as e:
            print(f"Error initializing GL renderer: {e}")
            import traceback
            traceback.print_exc()
            raise

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
        uniform sampler2D iChannel0;  // Current audio data
        uniform sampler2D iChannel1;  // Previous frame's audio data (for decay)
        uniform sampler2D iChannel2;  // Background image

        // Custom uniforms for Smooth Curves
        uniform float iLineThickness;
        uniform float iBloomSize;
        uniform float iBloomIntensity;
        uniform float iBloomFalloff;
        uniform bool iFillEnabled;
        uniform float iFillOpacity;
        uniform float iScale;
        uniform float iShift;
        uniform float iWidth;
        uniform float iAmp;
        uniform vec3 iColor1;
        uniform vec3 iColor2;
        uniform vec3 iColor3;

        // Reactivity uniforms
        uniform float iDecaySpeed;
        uniform float iAttackSpeed;
        uniform float iNoiseGate;

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

    def update_audio_texture(self, audio_data):
        """
        Update the audio texture with new audio data.

        Args:
            audio_data (numpy.ndarray): Audio data array (1D)
        """
        # Normalize audio data to 0-1 range
        normalized_data = np.clip((audio_data + 1.0) / 2.0, 0, 1)

        # Create a 2D texture with audio data
        # Format: R channel contains audio amplitude
        texture_data = np.zeros((1, 512, 4), dtype=np.uint8)

        # Fill the texture with audio data
        for i in range(min(512, len(normalized_data))):
            value = int(normalized_data[i] * 255)
            texture_data[0, i, 0] = value  # R channel
            texture_data[0, i, 1] = value  # G channel
            texture_data[0, i, 2] = value  # B channel
            texture_data[0, i, 3] = 255    # A channel

        # Update the texture
        self.audio_texture.write(texture_data.tobytes())

    def update_background_texture(self, background_image):
        """
        Update the background texture with a new image.

        Args:
            background_image (PIL.Image): Background image
        """
        if background_image is None:
            # Use black background if no image is provided
            texture_data = np.zeros((self.height, self.width, 4), dtype=np.uint8)
            self.background_texture.write(texture_data.tobytes())
            print("No background image provided, using black background")
            return

        # Convert PIL image to numpy array
        if background_image.mode != 'RGBA':
            background_image = background_image.convert('RGBA')
            print(f"Converted background image to RGBA mode")

        # Resize if needed
        if background_image.size != (self.width, self.height):
            print(f"Resizing background image from {background_image.size} to {(self.width, self.height)}")
            background_image = background_image.resize((self.width, self.height), Image.LANCZOS)

        # Convert to numpy array
        texture_data = np.array(background_image)
        print(f"Background texture data shape: {texture_data.shape}, dtype: {texture_data.dtype}")

        # Update the texture
        self.background_texture.write(texture_data.tobytes())
        print(f"Background texture updated with image: {background_image.size}, mode: {background_image.mode}")

    def render_frame(self, audio_data, background_image=None, metadata=None):
        """
        Render a frame with the current audio data.

        Args:
            audio_data (numpy.ndarray): Audio data for the current frame
            background_image (PIL.Image, optional): Background image to composite with
            metadata (dict, optional): Additional metadata (artist, title, etc.)

        Returns:
            PIL.Image: Rendered frame
        """
        try:
            # Calculate current time
            current_time = time.time() - self.start_time

            # Ensure audio_data is the right shape - optimize with numpy operations
            if len(audio_data) != 512:
                # Resize to exactly 512 elements
                if len(audio_data) < 512:
                    # Pad with zeros if too short
                    audio_data = np.pad(audio_data, (0, 512 - len(audio_data)), 'constant')
                else:
                    # Truncate if too long
                    audio_data = audio_data[:512]

            # Store current audio texture in previous audio texture before updating
            # Copy the current audio texture to the previous audio texture - optimize with direct texture copy
            current_audio_data = np.frombuffer(self.audio_texture.read(), dtype=np.uint8).reshape(1, 512, 4)
            self.prev_audio_texture.write(current_audio_data.tobytes())

            # Update audio texture (iChannel0)
            self.update_audio_texture(audio_data)

            # Update background texture (iChannel2)
            self.update_background_texture(background_image)

            # Set all uniforms in a more optimized way
            # Set time uniform
            if 'iTime' in self.prog:
                self.prog['iTime'].value = current_time

            # Set all custom uniforms at once
            uniforms = {
                'iLineThickness': self.line_thickness,
                'iBloomSize': self.bloom_size,
                'iBloomIntensity': self.bloom_intensity,
                'iBloomFalloff': self.bloom_falloff,
                'iFillEnabled': self.fill_enabled,
                'iFillOpacity': self.fill_opacity,
                'iScale': self.scale,
                'iShift': self.shift,
                'iWidth': self.width_param,
                'iAmp': self.amp,
                'iColor1': self.color1_normalized,
                'iColor2': self.color2_normalized,
                'iColor3': self.color3_normalized,
                'iDecaySpeed': self.decay_speed,
                'iAttackSpeed': self.attack_speed,
                'iNoiseGate': self.noise_gate
            }

            # Set all uniforms that exist in the shader
            for name, value in uniforms.items():
                if name in self.prog:
                    self.prog[name].value = value

            # Bind the framebuffer
            self.fbo.use()

            # Clear the framebuffer
            self.ctx.clear(0.0, 0.0, 0.0, 0.0)

            # Bind all textures at once
            self.audio_texture.use(0)
            self.prev_audio_texture.use(1)
            self.background_texture.use(2)

            # Set texture uniforms
            if 'iChannel0' in self.prog:
                self.prog['iChannel0'].value = 0
            if 'iChannel1' in self.prog:
                self.prog['iChannel1'].value = 1
            if 'iChannel2' in self.prog:
                self.prog['iChannel2'].value = 2

            # Render the quad
            self.vao.render(moderngl.TRIANGLES)

            # Read the pixels from the framebuffer
            pixels = self.fbo.read(components=4)

            # Convert to PIL image
            image = Image.frombytes('RGBA', (self.width, self.height), pixels).transpose(Image.FLIP_TOP_BOTTOM)

            # Add text if metadata is provided and show_text is enabled
            if metadata and self.config.get("show_text", True):
                # Create a transparent overlay for text
                text_overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
                draw = ImageDraw.Draw(text_overlay)

                # Get glow settings - we're using pure white for text regardless of text_color
                # This is to ensure maximum visibility of the text
                glow_color_setting = self.config.get("text_color", "#ffffff")
                # We don't need to parse the text color since we're using pure white

                glow_effect = self.config.get("glow_effect", "black")
                glow_blur_radius = self.config.get("glow_blur_radius", 3)
                glow_intensity = self.config.get("glow_intensity", 1.0)

                # Extract artist and title from metadata
                artist_name = metadata.get("artist_name", "Artist Name")
                track_title = metadata.get("track_title", "Track Title")

                # Calculate text positions (bottom of the screen)
                title_y = self.height - 60
                artist_y = self.height - 30

                # Draw text with glow effect
                if glow_effect != "none":
                    # Create a separate image for the glow
                    glow_overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
                    glow_draw = ImageDraw.Draw(glow_overlay)

                    # Determine glow color
                    if glow_effect == "black":
                        glow_color = (0, 0, 0, int(255 * glow_intensity))
                    elif glow_effect == "white":
                        glow_color = (255, 255, 255, int(255 * glow_intensity))
                    else:
                        # Try to parse as hex color
                        try:
                            if glow_effect.startswith("#"):
                                r = int(glow_effect[1:3], 16)
                                g = int(glow_effect[3:5], 16)
                                b = int(glow_effect[5:7], 16)
                                glow_color = (r, g, b, int(255 * glow_intensity))
                            else:
                                glow_color = (0, 0, 0, int(255 * glow_intensity))
                        except:
                            glow_color = (0, 0, 0, int(255 * glow_intensity))

                    # Draw text on glow overlay
                    glow_draw.text((self.width // 2, title_y), track_title, fill=glow_color, font=self.title_font, anchor="ms")
                    glow_draw.text((self.width // 2, artist_y), artist_name, fill=glow_color, font=self.artist_font, anchor="ms")

                    # Apply blur to glow overlay
                    glow_overlay = glow_overlay.filter(ImageFilter.GaussianBlur(radius=glow_blur_radius))

                    # Composite glow overlay onto text overlay first (glow goes behind text)
                    text_overlay = Image.alpha_composite(text_overlay, glow_overlay)

                # Create a separate layer for the actual text (on top of glow)
                text_foreground = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
                text_fg_draw = ImageDraw.Draw(text_foreground)

                # Draw the actual text with full opacity - white color for maximum visibility
                # Use pure white for better visibility regardless of the text_color setting
                text_fg_draw.text((self.width // 2, title_y), track_title, fill=(255, 255, 255, 255), font=self.title_font, anchor="ms")
                text_fg_draw.text((self.width // 2, artist_y), artist_name, fill=(255, 255, 255, 255), font=self.artist_font, anchor="ms")

                # Composite the text foreground on top of everything
                text_overlay = Image.alpha_composite(text_overlay, text_foreground)

                # Composite text overlay onto the main image
                image = Image.alpha_composite(image, text_overlay)

            return image

        except Exception as e:
            print(f"Error rendering frame: {e}")
            import traceback
            traceback.print_exc()

            # Return a black image as fallback
            return Image.new('RGBA', (self.width, self.height), (0, 0, 0, 255))

    def cleanup(self):
        """Clean up resources."""
        try:
            if hasattr(self, 'audio_texture'):
                self.audio_texture.release()
            if hasattr(self, 'prev_audio_texture'):
                self.prev_audio_texture.release()
            if hasattr(self, 'background_texture'):
                self.background_texture.release()
            if hasattr(self, 'previous_frame_texture'):
                self.previous_frame_texture.release()
            if hasattr(self, 'texture'):
                self.texture.release()
            if hasattr(self, 'fbo'):
                self.fbo.release()
            if hasattr(self, 'quad'):
                self.quad.release()
            if hasattr(self, 'prog'):
                self.prog.release()
            if hasattr(self, 'ctx'):
                self.ctx.release()
            print("GL resources cleaned up")
        except Exception as e:
            print(f"Error cleaning up GL resources: {e}")
