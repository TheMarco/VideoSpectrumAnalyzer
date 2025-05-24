"""
WebGL renderer for the Circular Audio Visualizer.
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import moderngl
import os
import tempfile
import subprocess
import logging

logger = logging.getLogger(__name__)

class CircularAudioWebGLRenderer:
    def __init__(self, width=1280, height=720):
        self.width = int(width)
        self.height = int(height)
        self.ctx = None
        self.program = None
        self.vao = None
        self.texture = None
        self.background_texture = None
        self.fbo = None

    def initialize_gl(self):
        """Initialize OpenGL context and shaders"""
        try:
            # Try different context creation methods for better compatibility
            try:
                self.ctx = moderngl.create_context(standalone=True)
            except Exception as e1:
                logger.warning(f"Failed to create standalone context: {e1}")
                try:
                    # Try with require=False for better compatibility
                    self.ctx = moderngl.create_context(standalone=True, require=False)
                except Exception as e2:
                    logger.warning(f"Failed to create context with require=False: {e2}")
                    # Try with backend specification
                    try:
                        import os
                        os.environ['PYOPENGL_PLATFORM'] = 'osmesa'
                        self.ctx = moderngl.create_context(standalone=True)
                    except Exception as e3:
                        logger.error(f"All context creation methods failed: {e1}, {e2}, {e3}")
                        raise Exception("Failed to create OpenGL context")

            # Vertex shader
            vertex_shader = """
            #version 330 core
            in vec2 position;
            out vec2 uv;

            void main() {
                gl_Position = vec4(position, 0.0, 1.0);
                uv = position * 0.5 + 0.5;
            }
            """

            # Fragment shader - optimized version
            fragment_shader = """
            #version 330 core

            uniform sampler2D iChannel0;  // Audio texture
            uniform sampler2D iChannel1;  // Background texture
            uniform vec3 iResolution;
            uniform float iTime;
            uniform float iSensitivity;
            uniform bool iUseLogScale;
            uniform float iSegmentSize;
            uniform float iBrightness;
            uniform float iBloomSize;
            uniform float iBloomIntensity;
            uniform float iBloomFalloff;
            uniform float iSegmentGap;
            uniform float iInnerRadius;
            uniform float iScale;
            uniform vec3 iBaseColor;
            uniform vec3 iHotColor;

            in vec2 uv;
            out vec4 fragColor;

            #define PI 3.14159265359
            #define TWO_PI 6.28318530718

            void main() {
                vec2 fragCoord = uv * iResolution.xy;
                vec2 uvCoord = (fragCoord - 0.5 * iResolution.xy) / min(iResolution.x, iResolution.y);

                // Apply overall scale to make the visualizer smaller
                uvCoord *= iScale;

                float dist = length(uvCoord);
                float angle = atan(uvCoord.y, uvCoord.x) + PI; // 0 to 2PI

                vec3 color = vec3(0.0);

                // Spectrum analyzer parameters
                float innerRadius = iInnerRadius;
                float segmentHeight = 0.02 * iSegmentSize;
                float segmentGap = (iSegmentGap > 0.0) ? 0.005 * iSegmentGap : 0.0;
                int numFreqBands = 64;
                int numSegments = 15;

                // Calculate which frequency band we're in
                float bandAngle = TWO_PI / float(numFreqBands);
                int bandIndex = int(angle / bandAngle);
                float bandCenter = float(bandIndex) * bandAngle + bandAngle * 0.5;

                // Get frequency data for this band
                float freq = float(bandIndex) / float(numFreqBands);
                float rawAmplitude = texture(iChannel0, vec2(freq, 0.0)).x;

                // Apply sensitivity
                float amplitude = rawAmplitude * iSensitivity;

                // Apply scaling mode
                if (iUseLogScale) {
                    amplitude = log(1.0 + amplitude * 9.0) / log(10.0);
                } else {
                    amplitude = amplitude;
                }

                amplitude = pow(amplitude, 0.7);
                amplitude = clamp(amplitude, 0.0, 1.0);

                // Check if we're within the angular bounds of this frequency band
                float angleFromCenter = abs(angle - bandCenter);
                if (angleFromCenter > PI) angleFromCenter = TWO_PI - angleFromCenter;

                float bandWidth = bandAngle * (0.85 + iSegmentSize * 0.1);

                if (angleFromCenter < bandWidth * 0.5) {
                    // OPTIMIZED: Calculate segment index directly instead of looping
                    float segmentIndex = (dist - innerRadius) / (segmentHeight + segmentGap);
                    int seg = int(segmentIndex);

                    // Check if we're in a valid segment range
                    if (seg >= 0 && seg < numSegments) {
                        float segmentStart = innerRadius + float(seg) * (segmentHeight + segmentGap);
                        float segmentEnd = segmentStart + segmentHeight;

                        // Check if we're in the segment (not in the gap)
                        if (dist >= segmentStart && dist <= segmentEnd) {
                            // Calculate how many segments should be lit based on amplitude
                            int litSegments = int(amplitude * float(numSegments));

                            // Check if this segment should be lit
                            if (seg < litSegments) {
                                float radialPos = (dist - segmentStart) / segmentHeight;
                                float angularPos = angleFromCenter / (bandWidth * 0.5);

                                // Simplified edge softness calculation
                                float edgeSoftness = 0.1;
                                float radialFade = smoothstep(edgeSoftness, 1.0 - edgeSoftness, radialPos) *
                                                 smoothstep(1.0 - edgeSoftness, edgeSoftness, radialPos);
                                float angularFade = smoothstep(edgeSoftness, 1.0 - edgeSoftness, angularPos) *
                                                   smoothstep(1.0 - edgeSoftness, edgeSoftness, angularPos);

                                float intensity = radialFade * angularFade;

                                float heightRatio = float(seg) / float(numSegments);
                                // Improved color mixing: use amplitude as primary factor, height as secondary
                                // Make the color transition more visible by using a more aggressive mixing
                                float colorMixFactor = clamp(amplitude * 1.2 + heightRatio * 0.5, 0.0, 1.0);
                                vec3 segmentColor = mix(iBaseColor, iHotColor, colorMixFactor);

                                float baseIntensity = iBrightness * (2.0 + amplitude * 3.0);
                                float segmentBoost = 1.0 + heightRatio * amplitude * 2.0;

                                color = segmentColor * intensity * baseIntensity * segmentBoost;
                            }
                        }
                    }
                }
            """

            # Continue with the rest of the fragment shader
            fragment_shader += """
                // OPTIMIZED BLOOM: Simple radial glow instead of expensive nested loops
                vec3 bloomColor = vec3(0.0);

                // Only calculate bloom if we have some base color and bloom is enabled
                if (length(color) > 0.0 && iBloomIntensity > 0.0) {
                    // Simple radial bloom based on distance from center
                    float centerDist = length(uvCoord);
                    float maxRadius = innerRadius + float(numSegments) * (segmentHeight + segmentGap);

                    // Create a soft glow around the entire visualizer
                    if (centerDist < maxRadius * 1.5) {
                        float bloomFactor = exp(-centerDist * iBloomFalloff / (0.1 * iBloomSize));
                        bloomColor = color * bloomFactor * iBloomIntensity * 0.3;
                    }
                }

                // Combine base color with bloom
                vec3 finalColor = color + bloomColor;

                // Sample background texture
                vec4 backgroundColor = texture(iChannel1, uv);

                // Composite visualizer over background
                vec3 result = backgroundColor.rgb + finalColor;

                fragColor = vec4(result, 1.0);
            }
            """

            # Create shader program
            self.program = self.ctx.program(
                vertex_shader=vertex_shader,
                fragment_shader=fragment_shader
            )

            # Create fullscreen quad
            vertices = np.array([
                -1.0, -1.0,
                 1.0, -1.0,
                -1.0,  1.0,
                 1.0,  1.0,
            ], dtype=np.float32)

            vbo = self.ctx.buffer(vertices.tobytes())
            self.vao = self.ctx.vertex_array(self.program, [(vbo, '2f', 'position')])

            # Create background texture
            self.create_background_texture()

            logger.info("WebGL context initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize WebGL context: {e}")
            return False

    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple (0-1 range)"""
        if isinstance(hex_color, str) and hex_color:
            hex_color = hex_color.lstrip('#')
            return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
        elif isinstance(hex_color, (list, tuple)) and len(hex_color) >= 3:
            # Already RGB values, normalize if needed
            if all(isinstance(x, (int, float)) and x <= 1.0 for x in hex_color[:3]):
                return tuple(hex_color[:3])  # Already normalized
            else:
                return tuple(x / 255.0 for x in hex_color[:3])  # Normalize from 0-255
        else:
            # Fallback to white if no valid color provided
            logger.warning(f"Invalid color value: {hex_color}, using white fallback")
            return (1.0, 1.0, 1.0)

    def create_background_texture(self):
        """Create a texture for background image (iChannel1)."""
        if self.ctx is None:
            return

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
        if self.background_texture is None:
            return

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

        # Convert to numpy array and update texture
        texture_data = np.array(background_image)
        self.background_texture.write(texture_data.tobytes())

    def create_audio_texture(self, frequency_data):
        """Create texture from frequency data"""
        if self.ctx is None:
            return None

        try:
            # Log the raw input data for debugging
            logger.debug(f"WebGL Renderer: Raw input type: {type(frequency_data)}")
            logger.debug(f"WebGL Renderer: Raw input shape: {getattr(frequency_data, 'shape', 'no shape')}")

            # Convert to numpy array if it isn't already
            if not isinstance(frequency_data, np.ndarray):
                frequency_data = np.array(frequency_data, dtype=np.float32)

            # Ensure it's 1D
            if len(frequency_data.shape) > 1:
                frequency_data = frequency_data.flatten()

            # The shader expects exactly 64 frequency bands
            target_bands = 64

            logger.debug(f"WebGL Renderer: After processing - shape: {frequency_data.shape}, dtype: {frequency_data.dtype}")

            # Force the data to be exactly 64 bands
            if len(frequency_data) != target_bands:
                logger.warning(f"WebGL Renderer: Resizing data from {len(frequency_data)} to {target_bands} bands")
                if len(frequency_data) > target_bands:
                    # Downsample by taking first 64 elements
                    frequency_data = frequency_data[:target_bands]
                else:
                    # Upsample by padding with zeros
                    padded_data = np.zeros(target_bands, dtype=np.float32)
                    padded_data[:len(frequency_data)] = frequency_data
                    frequency_data = padded_data

            # Ensure correct data type and range
            frequency_data = np.clip(frequency_data.astype(np.float32), 0.0, 1.0)

            logger.debug(f"WebGL Renderer: Final data shape: {frequency_data.shape}")
            logger.debug(f"WebGL Renderer: Data range - min: {frequency_data.min():.3f}, max: {frequency_data.max():.3f}")

            # Always recreate the texture to avoid any caching issues
            if self.texture is not None:
                try:
                    self.texture.release()
                    logger.debug("Released existing texture")
                except Exception as release_error:
                    logger.warning(f"Error releasing texture: {release_error}")
                self.texture = None

            # Create texture data in the same format as other visualizers (RGBA uint8)
            texture_width = target_bands
            texture_height = 1

            # Convert frequency data to uint8 RGBA format like other visualizers
            normalized_data = np.clip(frequency_data * 255, 0, 255).astype(np.uint8)

            # Create RGBA texture data (1 x 64 x 4)
            texture_data = np.zeros((texture_height, texture_width, 4), dtype=np.uint8)
            texture_data[0, :, 0] = normalized_data  # R channel
            texture_data[0, :, 1] = normalized_data  # G channel
            texture_data[0, :, 2] = normalized_data  # B channel
            texture_data[0, :, 3] = 255              # A channel (fully opaque)

            data_bytes = texture_data.tobytes()
            expected_bytes = texture_width * texture_height * 4  # 4 bytes per RGBA pixel

            logger.debug(f"WebGL Renderer: Creating RGBA texture {texture_width}x{texture_height}")
            logger.debug(f"WebGL Renderer: Data bytes length: {len(data_bytes)}")
            logger.debug(f"WebGL Renderer: Expected bytes: {expected_bytes}")

            # Create the texture with RGBA format like other visualizers
            self.texture = self.ctx.texture(
                size=(texture_width, texture_height),
                components=4,  # RGBA channels
                data=data_bytes
            )
            self.texture.filter = (moderngl.LINEAR, moderngl.LINEAR)

            logger.debug(f"WebGL Renderer: Successfully created texture: {self.texture.size}")
            return self.texture

        except Exception as e:
            logger.error(f"Error creating audio texture: {e}")
            logger.error(f"Exception type: {type(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    def render_frame(self, frequency_data, config, time_seconds=0.0, background_frame=None):
        """Render a single frame"""
        if self.ctx is None or self.program is None:
            logger.error("WebGL context not initialized")
            # Return a black image instead of None
            return Image.new('RGBA', (self.width, self.height), (0, 0, 0, 255))

        try:
            # Update background texture
            self.update_background_texture(background_frame)

            # Create audio texture
            audio_texture = self.create_audio_texture(frequency_data)
            if audio_texture is None:
                logger.error("Failed to create audio texture")
                # Return a black image instead of None
                return Image.new('RGBA', (self.width, self.height), (0, 0, 0, 255))

            # Set up framebuffer
            if self.fbo is None:
                self.fbo = self.ctx.framebuffer(
                    color_attachments=[self.ctx.texture((self.width, self.height), 4)]
                )
            self.fbo.use()

            # Clear
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            self.ctx.viewport = (0, 0, self.width, self.height)

            # Bind textures
            audio_texture.use(location=0)
            if self.background_texture is not None:
                self.background_texture.use(location=1)

            # Set texture uniforms
            if 'iChannel0' in self.program:
                self.program['iChannel0'] = 0
            if 'iChannel1' in self.program:
                self.program['iChannel1'] = 1

            # Set uniforms with error checking
            try:
                if 'iResolution' in self.program:
                    self.program['iResolution'] = (self.width, self.height, 1.0)
                if 'iTime' in self.program:
                    self.program['iTime'] = time_seconds
                if 'iSensitivity' in self.program:
                    self.program['iSensitivity'] = config.get('sensitivity', 1.4)
                if 'iUseLogScale' in self.program:
                    self.program['iUseLogScale'] = config.get('use_log_scale', False)
                if 'iSegmentSize' in self.program:
                    self.program['iSegmentSize'] = config.get('segment_size', 1.0)
                if 'iBrightness' in self.program:
                    self.program['iBrightness'] = config.get('brightness', 3.5)
                if 'iBloomSize' in self.program:
                    self.program['iBloomSize'] = config.get('bloom_size', 4.5)
                if 'iBloomIntensity' in self.program:
                    self.program['iBloomIntensity'] = config.get('bloom_intensity', 0.7)
                if 'iBloomFalloff' in self.program:
                    self.program['iBloomFalloff'] = config.get('bloom_falloff', 2.0)
                if 'iSegmentGap' in self.program:
                    self.program['iSegmentGap'] = config.get('segment_gap', 0.4)
                if 'iInnerRadius' in self.program:
                    self.program['iInnerRadius'] = config.get('inner_radius', 0.05)
                if 'iScale' in self.program:
                    self.program['iScale'] = config.get('scale', 1.5)
            except Exception as uniform_error:
                logger.error(f"Error setting uniforms: {uniform_error}")
                raise

            # Convert colors - use form values without hardcoded fallbacks
            base_color = self.hex_to_rgb(config.get('base_color'))
            hot_color = self.hex_to_rgb(config.get('hot_color'))

            try:
                if 'iBaseColor' in self.program:
                    self.program['iBaseColor'] = base_color
                if 'iHotColor' in self.program:
                    self.program['iHotColor'] = hot_color
            except Exception as color_error:
                logger.error(f"Error setting color uniforms: {color_error}")
                raise

            # Render
            self.vao.render(moderngl.TRIANGLE_STRIP)

            # Read pixels
            pixels = self.fbo.color_attachments[0].read()

            # Convert to PIL Image
            img_array = np.frombuffer(pixels, dtype=np.uint8).reshape((self.height, self.width, 4))
            img_array = np.flip(img_array, axis=0)  # Flip vertically
            img = Image.fromarray(img_array, 'RGBA')

            return img

        except Exception as e:
            logger.error(f"Error rendering frame: {e}")
            # Return a black image instead of None
            return Image.new('RGBA', (self.width, self.height), (0, 0, 0, 255))



    def cleanup(self):
        """Clean up OpenGL resources"""
        if self.texture:
            self.texture.release()
        if self.background_texture:
            self.background_texture.release()
        if self.fbo:
            self.fbo.release()
        if self.vao:
            self.vao.release()
        if self.program:
            self.program.release()
        if self.ctx:
            self.ctx.release()
