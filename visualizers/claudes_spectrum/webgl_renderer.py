"""
GL renderer for Claude's Spectrum Visualizer.
"""

import numpy as np
from PIL import Image
import os
import logging

try:
    import moderngl
    MODERNGL_AVAILABLE = True
except ImportError:
    MODERNGL_AVAILABLE = False
    moderngl = None

logger = logging.getLogger(__name__)
# Enable debug logging for this module
logger.setLevel(logging.DEBUG)

class ClaudesSpectrumGLRenderer:
    def __init__(self, width=1280, height=720):
        self.width = int(width)
        self.height = int(height)
        self.ctx = None
        self.program = None
        self.vao = None
        self.texture = None
        self.background_texture = None
        self.fbo = None

    def initialize_gl(self, config=None):
        """Initialize the GL context and resources."""
        try:
            logger.info("Starting GL renderer initialization...")
            if not MODERNGL_AVAILABLE:
                logger.error("ModernGL is not available")
                return False

            # Create a standalone context
            try:
                logger.info("Attempting to create standalone ModernGL context...")
                self.ctx = moderngl.create_context(standalone=True)
                logger.info("Successfully created standalone ModernGL context")
            except Exception as ctx_error:
                logger.error(f"Failed to create standalone moderngl context: {ctx_error}")
                try:
                    logger.info("Attempting to create default ModernGL context...")
                    # Try without standalone parameter
                    self.ctx = moderngl.create_context()
                    logger.info("Successfully created default ModernGL context")
                except Exception as ctx_error2:
                    logger.error(f"Failed to create any moderngl context: {ctx_error2}")
                    logger.error("ModernGL context creation failed completely - falling back to PIL renderer")
                    return False

            # Load the shader and modify it for ModernGL
            logger.info("Loading shader file...")
            shader_path = os.path.join(os.path.dirname(__file__), '..', '..', 'glsl', 'ar_claudespectrum.glsl')
            if not os.path.exists(shader_path):
                logger.error(f"Shader file not found: {shader_path}")
                return False

            with open(shader_path, 'r') as f:
                shader_content = f.read()
            logger.info("Shader file loaded successfully")

            # Convert Shadertoy shader to ModernGL format
            logger.info("Converting Shadertoy shader to ModernGL format...")
            fragment_shader = self._convert_shadertoy_shader(shader_content, config)
            logger.info("Shader conversion completed")

            # Vertex shader for a fullscreen quad
            vertex_shader = """
            #version 330 core
            in vec2 in_position;
            void main() {
                gl_Position = vec4(in_position, 0.0, 1.0);
            }
            """

            # Create shader program
            logger.info("Creating shader program...")
            try:
                self.program = self.ctx.program(
                    vertex_shader=vertex_shader,
                    fragment_shader=fragment_shader
                )
                logger.info("Shader program created successfully")
            except Exception as shader_error:
                logger.error(f"Shader compilation failed: {shader_error}")
                return False

            # Create a fullscreen quad
            logger.info("Creating fullscreen quad...")
            vertices = np.array([
                -1.0, -1.0,
                 1.0, -1.0,
                -1.0,  1.0,
                 1.0,  1.0,
            ], dtype=np.float32)

            vbo = self.ctx.buffer(vertices.tobytes())
            self.vao = self.ctx.vertex_array(self.program, [(vbo, '2f', 'in_position')])
            logger.info("Fullscreen quad created successfully")

            # Create texture for audio data (use uint8 format like other visualizers)
            logger.info("Creating audio texture...")
            # Use 4-component RGBA uint8 format like other GL visualizers
            initial_data = np.zeros((1, 256, 4), dtype=np.uint8)
            self.texture = self.ctx.texture((256, 1), 4, data=initial_data.tobytes())
            self.texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            logger.info(f"Audio texture created successfully - size: {self.texture.size}, components: {self.texture.components}")
            logger.info(f"Expected data size: {256 * 1 * 4} bytes")

            # Create background texture for background shaders (iChannel1)
            logger.info("Creating background texture...")
            self.background_texture = self.ctx.texture((self.width, self.height), 4)
            self.background_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            self.background_texture.repeat_x = False
            self.background_texture.repeat_y = False
            # Initialize with black transparent texture
            self.background_texture.write(np.zeros((self.height, self.width, 4), dtype=np.uint8))
            logger.info("Background texture created successfully")

            # Create framebuffer for rendering
            logger.info("Creating framebuffer...")
            color_attachment = self.ctx.texture((self.width, self.height), 4)
            self.fbo = self.ctx.framebuffer(color_attachment)
            logger.info("Framebuffer created successfully")

            logger.info("GL renderer initialization completed successfully!")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize GL renderer: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return False

    def update_background_texture(self, background_frame):
        """Update the background texture with a new frame (for background shaders)."""
        if self.background_texture is None or background_frame is None:
            return

        # Ensure background frame is RGBA
        if background_frame.mode != 'RGBA':
            background_frame = background_frame.convert('RGBA')

        # Resize to match renderer size
        if background_frame.size != (self.width, self.height):
            background_frame = background_frame.resize((self.width, self.height), Image.LANCZOS)

        # Convert to numpy array and flip vertically to account for OpenGL coordinate system
        # OpenGL has origin at bottom-left, PIL has origin at top-left
        background_frame_flipped = background_frame.transpose(Image.FLIP_TOP_BOTTOM)
        texture_data = np.array(background_frame_flipped)
        self.background_texture.write(texture_data.tobytes())

    def render_frame(self, frequency_data, config, time_seconds, background_image=None):
        """Render a single frame using the GL shader."""
        try:
            logger.debug(f"GL render_frame called with frequency_data shape: {frequency_data.shape if hasattr(frequency_data, 'shape') else len(frequency_data)}")

            if not self.ctx:
                logger.error("GL context is None")
                return None
            if not self.program:
                logger.error("GL program is None")
                return None
            if not self.texture:
                logger.error("GL texture is None")
                return None
            if not self.fbo:
                logger.error("GL framebuffer is None")
                return None
            if not self.vao:
                logger.error("GL vertex array is None")
                return None

            # Prepare audio texture data (use uint8 format like other visualizers)
            audio_data_1d = np.zeros(256, dtype=np.float32)
            if len(frequency_data) > 0:
                # Resample frequency data to 256 samples
                indices = np.linspace(0, len(frequency_data) - 1, 256)
                audio_data_1d = np.interp(indices, np.arange(len(frequency_data)), frequency_data)

                # Apply sensitivity scaling
                sensitivity = config.get('sensitivity', 1.0)
                audio_data_1d = audio_data_1d * sensitivity

                # Clamp values
                audio_data_1d = np.clip(audio_data_1d, 0.0, 1.0)

            # Convert to uint8 format like other GL visualizers
            normalized_data = np.clip(audio_data_1d * 255, 0, 255).astype(np.uint8)

            # Create RGBA texture data (1 x 256 x 4)
            texture_data = np.zeros((1, 256, 4), dtype=np.uint8)
            texture_data[0, :, 0] = normalized_data  # R channel
            texture_data[0, :, 1] = normalized_data  # G channel
            texture_data[0, :, 2] = normalized_data  # B channel
            texture_data[0, :, 3] = 255              # A channel (fully opaque)

            # Update background texture if background image provided
            if background_image:
                self.update_background_texture(background_image)

            # Update audio texture (256 pixels × 4 components × 1 byte = 1024 bytes)
            data_bytes = texture_data.tobytes()
            logger.debug(f"Writing {len(data_bytes)} bytes to texture (size: {self.texture.size}, components: {self.texture.components})")
            self.texture.write(data_bytes)

            # Set up rendering
            self.fbo.use()
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            self.ctx.viewport = (0, 0, self.width, self.height)

            # Bind textures and uniforms
            self.texture.use(0)  # Audio data on iChannel0
            if self.background_texture:
                self.background_texture.use(1)  # Background on iChannel1

            # Set shader uniforms
            if 'iResolution' in self.program:
                self.program['iResolution'].value = (float(self.width), float(self.height))
            if 'iTime' in self.program:
                self.program['iTime'].value = float(time_seconds)
            if 'iChannel0' in self.program:
                self.program['iChannel0'].value = 0
            if 'iChannel1' in self.program:
                self.program['iChannel1'].value = 1

            # Update shader defines based on config
            # Note: Since we can't modify #defines at runtime, we'll need to handle
            # configuration through uniforms in a future version

            # Render the quad
            self.vao.render(moderngl.TRIANGLE_STRIP)

            # Read the result
            data = self.fbo.color_attachments[0].read()
            image = Image.frombytes('RGBA', (self.width, self.height), data)

            # Flip vertically (OpenGL has origin at bottom-left)
            image = image.transpose(Image.FLIP_TOP_BOTTOM)

            return image

        except Exception as e:
            logger.error(f"Error rendering frame: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return None

    def cleanup(self):
        """Clean up GL resources."""
        try:
            if self.fbo:
                self.fbo.release()
            if self.texture:
                self.texture.release()
            if self.vao:
                self.vao.release()
            if self.program:
                self.program.release()
            if self.ctx:
                self.ctx.release()
            logger.info("GL renderer cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def _convert_shadertoy_shader(self, shader_content, config=None):
        """Convert Shadertoy shader format to ModernGL format."""
        # Update shader defines based on config
        if config:
            logger.debug(f"Config received: {config}")
            # Number of bars
            num_bars = config.get('num_bars', 48)
            shader_content = shader_content.replace(
                '#define NUM_BARS 48',
                f'#define NUM_BARS {num_bars}'
            )

            # Color scheme
            color_scheme = config.get('color_scheme', 0)
            shader_content = shader_content.replace(
                '#define COLOR_SCHEME 0',
                f'#define COLOR_SCHEME {color_scheme}'
            )

            # Single color (convert hex to vec3)
            single_color = config.get('single_color', '#ffffff')
            r, g, b = self._hex_to_rgb(single_color)
            shader_content = shader_content.replace(
                '#define SINGLE_COLOR vec3(1.0, 1.0, 1.0)',
                f'#define SINGLE_COLOR vec3({r:.3f}, {g:.3f}, {b:.3f})'
            )

            # Gradient colors
            color_low = config.get('color_low', '#ff3319')
            r, g, b = self._hex_to_rgb(color_low)
            shader_content = shader_content.replace(
                '#define COLOR_LOW vec3(1.0, 0.2, 0.1)',
                f'#define COLOR_LOW vec3({r:.3f}, {g:.3f}, {b:.3f})'
            )

            color_mid = config.get('color_mid', '#ffff33')
            r, g, b = self._hex_to_rgb(color_mid)
            shader_content = shader_content.replace(
                '#define COLOR_MID vec3(1.0, 1.0, 0.2)',
                f'#define COLOR_MID vec3({r:.3f}, {g:.3f}, {b:.3f})'
            )

            color_high = config.get('color_high', '#3366ff')
            r, g, b = self._hex_to_rgb(color_high)
            shader_content = shader_content.replace(
                '#define COLOR_HIGH vec3(0.2, 0.4, 1.0)',
                f'#define COLOR_HIGH vec3({r:.3f}, {g:.3f}, {b:.3f})'
            )

            # Center line color
            center_line_color = config.get('center_line_color', '#999999')
            r, g, b = self._hex_to_rgb(center_line_color)
            shader_content = shader_content.replace(
                '#define CENTER_LINE_COLOR vec3(0.6, 0.6, 0.6)',
                f'#define CENTER_LINE_COLOR vec3({r:.3f}, {g:.3f}, {b:.3f})'
            )

            # Logarithmic scale settings
            use_log_scale = 1 if config.get('use_logarithmic_scale', True) else 0
            shader_content = shader_content.replace(
                '#define USE_LOGARITHMIC_SCALE 1',
                f'#define USE_LOGARITHMIC_SCALE {use_log_scale}'
            )

            log_scale_factor = config.get('log_scale_factor', 0.5)
            shader_content = shader_content.replace(
                '#define LOG_SCALE_FACTOR 0.5',
                f'#define LOG_SCALE_FACTOR {log_scale_factor:.2f}'
            )

            # Maximum bar height setting
            max_bar_height = config.get('max_bar_height', 0.7)
            shader_content = shader_content.replace(
                '#define MAX_BAR_HEIGHT 0.7',
                f'#define MAX_BAR_HEIGHT {max_bar_height:.2f}'
            )
            logger.info(f"Max bar height: {max_bar_height:.2f}")

            # Waveform width setting
            waveform_width = config.get('waveform_width', 0.8)
            shader_content = shader_content.replace(
                '#define WAVEFORM_WIDTH 0.8',
                f'#define WAVEFORM_WIDTH {waveform_width:.2f}'
            )
            logger.info(f"Waveform width: {waveform_width:.2f}")

            # Center line settings - convert pixels to normalized coordinates
            center_line_thickness_pixels = config.get('center_line_thickness', 4)  # Default 4px
            # Convert to normalized coordinates based on 720px reference height
            center_line_thickness_normalized = center_line_thickness_pixels / 720.0
            shader_content = shader_content.replace(
                '#define CENTER_LINE_THICKNESS 0.006',
                f'#define CENTER_LINE_THICKNESS {center_line_thickness_normalized:.6f}'
            )
            logger.info(f"Center line thickness: {center_line_thickness_pixels}px -> {center_line_thickness_normalized:.6f}")

            center_line_overhang = config.get('center_line_overhang', 0.05)
            shader_content = shader_content.replace(
                '#define CENTER_LINE_OVERHANG 0.05',
                f'#define CENTER_LINE_OVERHANG {center_line_overhang:.2f}'
            )
            logger.info(f"Center line overhang: {center_line_overhang:.2f}")

            # Get pixel values directly from config - no more confusing conversions!
            bar_width_pixels = config.get('bar_width', 10)  # Default 10px
            bar_spacing_pixels = config.get('bar_spacing', 18)  # Default 18px

            logger.info(f"Bar width: {bar_width_pixels}px")
            logger.info(f"Bar spacing: {bar_spacing_pixels}px")

            # Convert to normalized coordinates for shader (0.0 to 1.0 range)
            # Based on 1280px reference width
            actual_width = bar_width_pixels / 1280.0
            actual_spacing = bar_spacing_pixels / 1280.0

            # Ensure reasonable minimum values
            actual_width = max(0.002, actual_width)  # At least ~2.5px
            actual_spacing = max(0.003, actual_spacing)  # At least ~4px

            logger.info(f"Normalized width: {actual_width:.6f}")
            logger.info(f"Normalized spacing: {actual_spacing:.6f}")

            # Check if the replacements are working
            old_width_define = '#define BAR_WIDTH 0.008'
            new_width_define = f'#define BAR_WIDTH {actual_width:.6f}'
            old_spacing_define = '#define BAR_SPACING 0.014'
            new_spacing_define = f'#define BAR_SPACING {actual_spacing:.6f}'

            logger.info(f"Replacing '{old_width_define}' with '{new_width_define}'")
            logger.info(f"Replacing '{old_spacing_define}' with '{new_spacing_define}'")

            shader_content = shader_content.replace(old_width_define, new_width_define)
            shader_content = shader_content.replace(old_spacing_define, new_spacing_define)

            # Verify the replacements worked
            if new_width_define in shader_content:
                logger.info("✅ BAR_WIDTH replacement successful")
            else:
                logger.error("❌ BAR_WIDTH replacement failed")

            if new_spacing_define in shader_content:
                logger.info("✅ BAR_SPACING replacement successful")
            else:
                logger.error("❌ BAR_SPACING replacement failed")

            # Bloom settings
            bloom_size = config.get('bloom_size', 8.0)
            bloom_intensity = config.get('bloom_intensity', 0.3)
            bloom_falloff = config.get('bloom_falloff', 2.0)

            shader_content = shader_content.replace(
                '#define BLOOM_SIZE 8.0',
                f'#define BLOOM_SIZE {bloom_size:.1f}'
            )

            shader_content = shader_content.replace(
                '#define BLOOM_INTENSITY 0.3',
                f'#define BLOOM_INTENSITY {bloom_intensity:.2f}'
            )

            shader_content = shader_content.replace(
                '#define BLOOM_FALLOFF 2.0',
                f'#define BLOOM_FALLOFF {bloom_falloff:.1f}'
            )

        # Add proper GLSL version and uniforms
        header = """#version 330 core

uniform vec2 iResolution;
uniform float iTime;
uniform sampler2D iChannel0;
uniform sampler2D iChannel1;

out vec4 fragColor;

"""

        # Replace mainImage with main and add gl_FragCoord
        shader_content = shader_content.replace(
            'void mainImage(out vec4 fragColor, in vec2 fragCoord)',
            'void main()'
        )

        # Add fragCoord definition at the start of main
        shader_content = shader_content.replace(
            'void main() {',
            'void main() {\n    vec2 fragCoord = gl_FragCoord.xy;'
        )

        return header + shader_content

    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB values (0.0-1.0)."""
        # Remove # if present
        hex_color = hex_color.lstrip('#')
        # Convert to RGB
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0
        return r, g, b
