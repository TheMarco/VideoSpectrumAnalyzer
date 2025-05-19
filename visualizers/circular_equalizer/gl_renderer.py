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

        # Get parameters from config
        self.n_bars = config["n_bars"]
        self.segments_per_bar = config["segments_per_bar"]
        self.circle_diameter = int(config["circle_diameter"])
        self.bar_width = int(config["bar_width"])
        self.bar_gap = int(config["bar_gap"])
        self.segment_height = int(config["segment_height"])
        self.segment_gap = int(config["segment_gap"])
        self.corner_radius = int(config["corner_radius"])
        self.always_on_inner = config.get("always_on_inner", True)
        self.pil_alpha = config.get("pil_alpha", 255) # Note: Alpha will be handled in GL shader later

        # Shader-specific amplitude and gain settings
        self.overall_master_gain = config.get("overall_master_gain", 1.0)
        self.freq_gain_min_mult = config.get("freq_gain_min_mult", 0.4)
        self.freq_gain_max_mult = config.get("freq_gain_max_mult", 1.8)
        self.freq_gain_curve_power = config.get("freq_gain_curve_power", 0.6)
        self.bar_height_power = config.get("bar_height_power", 1.1)
        self.amplitude_compression_power = config.get("amplitude_compression_power", 1.0)
        self.freq_pos_power = config.get("freq_pos_power", 1.7)  # Match the shader's power value

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

        # Calculate the angle between bars
        self.angle_per_bar = 2 * math.pi / self.n_bars
        self.bar_arc_width = 2 * math.pi * self.inner_radius / self.n_bars
        if self.bar_width > self.bar_arc_width:
            self.bar_width = int(self.bar_arc_width * 0.8)
            self.bar_width = max(1, self.bar_width)

        total_angular_space = 2 * math.pi
        angular_gap_size = (self.bar_gap / (2 * math.pi * self.inner_radius)) * total_angular_space
        angular_space_for_bars = total_angular_space - (angular_gap_size * self.n_bars)
        self.angle_per_bar_segment = angular_space_for_bars / self.n_bars

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


    def render_frame(self, smoothed_spectrum: np.ndarray, background_texture: moderngl.Texture = None):
        """
        Render a single frame of the circular equalizer using ModernGL.

        Args:
            smoothed_spectrum (numpy.ndarray): Smoothed spectrum values.
            background_texture (moderngl.Texture, optional): Background texture to render.
        """
        # Clear the framebuffer
        self.ctx.clear(0.0, 0.0, 0.0, 0.0) # Clear with transparency

        # Render background if provided
        if background_texture:
            self.render_background(background_texture)

        # Generate vertex data for the bars based on the spectrum
        vertex_data = self._generate_bar_vertices(smoothed_spectrum)

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


    def _generate_bar_vertices(self, smoothed_spectrum: np.ndarray) -> np.ndarray:
        """
        Generate vertex data for all segments of all bars using GL coordinates.

        Returns:
            np.ndarray: Array of vertex data (x, y, r, g, b).
        """
        vertices = []

        for i in range(self.n_bars):
            # Calculate the angle for the center of this bar
            # Add half of the bar segment angle to center the bar within its allocated space
            bar_center_angle = self.start_angle_rad + i * (self.angle_per_bar_segment + (self.bar_gap / (2 * math.pi * self.inner_radius)) * 2 * math.pi / self.n_bars) + self.angle_per_bar_segment / 2

            # --- Get Audio Data for the Current Bar ---
            # Map the bar index to a frequency position (0.0 to 1.0) in the audio texture.
            # Use the freq_pos_power for non-linear mapping
            freq_pos = pow(float(i) / float(self.n_bars - 1), self.freq_pos_power)

            # Ensure we have a valid index for the spectrum data
            spectrum_idx = min(i, len(smoothed_spectrum) - 1)

            # Sample raw amplitude (ensuring we don't go out of bounds)
            raw_amplitude = smoothed_spectrum[spectrum_idx]

            # Apply noise gate to filter out very low amplitudes
            noise_gate = 0.01
            raw_amplitude = max(0.0, raw_amplitude - noise_gate)

            # --- Apply Sensitivity and Frequency-Dependent Gain ---
            processed_amplitude = pow(raw_amplitude, self.amplitude_compression_power)
            bar_norm = float(i) / float(self.n_bars - 1) # 0 for first bar, 1 for last
            curved_bar_norm = pow(bar_norm, self.freq_gain_curve_power)
            # Linear interpolation (equivalent to GLSL mix function)
            freq_gain_multiplier = self.freq_gain_min_mult * (1.0 - curved_bar_norm) + self.freq_gain_max_mult * curved_bar_norm
            amplitude_after_gain = processed_amplitude * self.overall_master_gain * freq_gain_multiplier
            final_amplitude = pow(amplitude_after_gain, self.bar_height_power) # Height 0.0 to 1.0 after power curve

            # Clamp the final amplitude to be between 0 and 1
            final_amplitude = max(0.0, min(1.0, final_amplitude))

            # --- Determine how many segments are lit based on final amplitude ---
            lit_segments_count = int(math.floor(final_amplitude * float(self.segments_per_bar)))

            # Iterate through all segments for this bar
            for k in range(self.segments_per_bar):
                segment_idx = k # 0 is innermost segment

                # Determine if this segment should be lit
                is_lit = False
                # Lighting logic similar to the shader: segment is lit if its index is less than the number of segments to light,
                # OR if it's the innermost segment and always_on_inner is true.
                if segment_idx < lit_segments_count or (self.always_on_inner and segment_idx == 0):
                    is_lit = True

                # Only generate vertices for lit segments
                if is_lit:
                    # Calculate segment's inner and outer radii
                    segment_inner_radius = self.inner_radius + segment_idx * self.segment_radial_size
                    segment_outer_radius = segment_inner_radius + self.segment_radial_size

                    # Calculate segment's start and end angles
                    # Use the pre-calculated angle per bar segment
                    half_bar_angle_segment = self.angle_per_bar_segment / 2.0
                    segment_start_angle = bar_center_angle - half_bar_angle_segment
                    segment_end_angle = bar_center_angle + half_bar_angle_segment

                    # Interpolate color based on segment height using shader logic
                    segment_norm_height = float(segment_idx) / float(max(1, self.segments_per_bar - 1))
                    color_rgb = tuple(
                        int(self.color_lit_dark_rgb[c] * (1.0 - segment_norm_height) + self.color_lit_bright_rgb[c] * segment_norm_height)
                        for c in range(3)
                    )

                    # Apply brightness multiplier for lit segments
                    color_rgb = tuple(min(255, int(c * self.lit_brightness_multiplier)) for c in color_rgb)

                    color = (color_rgb[0]/255.0, color_rgb[1]/255.0, color_rgb[2]/255.0) # Normalize to 0-1

                    # Generate vertices for a quad representing the segment
                    # Vertices are in (x, y, r, g, b) format
                    # Inner points
                    ix1 = self.center_x + segment_inner_radius * math.cos(segment_start_angle)
                    iy1 = self.center_y + segment_inner_radius * math.sin(segment_start_angle)
                    ix2 = self.center_x + segment_inner_radius * math.cos(segment_end_angle)
                    iy2 = self.center_y + segment_inner_radius * math.sin(segment_end_angle)

                    # Outer points
                    ox1 = self.center_x + segment_outer_radius * math.cos(segment_start_angle)
                    oy1 = self.center_y + segment_outer_radius * math.sin(segment_start_angle)
                    ox2 = self.center_x + segment_outer_radius * math.cos(segment_end_angle)
                    oy2 = self.center_y + segment_outer_radius * math.sin(segment_end_angle)

                    # Add vertices for two triangles forming a quad
                    vertices.extend([
                        (ix1, iy1, *color), (ox1, oy1, *color), (ox2, oy2, *color), # Triangle 1
                        (ix1, iy1, *color), (ox2, oy2, *color), (ix2, iy2, *color), # Triangle 2
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