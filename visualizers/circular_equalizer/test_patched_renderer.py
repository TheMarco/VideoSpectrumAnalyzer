"""
Patched version of the GLCircularEqualizerRenderer for testing.
This fixes the np.ortho issue by implementing the function.
"""
import numpy as np
import moderngl
import math
from visualizers.circular_equalizer.gl_renderer import GLCircularEqualizerRenderer

def ortho(left, right, bottom, top, near, far, dtype=None):
    """
    Create an orthographic projection matrix.
    This is a replacement for np.ortho which doesn't exist.

    Args:
        left, right: Left and right bounds
        bottom, top: Bottom and top bounds
        near, far: Near and far bounds
        dtype: Data type for the matrix

    Returns:
        numpy.ndarray: 4x4 orthographic projection matrix
    """
    width = right - left
    height = top - bottom
    depth = far - near

    if width == 0 or height == 0 or depth == 0:
        raise ValueError("Invalid orthographic projection parameters")

    result = np.zeros((4, 4), dtype=dtype or np.float32)

    result[0, 0] = 2.0 / width
    result[1, 1] = 2.0 / height
    result[2, 2] = -2.0 / depth

    result[0, 3] = -(right + left) / width
    result[1, 3] = -(top + bottom) / height
    result[2, 3] = -(far + near) / depth
    result[3, 3] = 1.0

    return result

class PatchedGLCircularEqualizerRenderer(GLCircularEqualizerRenderer):
    """
    Patched version of the GLCircularEqualizerRenderer that fixes the np.ortho issue.
    """

    def render_frame(self, smoothed_spectrum: np.ndarray, background_texture: moderngl.Texture = None):
        """
        Render a single frame of the circular equalizer using ModernGL.
        This is a patched version that works with the standalone context.

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

        # In standalone context, we don't need to call use() on the program
        # self.program.use() - removed as it's not needed in standalone context

        # Set up model matrix (identity for now, transformations will be in vertex generation)
        model = np.identity(4, dtype='f4')
        self.program['model'].write(model)

        # Render the bars (assuming each segment is a quad, 6 vertices per segment)
        num_vertices = vertex_data.shape[0] // 5 # 5 components per vertex (x, y, r, g, b)
        self.vao.render(moderngl.TRIANGLES, vertices=num_vertices)

    def render_background(self, background_texture: moderngl.Texture):
        """
        Render the background texture to the framebuffer.
        This is a patched version that works with the standalone context.

        Args:
            background_texture (moderngl.Texture): The texture containing the background.
        """
        if self.background_program and self.background_vao and background_texture:
            # In standalone context, we don't need to call use() on the program
            background_texture.use(0) # Use texture unit 0
            self.background_program['background_texture'].value = 0 # Link uniform to texture unit
            self.background_vao.render(moderngl.TRIANGLE_FAN)

    def _init_gl_resources(self):
        """
        Initialize ModernGL program, VAO, and VBO.
        This is a patched version that uses our custom ortho function.
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
        # Use our custom ortho function instead of np.ortho
        projection = ortho(0, self.width, 0, self.height, -1, 1, dtype='f4')
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
