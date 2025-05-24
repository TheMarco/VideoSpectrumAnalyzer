"""
GL-based renderer for the Smooth Curves visualizer.
This implementation uses direct GL rendering for better performance.
"""

import os
import time
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import moderngl
from modules.media_handler import load_fonts

class SmoothCurvesGLRenderer:
    """
    GL renderer for the Smooth Curves visualizer.
    This implementation uses direct GL rendering for better performance.
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
        print(f"SmoothCurvesGLRenderer.__init__(width={width}, height={height}, config={config})")

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
            self.fill_opacity = float(config.get("fill_opacity", 0.5))
            self.scale = float(config.get("scale", 0.2))
            self.shift = float(config.get("shift", 0.08))
            # Use width_param to avoid confusion with the frame width
            self.width_param = float(config.get("width", 0.04))
            self.amp = float(config.get("amp", 1.0))

            # Reactivity parameters
            self.decay_speed = float(config.get("decay_speed", 0.2))
            self.attack_speed = float(config.get("attack_speed", 1.0))
            self.noise_gate = float(config.get("noise_gate", 0.03))
        except ValueError as e:
            print(f"Error converting config values to float: {e}")
            # Use default values if conversion fails
            self.line_thickness = 3.0
            self.bloom_size = 20.0
            self.bloom_intensity = 0.5
            self.bloom_falloff = 1.5
            self.fill_enabled = True
            self.fill_opacity = 0.5
            self.scale = 0.2
            self.shift = 0.08
            self.width_param = 0.04
            self.amp = 1.0
            self.decay_speed = 0.2
            self.attack_speed = 1.0
            self.noise_gate = 0.03

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
        print(f"Initializing Smooth Curves GL Renderer with width={self.width}, height={self.height}, width_param={self.width_param}")

        try:
            # Create standalone ModernGL context with performance optimizations
            self.ctx = moderngl.create_standalone_context(require=330)
            # Enable performance optimizations
            self.ctx.enable(moderngl.BLEND)
            self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
            print("ModernGL standalone context created successfully with performance optimizations")

            # Load shader
            self.vertex_shader, self.fragment_shader = self._load_shaders()
            print("Shaders loaded successfully")

            # Create shader program
            self.prog = self._build_shader_program()
            print("Shader program built successfully")

            # Create vertex buffer and VAO for a full-screen quad
            # Use a simpler quad definition for better compatibility
            vertices = np.array([
                # positions (x, y)
                -1.0, -1.0,  # bottom left
                 1.0, -1.0,  # bottom right
                -1.0,  1.0,  # top left
                 1.0,  1.0,  # top right
            ], dtype='f4')

            self.quad = self.ctx.buffer(vertices.tobytes())
            self.vao = self.ctx.vertex_array(
                self.prog,
                [(self.quad, '2f', 'a_position')]
            )

            # Set uniforms - ensure width and height are floats
            self.prog['iResolution'].value = (float(width), float(height))

            # Create framebuffer and texture for rendering
            self.texture = self.ctx.texture((width, height), 4)
            self.fbo = self.ctx.framebuffer(self.texture)

            # Create audio texture with optimized settings
            self.audio_texture = self.ctx.texture((128, 1), 4)
            self.audio_texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
            self.audio_texture.repeat_x = False
            self.audio_texture.repeat_y = False

            # Create background texture with optimized settings
            self.background_texture = self.ctx.texture((width, height), 4)
            self.background_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            self.background_texture.repeat_x = False
            self.background_texture.repeat_y = False

            # Initialize textures with black - use optimized data format
            empty_audio_data = np.zeros((128, 1, 4), dtype=np.uint8)
            empty_frame_data = np.zeros((height, width, 4), dtype=np.uint8)

            self.audio_texture.write(empty_audio_data.tobytes())
            self.background_texture.write(empty_frame_data.tobytes())

        except Exception as e:
            print(f"Error initializing GL renderer: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _load_shaders(self):
        """
        Load vertex and fragment shaders.

        Returns:
            tuple: (vertex_shader_source, fragment_shader_source)
        """
        # Vertex shader - simple pass-through with standard texture coordinates
        vertex_shader = """
            #version 330

            in vec2 a_position;
            out vec2 v_texcoord;

            void main() {
                // Map from [-1,1] to [0,1] range for texture coordinates
                v_texcoord = vec2(a_position.x * 0.5 + 0.5, a_position.y * 0.5 + 0.5);
                gl_Position = vec4(a_position, 0.0, 1.0);
            }
        """

        # Fragment shader - based on the GL implementation
        fragment_shader = """
            #version 330

            in vec2 v_texcoord;
            out vec4 f_color;

            uniform vec2 iResolution;
            uniform sampler2D iChannel0;  // Audio data
            uniform sampler2D iChannel1;  // Background image

            // Time uniform - may not be used but declared for compatibility
            // uniform float iTime;

            // CONFIGURABLE SETTINGS
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

            // Get frequency for given channel and index - exact Shadertoy implementation
            float getFreq(int channel, int i) {
                int band;
                // Shuffle array: [1, 3, 0, 4, 2]
                if (i == 0) band = 2 * channel + 1 * 6;
                else if (i == 1) band = 2 * channel + 3 * 6;
                else if (i == 2) band = 2 * channel + 0 * 6;
                else if (i == 3) band = 2 * channel + 4 * 6;
                else band = 2 * channel + 2 * 6;

                float normalizedBand = float(band) / 32.0;
                return texture(iChannel0, vec2(normalizedBand, 0.0)).x;
            }

            // Scale factor for the given value index - exact Shadertoy implementation
            float getScale(int i) {
                float x = abs(2.0 - float(i)); // 2,1,0,1,2
                float s = 3.0 - x;             // 1,2,3,2,1
                return s / 3.0 * iAmp;
            }

            // Smooth cubic interpolation for curves
            float smoothCubic(float t) {
                return t * t * (3.0 - 2.0 * t);
            }

            // Inversion factor - curves bulge outward at ends, inward in middle
            float getInversionFactor(int index) {
                if (index == 0 || index == 4) {
                    return -1.0;
                } else {
                    return 1.0;
                }
            }

            // Sample curve at parameter t with smooth transitions and inverted ends - exact Shadertoy implementation
            float sampleCurveY(float t, float y[5], bool upper) {
                t = clamp(t, 0.0, 1.0);

                // Extended curve for smooth transitions at ends
                float extendedT = t * 1.4 - 0.2; // Map to -0.2 to 1.2 for smooth ends

                if (extendedT <= 0.0) {
                    // Smooth transition from baseline to first peak (INVERTED)
                    float blend = smoothCubic((extendedT + 0.2) / 0.2);
                    float displacement = (y[0] - 0.5) * getInversionFactor(0);
                    float result = 0.5 + displacement * blend;
                    return upper ? result : (1.0 - result);
                } else if (extendedT >= 1.0) {
                    // Smooth transition from last peak to baseline (INVERTED)
                    float blend = smoothCubic(1.0 - (extendedT - 1.0) / 0.2);
                    float displacement = (y[4] - 0.5) * getInversionFactor(4);
                    float result = 0.5 + displacement * blend;
                    return upper ? result : (1.0 - result);
                }

                // Map to the 5 frequency peaks with smooth interpolation
                float scaledT = extendedT * 4.0; // 0 to 4
                int index = int(scaledT);
                float frac = fract(scaledT);

                // Smooth cubic interpolation between peaks
                frac = smoothCubic(frac);

                float y1, y2;
                float inv1, inv2;

                if (index >= 4) {
                    y1 = y2 = y[4];
                    inv1 = inv2 = getInversionFactor(4);
                } else {
                    y1 = y[index];
                    y2 = y[min(index + 1, 4)];
                    inv1 = getInversionFactor(index);
                    inv2 = getInversionFactor(min(index + 1, 4));
                }

                // Apply inversion to displacements
                float disp1 = (y1 - 0.5) * inv1;
                float disp2 = (y2 - 0.5) * inv2;

                float displacement = mix(disp1, disp2, frac);
                float result = 0.5 + displacement;

                if (!upper) {
                    result = 1.0 - result; // Mirror for lower curve
                }

                return result;
            }
        """

        # Continue with the fragment shader
        fragment_shader_part2 = """
            // Get fill intensity for a point (0.0 = outside, 1.0 = inside) - exact Shadertoy implementation
            float getFillIntensity(vec2 uv, int channel) {
                float m = 0.5; // middle of canvas

                // Calculate shape bounds
                float totalWidth = 15.0 * iWidth;
                float offset = (1.0 - totalWidth) / 2.0;
                float channelShift = float(channel) * iShift;

                // Shape bounds
                float startX = offset + channelShift;
                float endX = offset + channelShift + totalWidth;

                // Check horizontal bounds with smooth falloff
                if (uv.x < startX || uv.x > endX) {
                    return 0.0;
                }

                // Calculate y values based on frequencies
                float y[5];
                for (int i = 0; i < 5; i++) {
                    float freq = getFreq(channel, i);
                    float scaleFactor = getScale(i);
                    y[i] = max(0.0, m - scaleFactor * iScale * freq);
                }

                // Map UV x to curve parameter t
                float t = (uv.x - startX) / (endX - startX);

                // Sample upper and lower curves
                float upperY = sampleCurveY(t, y, true);
                float lowerY = sampleCurveY(t, y, false);

                float minY = min(upperY, lowerY);
                float maxY = max(upperY, lowerY);

                if (uv.y >= minY && uv.y <= maxY) {
                    return 1.0;
                }

                return 0.0;
            }

            // Get the outline distance for one channel with smooth curves
            float getOutlineDistance(vec2 uv, int channel) {
                float m = 0.5;

                float totalWidth = 15.0 * iWidth;
                float offset = (1.0 - totalWidth) / 2.0;
                float channelShift = float(channel) * iShift;

                float startX = offset + channelShift;
                float endX = offset + channelShift + totalWidth;



                // Calculate y values based on frequencies
                float y[5];
                for (int i = 0; i < 5; i++) {
                    float freq = getFreq(channel, i);
                    float scaleFactor = getScale(i);
                    y[i] = max(0.0, m - scaleFactor * iScale * freq);
                }

                float minDist = 1000.0;

                // Check if we're in the curve area
                if (uv.x >= startX && uv.x <= endX) {
                    // Map UV x to curve parameter t
                    float t = (uv.x - startX) / (endX - startX);

                    // Sample upper and lower curves with smooth transitions and inverted ends
                    float upperY = sampleCurveY(t, y, true);
                    float lowerY = sampleCurveY(t, y, false);

                    minDist = min(minDist, abs(uv.y - upperY));
                    minDist = min(minDist, abs(uv.y - lowerY));
                } else {
                    // Distance to baseline outside curve area
                    minDist = abs(uv.y - m);
                }

                return minDist;
            }

            void main() {
                // Use the texture coordinates from vertex shader instead of gl_FragCoord
                vec2 uv = v_texcoord;

                // Sample background texture if available
                vec4 backgroundColor = texture(iChannel1, uv);

                // Start with background color or black if no background
                vec3 finalColor = backgroundColor.a > 0.0 ? backgroundColor.rgb : vec3(0.0);

                vec2 pixelSize = 1.0 / iResolution.xy;
                float lineThickness = iLineThickness * length(pixelSize);
                float glowSize = iBloomSize * length(pixelSize);

                for (int channel = 0; channel < 3; channel++) {
                    vec3 channelColor;
                    if (channel == 0) channelColor = iColor1;
                    else if (channel == 1) channelColor = iColor2;
                    else channelColor = iColor3;

                    // Get distance to the outline
                    float dist = getOutlineDistance(uv, channel);

                    // Add fill if enabled - exact Shadertoy implementation
                    if (iFillEnabled) {
                        float fillIntensity = getFillIntensity(uv, channel);
                        if (fillIntensity > 0.0) {
                            vec3 fillColor = channelColor * iFillOpacity * fillIntensity;
                            finalColor += fillColor;
                        }
                    }

                    // Create smooth thin line stroke with CONFIGURABLE thickness - exact Shadertoy implementation
                    float stroke = 1.0 - smoothstep(0.0, lineThickness, dist);

                    // ENHANCED BLOOM/GLOW with multiple layers - exact Shadertoy implementation
                    // Primary glow - ensure smooth falloff
                    float glow1 = exp(-dist * iBloomFalloff / glowSize) * iBloomIntensity;

                    // Secondary wider glow for more dramatic effect - ensure smooth falloff
                    float glow2 = exp(-dist * (iBloomFalloff * 0.5) / (glowSize * 2.0)) * (iBloomIntensity * 0.5);

                    // Combine glows
                    float totalGlow = glow1 + glow2;

                    // Combine stroke and glow
                    float intensity = stroke + totalGlow;

                    // Screen blend mode approximation - exact Shadertoy implementation
                    vec3 layerColor = channelColor * intensity;
                    finalColor = finalColor + layerColor - finalColor * layerColor;
                }

                // Preserve alpha from background or use 1.0 if no background
                float alpha = backgroundColor.a > 0.0 ? backgroundColor.a : 1.0;
                f_color = vec4(finalColor, alpha);
            }
        """

        # Combine the fragment shader parts
        full_fragment_shader = fragment_shader + fragment_shader_part2

        return vertex_shader, full_fragment_shader

    def _build_shader_program(self):
        """
        Build the shader program from the vertex and fragment shaders.

        Returns:
            moderngl.Program: Compiled shader program
        """
        vertex_shader, fragment_shader = self._load_shaders()

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
            audio_data (numpy.ndarray): Audio data for the current frame
        """
        # Normalize audio data to 0-255 range for texture
        normalized_data = np.clip(audio_data * 255, 0, 255).astype(np.uint8)

        # Create a luminance texture (single channel)
        texture_data = np.zeros((1, len(normalized_data), 4), dtype=np.uint8)
        texture_data[0, :, 0] = normalized_data  # R channel
        texture_data[0, :, 1] = normalized_data  # G channel
        texture_data[0, :, 2] = normalized_data  # B channel
        texture_data[0, :, 3] = 255              # A channel (fully opaque)

        # Update the texture
        self.audio_texture.write(texture_data.tobytes())

    def update_background_texture(self, background_image):
        """
        Update the background texture with a new image.

        Args:
            background_image (PIL.Image, optional): Background image
        """
        if background_image is None:
            # Use a transparent black texture if no background
            texture_data = np.zeros((self.height, self.width, 4), dtype=np.uint8)
            self.background_texture.write(texture_data.tobytes())
            return

        # Resize the image to match the texture dimensions if needed
        if background_image.size != (self.width, self.height):
            background_image = background_image.resize((self.width, self.height), Image.LANCZOS)

        # Convert to RGBA if not already
        if background_image.mode != 'RGBA':
            background_image = background_image.convert('RGBA')

        # Convert to numpy array
        texture_data = np.array(background_image)

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

            # Ensure audio_data is the right shape
            if len(audio_data) != 128:
                # Resize to exactly 128 elements for GL version
                if len(audio_data) < 128:
                    # Pad with zeros if too short
                    audio_data = np.pad(audio_data, (0, 128 - len(audio_data)), 'constant')
                else:
                    # Resample if too long
                    indices = np.linspace(0, len(audio_data) - 1, 128).astype(int)
                    audio_data = audio_data[indices]

            # Update audio texture
            self.update_audio_texture(audio_data)

            # Update background texture
            self.update_background_texture(background_image)

            # Set resolution uniform (no time uniform needed)
            self.prog['iResolution'].value = (float(self.width), float(self.height))

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
                'iColor3': self.color3_normalized
            }

            # Set all uniforms that exist in the shader
            for name, value in uniforms.items():
                if name in self.prog:
                    self.prog[name].value = value

            # Bind the framebuffer
            self.fbo.use()

            # Clear the framebuffer
            self.ctx.clear(0.0, 0.0, 0.0, 0.0)

            # Bind textures
            self.audio_texture.use(0)
            self.background_texture.use(1)

            # Set texture uniforms
            self.prog['iChannel0'].value = 0  # Audio data
            self.prog['iChannel1'].value = 1  # Background image

            # Render the quad using triangle strip for better compatibility
            self.vao.render(moderngl.TRIANGLE_STRIP)

            # Read the rendered image
            data = self.fbo.read(components=4)
            # No need to flip the image since we're using correct texture coordinates
            image = Image.frombytes('RGBA', (self.width, self.height), data)

            # Add text overlay if metadata is provided
            if metadata and self.config.get("show_text", True):
                # Create a transparent overlay for text
                text_overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
                draw = ImageDraw.Draw(text_overlay)

                # Get text color and glow settings
                text_color = (255, 255, 255, 255)  # Pure white for maximum visibility
                glow_effect = self.config.get("glow_effect", "black")
                glow_blur_radius = int(self.config.get("glow_blur_radius", 3))
                glow_intensity = float(self.config.get("glow_intensity", 1.0))

                # Get artist and track title from metadata
                artist_name = metadata.get("artist_name", "")
                track_title = metadata.get("track_title", "")

                # Calculate text positions (bottom of screen)
                artist_y = self.height - 80
                title_y = self.height - 40

                # Create glow layer
                glow_layer = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
                glow_draw = ImageDraw.Draw(glow_layer)

                # Draw artist name with glow
                if artist_name:
                    # Draw glow (black text that will be blurred)
                    glow_color = (0, 0, 0, 255)
                    glow_draw.text((self.width // 2, artist_y), artist_name,
                                  fill=glow_color, font=self.artist_font, anchor="ms")

                    # Draw actual text on the main overlay
                    draw.text((self.width // 2, artist_y), artist_name,
                             fill=text_color, font=self.artist_font, anchor="ms")

                # Draw track title with glow
                if track_title:
                    # Draw glow (black text that will be blurred)
                    glow_draw.text((self.width // 2, title_y), track_title,
                                  fill=glow_color, font=self.title_font, anchor="ms")

                    # Draw actual text on the main overlay
                    draw.text((self.width // 2, title_y), track_title,
                             fill=text_color, font=self.title_font, anchor="ms")

                # Apply blur to the glow layer
                glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=glow_blur_radius))

                # Composite the glow layer onto the image first
                image = Image.alpha_composite(image, glow_layer)

                # Then composite the text overlay on top
                image = Image.alpha_composite(image, text_overlay)

            return image

        except Exception as e:
            print(f"Error rendering frame: {e}")
            import traceback
            traceback.print_exc()

            # Return a black image as fallback
            return Image.new('RGBA', (self.width, self.height), (0, 0, 0, 255))
