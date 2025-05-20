"""
Simple test renderer to verify the GL rendering pipeline is working.
"""
import os
import time
import numpy as np
from PIL import Image
import moderngl

class TestCircleRenderer:
    """Simple renderer that just draws a colored circle."""
    
    def __init__(self, width=800, height=600):
        """Initialize the renderer."""
        self.width = width
        self.height = height
        self.start_time = time.time()
        
        # Initialize ModernGL context
        self.ctx = moderngl.create_standalone_context()
        
        # Load shader
        shader_path = os.path.join('glsl', 'test_circle.glsl')
        with open(shader_path, 'r') as f:
            shader_source = f.read()
        
        # Create shader program
        self.prog = self._create_shader_program(shader_source)
        
        # Create vertex buffer and VAO
        vertices = np.array([
            # x, y, u, v
            -1.0, -1.0, 0.0, 0.0,  # bottom-left
            1.0, -1.0, 1.0, 0.0,   # bottom-right
            1.0, 1.0, 1.0, 1.0,    # top-right
            -1.0, 1.0, 0.0, 1.0,   # top-left
        ], dtype='f4')
        
        indices = np.array([
            0, 1, 2,  # first triangle
            0, 2, 3,  # second triangle
        ], dtype='i4')
        
        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.ibo = self.ctx.buffer(indices.tobytes())
        
        self.vao = self.ctx.vertex_array(
            self.prog,
            [
                (self.vbo, '2f 2f', 'in_position', 'in_texcoord'),
            ],
            self.ibo
        )
        
        # Create framebuffer
        self.fbo_texture = self.ctx.texture((width, height), 4)
        self.fbo = self.ctx.framebuffer(self.fbo_texture)
    
    def _create_shader_program(self, shader_source):
        """Create a shader program from the given source."""
        vertex_shader = """
        #version 330

        in vec2 in_position;
        in vec2 in_texcoord;
        
        out vec2 v_texcoord;
        
        void main() {
            gl_Position = vec4(in_position, 0.0, 1.0);
            v_texcoord = in_texcoord;
        }
        """
        
        fragment_shader_template = """
        #version 330
        
        in vec2 v_texcoord;
        out vec4 f_color;
        
        uniform vec2 iResolution;
        uniform float iTime;
        
        // The shader body will be inserted here
        {shader_body}
        
        void main() {{
            vec4 fragColor;
            mainImage(fragColor, v_texcoord * iResolution.xy);
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
    
    def render_frame(self, current_time=None):
        """Render a frame."""
        try:
            # Calculate time if not provided
            if current_time is None:
                current_time = time.time() - self.start_time
            
            # Set time uniform
            if 'iTime' in self.prog:
                self.prog['iTime'].value = current_time
            
            # Set resolution uniform
            if 'iResolution' in self.prog:
                self.prog['iResolution'].value = (self.width, self.height)
            
            # Bind the framebuffer
            self.fbo.use()
            
            # Clear the framebuffer
            self.ctx.clear(0.0, 0.0, 0.0, 0.0)
            
            # Render the quad
            self.vao.render(moderngl.TRIANGLES)
            
            # Read the pixels from the framebuffer
            pixels = self.fbo.read(components=4)
            
            # Convert to PIL Image
            result_image = Image.frombytes('RGBA', (self.width, self.height), pixels).transpose(Image.FLIP_TOP_BOTTOM)
            print(f"Rendered test circle: size={result_image.size}, mode={result_image.mode}")
            
            return result_image
        except Exception as e:
            print(f"Error rendering test circle: {e}")
            import traceback
            traceback.print_exc()
            # Return a blank image as fallback
            return Image.new('RGBA', (self.width, self.height), (255, 0, 0, 255))
    
    def cleanup(self):
        """Clean up resources."""
        try:
            if hasattr(self, 'fbo') and self.fbo:
                self.fbo.release()
            if hasattr(self, 'fbo_texture') and self.fbo_texture:
                self.fbo_texture.release()
            if hasattr(self, 'vbo') and self.vbo:
                self.vbo.release()
            if hasattr(self, 'ibo') and self.ibo:
                self.ibo.release()
            if hasattr(self, 'vao') and self.vao:
                self.vao.release()
            if hasattr(self, 'prog') and self.prog:
                self.prog.release()
            if hasattr(self, 'ctx') and self.ctx:
                self.ctx.release()
        except Exception as e:
            print(f"Error during cleanup: {e}")
