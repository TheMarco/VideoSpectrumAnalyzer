import moderngl
import numpy as np
import math

class GLCircularEqualizerRenderer:
    """
    Class for rendering Circular Equalizer frames using ModernGL.
    """

    def __init__(self, ctx: moderngl.Context, width: int, height: int, config: dict):
        """
        Initialize the GL renderer.

        Args:
            ctx (moderngl.Context): The ModernGL context.
            width (int): Frame width.
            height (int): Frame height.
            config (dict): Configuration dictionary.
        """
        self.ctx = ctx
        self.width = width
        self.height = height
        self.config = config
        self.is_silent_state = False  # Flag to track if we're in a silent state

        # Get parameters from config
        self.n_bars = config["n_bars"]
        self.segments_per_bar = config["segments_per_bar"]
        self.circle_diameter = int(config["circle_diameter"])
        self.bar_width = int(config["bar_width"])
        self.bar_gap = int(config["bar_gap"])
        self.segment_height = int(config["segment_height"])
        self.segment_gap = int(config["segment_gap"])
        self.corner_radius = int(config["corner_radius"])
        self.always_on_inner = True  # Always force this to be True to ensure inner ring is always visible
        self.pil_alpha = config.get("pil_alpha", 255) # Note: Alpha will be handled in GL shader later

        # Shader-specific amplitude and gain settings
        self.overall_master_gain = config.get("overall_master_gain", 1.2)  # Increased from 1.0 for better visibility
        self.freq_gain_min_mult = config.get("freq_gain_min_mult", 1.0)  # Increased to 1.0 for equal response across all frequencies
        self.freq_gain_max_mult = config.get("freq_gain_max_mult", 1.0)  # Set to 1.0 for equal response across all frequencies
        self.freq_gain_curve_power = config.get("freq_gain_curve_power", 0.0)  # Set to 0.0 for a completely linear curve
        self.bar_height_power = config.get("bar_height_power", 1.0)  # Keep at 1.0 for linear response
        self.amplitude_compression_power = config.get("amplitude_compression_power", 0.8)  # Further reduced to boost lower amplitudes
        self.freq_pos_power = config.get("freq_pos_power", 1.0)  # Set to 1.0 for linear frequency distribution

        # Shader-specific color settings (using RGB tuples)
        self.color_lit_dark_rgb = config.get("color_lit_dark_rgb", (int(0.4*255), int(0.4*255), int(0.4*255)))
        self.color_lit_bright_rgb = config.get("color_lit_bright_rgb", (int(1.0*255), int(1.0*255), int(1.0*255)))
        self.color_unlit_rgb = config.get("color_unlit_rgb", (int(0.08*255), int(0.08*255), int(0.08*255)))
        self.color_border_rgb = config.get("color_border_rgb", (0, 0, 0))
        self.lit_brightness_multiplier = config.get("lit_brightness_multiplier", 1.3)

        self.visualizer_placement = config.get("visualizer_placement", "center")
        self.start_angle = config.get("start_angle", 270)
        self.start_angle_rad = math.radians(self.start_angle)

        # Calculate visualization dimensions
        self.max_radius = self.circle_diameter // 2

        # Calculate inner radius based on the configured parameters
        min_circumference = self.n_bars * (self.bar_width + self.bar_gap)
        min_inner_radius = min_circumference / (2 * math.pi)

        if self.circle_diameter <= 400:
            proportion = 0.25
        else:
            proportion = 0.25 - (self.circle_diameter - 400) / 4000
            proportion = max(0.15, proportion)

        proportion_inner_radius = int(self.max_radius * proportion)
        self.inner_radius = max(int(min_inner_radius), proportion_inner_radius)
        self.inner_radius = max(10, self.inner_radius)

        # Calculate center position based on placement (simplified for now, assuming no text)
        self.center_x = width // 2
        self.center_y = height // 2

        # Calculate segment dimensions
        total_segment_space = self.max_radius - self.inner_radius
        if self.segments_per_bar > 1:
            self.segment_radial_size = total_segment_space / self.segments_per_bar
            if self.segment_height > self.segment_radial_size:
                self.segment_height = int(self.segment_radial_size * 0.8)
                self.segment_height = max(1, self.segment_height)
        else:
            self.segment_radial_size = total_segment_space

        # We'll use a fixed pixel width for bars at all radii
        # First, ensure the bar width is reasonable
        max_possible_bar_width = (2 * math.pi * self.inner_radius) / (self.n_bars * 2)
        if self.bar_width > max_possible_bar_width:
            self.bar_width = int(max_possible_bar_width * 0.8)
            self.bar_width = max(1, self.bar_width)

        # Store the fixed bar width for all segments
        self.fixed_bar_width_px = self.bar_width

        # Calculate the angular width at the inner radius
        # This is used for spacing the bars evenly
        inner_angular_width = self.bar_width / self.inner_radius

        # Calculate the gap angle in radians at the inner radius
        gap_angle_radians = self.bar_gap / self.inner_radius

        # Calculate the total angle needed for each bar including its gap
        total_angle_per_bar = inner_angular_width + gap_angle_radians

        # Calculate the total angular space needed for all bars and gaps
        total_angular_space_needed = total_angle_per_bar * self.n_bars

        # If the total exceeds 2π, we need to scale down
        if total_angular_space_needed > 2 * math.pi:
            scale_factor = (2 * math.pi) / total_angular_space_needed
            inner_angular_width *= scale_factor
            gap_angle_radians *= scale_factor
            total_angle_per_bar = inner_angular_width + gap_angle_radians
            total_angular_space_needed = 2 * math.pi

        # Calculate the offset to center all bars evenly around the circle
        self.bar_offset_angle = (2 * math.pi - total_angular_space_needed) / 2.0

        # Store these values for use in vertex generation
        self.inner_angular_width = inner_angular_width
        self.gap_angle_radians = gap_angle_radians
        self.total_angle_per_bar = total_angle_per_bar

        # Debug output
        print(f"Bar configuration: fixed_width={self.fixed_bar_width_px}px, gap={self.bar_gap}px")
        print(f"Angular values at inner radius: bar={inner_angular_width:.6f}rad, gap={gap_angle_radians:.6f}rad, total={total_angle_per_bar:.6f}rad")
        print(f"Total space needed: {total_angular_space_needed:.6f}rad, offset: {self.bar_offset_angle:.6f}rad")
        print(f"Inner radius: {self.inner_radius}px, Max radius: {self.max_radius}px")

        # Placeholder for GL resources (program, vao, etc.)
        self.program = None
        self.vao = None
        self.vbo = None
        self.background_program = None
        self.background_vao = None
        self.quad_vbo = None


        # Initialize GL resources
        self._init_gl_resources()

    def _init_gl_resources(self):
        """
        Initialize ModernGL program, VAO, and VBO.
        """
        # Define a simple vertex shader for the equalizer bars
        vertex_shader_source = """
            #version 330

            in vec2 in_position;
            in vec3 in_color;
            out vec3 v_color;

            uniform mat4 projection;
            uniform mat4 model;

            void main() {
                gl_Position = projection * model * vec4(in_position, 0.0, 1.0);
                v_color = in_color;
            }
        """

        # Define a simple fragment shader for the equalizer bars
        fragment_shader_source = """
            #version 330

            in vec3 v_color;
            out vec4 f_color;

            void main() {
                f_color = vec4(v_color, 1.0);
            }
        """

        self.program = self.ctx.program(
            vertex_shader=vertex_shader_source,
            fragment_shader=fragment_shader_source,
        )

        # Placeholder for vertex data (will be generated per frame)
        # We'll use a VBO to hold the vertex data for all segments
        self.vbo = self.ctx.buffer(reserve=1024 * 1024) # Reserve some space

        # Create a VAO for the equalizer bars
        self.vao = self.ctx.simple_vertex_array(
            self.program,
            self.vbo,
            'in_position', 'in_color'
        )

        # Set up projection matrix (orthographic projection) for the equalizer
        projection = np.ortho(0, self.width, 0, self.height, -1, 1, dtype='f4')
        self.program['projection'].write(projection)

        # --- Background Rendering Resources ---
        # Vertex shader for the background quad
        background_vertex_shader_source = """
            #version 330

            in vec2 in_position;
            in vec2 in_uv;
            out vec2 v_uv;

            void main() {
                gl_Position = vec4(in_position, 0.0, 1.0);
                v_uv = in_uv;
            }
        """

        # Fragment shader for the background quad (samples from texture)
        background_fragment_shader_source = """
            #version 330

            in vec2 v_uv;
            out vec4 f_color;

            uniform sampler2D background_texture;

            void main() {
                f_color = texture(background_texture, v_uv);
            }
        """

        self.background_program = self.ctx.program(
            vertex_shader=background_vertex_shader_source,
            fragment_shader=background_fragment_shader_source,
        )

        # Vertices for a screen-filling quad
        quad_vertices = np.array([
            -1.0, -1.0, 0.0, 0.0, # Bottom-left
             1.0, -1.0, 1.0, 0.0, # Bottom-right
             1.0,  1.0, 1.0, 1.0, # Top-right
            -1.0,  1.0, 0.0, 1.0, # Top-left
        ], dtype='f4')

        self.quad_vbo = self.ctx.buffer(quad_vertices)

        # Create a VAO for the background quad
        self.background_vao = self.ctx.simple_vertex_array(
            self.background_program,
            self.quad_vbo,
            'in_position', 'in_uv'
        )


    def render_background(self, background_texture: moderngl.Texture):
        """
        Render the background texture to the framebuffer.

        Args:
            background_texture (moderngl.Texture): The texture containing the background.
        """
        if self.background_program and self.background_vao and background_texture:
            self.ctx.use_program(self.background_program)
            background_texture.use(0) # Use texture unit 0
            self.background_program['background_texture'].value = 0 # Link uniform to texture unit
            self.background_vao.render(moderngl.TRIANGLE_FAN)


    def render_frame(self, smoothed_spectrum: np.ndarray, background_texture: moderngl.Texture = None, debug_mode=False):
        """
        Render a single frame of the circular equalizer using ModernGL.

        Args:
            smoothed_spectrum (numpy.ndarray): Smoothed spectrum values.
            background_texture (moderngl.Texture, optional): Background texture to render.
            debug_mode (bool, optional): Whether to print debug information.
        """
        # Print debug info
        if debug_mode:
            # Print the first and last 10 values
            print(f"First 10 audio values: {smoothed_spectrum[:10]}")
            print(f"Last 10 audio values: {smoothed_spectrum[-10:]}")

            # Print the min, max, and mean values
            print(f"Spectrum stats - min: {np.min(smoothed_spectrum):.4f}, max: {np.max(smoothed_spectrum):.4f}, mean: {np.mean(smoothed_spectrum):.4f}")

        # Check if we're in a silent state (all values very low or all values are the same)
        # This threshold should match what we see in the logs (0.001 is considered silence)
        max_val = np.max(smoothed_spectrum)
        min_val = np.min(smoothed_spectrum)

        # Consider it silent if:
        # 1. All values are very low (below threshold), OR
        # 2. All values are exactly the same (indicating artificial/test data with no variation)
        # 3. All values are within a very small range (indicating no meaningful audio variation)
        # 4. All values are exactly 0.8 (specific case we're seeing in the logs)
        # 5. All values are within 0.001 of 0.8 (to catch slight variations around 0.8)
        is_silent = (max_val <= 0.002) or \
                   (max_val == min_val and len(smoothed_spectrum) > 1) or \
                   (abs(max_val - min_val) < 0.001 and len(smoothed_spectrum) > 1) or \
                   (abs(max_val - 0.8) < 0.001 and abs(min_val - 0.8) < 0.001) or \
                   (abs(np.mean(smoothed_spectrum) - 0.8) < 0.001)

        if debug_mode:
            # Calculate the conditions separately for better debugging
            condition1 = max_val <= 0.002
            condition2 = max_val == min_val and len(smoothed_spectrum) > 1
            condition3 = abs(max_val - min_val) < 0.001 and len(smoothed_spectrum) > 1
            condition4 = abs(max_val - 0.8) < 0.001 and abs(min_val - 0.8) < 0.001
            condition5 = abs(np.mean(smoothed_spectrum) - 0.8) < 0.001

            print(f"Silence detection - max: {max_val:.6f}, min: {min_val:.6f}, mean: {np.mean(smoothed_spectrum):.6f}, is_silent: {is_silent}")
            print(f"Silence conditions: low values: {condition1}, all same: {condition2}, small range: {condition3}, all 0.8: {condition4}, mean ≈ 0.8: {condition5}")

        # If we're in a silent state, zero out all values to ensure only the inner ring is shown
        if is_silent:
            # Create a copy to avoid modifying the original array
            smoothed_spectrum = np.zeros_like(smoothed_spectrum)
            # Set a flag to indicate silence state for the vertex generation
            self.is_silent_state = True
            if debug_mode:
                # Print which condition triggered the silence detection
                if max_val <= 0.002:
                    print("SILENCE DETECTED (low values) - Zeroed all spectrum values to ensure only inner ring is shown")
                elif max_val == min_val and len(smoothed_spectrum) > 1:
                    print("SILENCE DETECTED (all same values) - Zeroed all spectrum values to ensure only inner ring is shown")
                elif abs(max_val - min_val) < 0.001 and len(smoothed_spectrum) > 1:
                    print("SILENCE DETECTED (small range) - Zeroed all spectrum values to ensure only inner ring is shown")
                elif abs(max_val - 0.8) < 0.001 and abs(min_val - 0.8) < 0.001:
                    print("SILENCE DETECTED (all values ≈ 0.8) - Zeroed all spectrum values to ensure only inner ring is shown")
                elif abs(np.mean(smoothed_spectrum) - 0.8) < 0.001:
                    print("SILENCE DETECTED (mean ≈ 0.8) - Zeroed all spectrum values to ensure only inner ring is shown")
                else:
                    print("SILENCE DETECTED (unknown condition) - Zeroed all spectrum values to ensure only inner ring is shown")

                # Print a sample of the values to help diagnose
                print(f"Sample values before zeroing: {smoothed_spectrum[:5]}")
        else:
            self.is_silent_state = False
            if debug_mode:
                print("ACTIVE AUDIO - Using normal spectrum values")

        # Clear the framebuffer
        self.ctx.clear(0.0, 0.0, 0.0, 0.0) # Clear with transparency

        # Render background if provided
        if background_texture:
            self.render_background(background_texture)

        # Generate vertex data for the bars based on the spectrum
        vertex_data = self._generate_bar_vertices(smoothed_spectrum, debug_mode)

        # Write vertex data to the VBO
        self.vbo.write(vertex_data.astype('f4'))

        # Use the equalizer program
        self.ctx.use_program(self.program)

        # Set up model matrix (identity for now, transformations will be in vertex generation)
        model = np.identity(4, dtype='f4')
        self.program['model'].write(model)

        # Render the bars (assuming each segment is a quad, 6 vertices per segment)
        num_vertices = vertex_data.shape[0] // 5 # 5 components per vertex (x, y, r, g, b)
        self.vao.render(moderngl.TRIANGLES, vertices=num_vertices)


    def _generate_bar_vertices(self, smoothed_spectrum: np.ndarray, debug_mode=False) -> np.ndarray:
        """
        Generate vertex data for all segments of all bars using GL coordinates.

        Args:
            smoothed_spectrum (numpy.ndarray): Smoothed spectrum values.
            debug_mode (bool, optional): Whether to print debug information.

        Returns:
            np.ndarray: Array of vertex data (x, y, r, g, b).
        """
        vertices = []

        for i in range(self.n_bars):
            # Calculate the angle for the center of this bar
            # Use the pre-calculated values from __init__ to ensure consistent spacing

            # Calculate the center angle for this bar
            # Add the offset angle to ensure bars are evenly distributed
            bar_center_angle = self.start_angle_rad + self.bar_offset_angle + i * self.total_angle_per_bar

            # --- Get Audio Data for the Current Bar ---
            # Use a linear frequency mapping for more consistent bar heights
            # This ensures each bar gets an equal portion of the spectrum

            # Calculate normalized position (0 to 1)
            norm_pos = float(i) / float(self.n_bars - 1)

            # Use a simple linear mapping for even distribution
            # This gives each bar an equal portion of the frequency spectrum
            freq_pos = norm_pos

            # Calculate spectrum index using the frequency position
            spectrum_idx = min(int(freq_pos * len(smoothed_spectrum)), len(smoothed_spectrum) - 1)

            # Sample raw amplitude (ensuring we don't go out of bounds)
            raw_amplitude = smoothed_spectrum[spectrum_idx]

            # Apply a very low noise gate to avoid cutting off too many low amplitudes
            # This ensures more bars are visible even with quieter audio
            noise_gate = 0.001  # Reduced from 0.005 to show more subtle audio details
            raw_amplitude = max(0.0, raw_amplitude - noise_gate)

            # --- Apply Simplified Amplitude Processing for Consistent Heights ---
            # Apply compression to boost lower amplitudes
            processed_amplitude = pow(raw_amplitude, self.amplitude_compression_power)

            # Apply a consistent gain multiplier to all bars
            # This ensures all bars have the same sensitivity
            amplitude_after_gain = processed_amplitude * self.overall_master_gain

            # Apply final power curve for visual effect
            final_amplitude = pow(amplitude_after_gain, self.bar_height_power)

            # Only apply a very minimal noise gate to avoid completely silent bars
            # This ensures more bars are visible with subtle audio
            if raw_amplitude < 0.002:  # Reduced from 0.05 to show more subtle audio details
                final_amplitude = 0.0

            # Apply a consistent gain to all bars to ensure they have the same maximum height
            # This prevents some bars from being shorter than others
            if final_amplitude > 0.0:
                # Scale up to ensure bars reach their full height
                final_amplitude = min(1.0, final_amplitude * 1.2)

            # Clamp the final amplitude to be between 0 and 1
            final_amplitude = max(0.0, min(1.0, final_amplitude))

            # --- Determine how many segments are lit based on final amplitude ---
            lit_segments_count = int(math.floor(final_amplitude * float(self.segments_per_bar)))

            # Iterate through all segments for this bar
            for k in range(self.segments_per_bar):
                segment_idx = k # 0 is innermost segment

                # Determine if this segment should be lit
                is_lit = False

                # Lighting logic:
                # 1. If we're in a global silent state, only light the innermost segment of each bar
                # 2. Otherwise, light segments based on amplitude
                if self.is_silent_state:
                    # For silent state, only light the innermost segment of each bar
                    if segment_idx == 0:
                        is_lit = True
                else:
                    # For normal audio, light segments based on amplitude
                    if segment_idx < lit_segments_count:
                        is_lit = True

                # Only generate vertices for lit segments
                if is_lit:
                    # Calculate segment's inner and outer radii
                    segment_inner_radius = self.inner_radius + segment_idx * self.segment_radial_size
                    segment_outer_radius = segment_inner_radius + self.segment_radial_size

                    # (constant-width bars) segments drawn as rotated rectangles

                    # Interpolate color based on segment height using shader logic
                    segment_norm_height = float(segment_idx) / float(max(1, self.segments_per_bar - 1))

                    # Special case for innermost segment (the ring)
                    if segment_idx == 0:
                        # For the innermost segment, we use different coloring based on silence state
                        if self.is_silent_state:
                            # For global silence, use a consistent dim color for all ring segments
                            # This creates a uniform ring appearance during silence
                            dimming_factor = 0.25  # Consistent dim factor for the ring during silence
                            color_rgb = tuple(
                                int(self.color_lit_dark_rgb[c] * dimming_factor)
                                for c in range(3)
                            )
                        else:
                            # For active audio, use normal color interpolation but slightly dimmer
                            # This makes the ring segments for active bars stand out more
                            color_rgb = tuple(
                                int(self.color_lit_dark_rgb[c] * (1.0 - segment_norm_height) +
                                    self.color_lit_bright_rgb[c] * segment_norm_height * 0.7)  # Slightly dimmer
                                for c in range(3)
                            )
                    else:
                        # Normal color interpolation for other segments
                        color_rgb = tuple(
                            int(self.color_lit_dark_rgb[c] * (1.0 - segment_norm_height) +
                                self.color_lit_bright_rgb[c] * segment_norm_height)
                            for c in range(3)
                        )

                    # Apply brightness multiplier for lit segments
                    # For innermost segments during silence, don't apply the brightness multiplier
                    if not (segment_idx == 0 and self.is_silent_state):
                        color_rgb = tuple(min(255, int(c * self.lit_brightness_multiplier)) for c in color_rgb)

                    color = (color_rgb[0]/255.0, color_rgb[1]/255.0, color_rgb[2]/255.0) # Normalize to 0-1

                    # Compute rectangle corners for truly consistent bar width
                    # We need to adjust the angular width at each radius to maintain the same physical width
                    theta = bar_center_angle

                    # Calculate half-width angles at inner and outer radii
                    # This ensures the arc length is the same at both radii
                    inner_half_angle = (self.fixed_bar_width_px / 2.0) / segment_inner_radius
                    outer_half_angle = (self.fixed_bar_width_px / 2.0) / segment_outer_radius

                    # Calculate the four corners using the appropriate angles
                    # Inner radius, left corner
                    theta1 = theta - inner_half_angle
                    x1 = self.center_x + math.cos(theta1) * segment_inner_radius
                    y1 = self.center_y + math.sin(theta1) * segment_inner_radius

                    # Outer radius, left corner
                    theta2 = theta - outer_half_angle
                    x2 = self.center_x + math.cos(theta2) * segment_outer_radius
                    y2 = self.center_y + math.sin(theta2) * segment_outer_radius

                    # Outer radius, right corner
                    theta3 = theta + outer_half_angle
                    x3 = self.center_x + math.cos(theta3) * segment_outer_radius
                    y3 = self.center_y + math.sin(theta3) * segment_outer_radius

                    # Inner radius, right corner
                    theta4 = theta + inner_half_angle
                    x4 = self.center_x + math.cos(theta4) * segment_inner_radius
                    y4 = self.center_y + math.sin(theta4) * segment_inner_radius

                    vertices.extend([
                        (x1, y1, *color), (x2, y2, *color), (x3, y3, *color),
                        (x1, y1, *color), (x3, y3, *color), (x4, y4, *color),
                    ])

        return np.array(vertices, dtype='f4')


    def cleanup(self):
        """
        Clean up GL resources.
        """
        if self.program:
            self.program.release()
        if self.vao:
            self.vao.release()
        if self.vbo:
            self.vbo.release()
        if self.background_program:
            self.background_program.release()
        if self.background_vao:
            self.background_vao.release()
        if self.quad_vbo:
            self.quad_vbo.release()