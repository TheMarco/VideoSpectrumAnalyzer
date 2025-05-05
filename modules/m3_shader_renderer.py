"""
M3 Mac-compatible shader renderer for the Audio Visualizer Suite.
This module provides a shader renderer that works on M3 Mac chips.
"""
import os
import sys
import time
import numpy as np
from PIL import Image
import moderngl
import glfw

# Constants for shader templates
VERTEX_SHADER = """
#version 330

in vec2 in_vert;
out vec2 v_text;

void main() {
    v_text = in_vert * 0.5 + 0.5;
    gl_Position = vec4(in_vert, 0.0, 1.0);
}
"""

FRAG_TEMPLATE = """
#version 330

in vec2 v_text;
out vec4 f_color;

uniform vec3 iResolution;
uniform float iTime;
uniform vec4 iMouse;

{body}

#ifdef USE_MAIN_IMAGE
void main() {{
    vec4 fragColor;
    mainImage(fragColor, v_text * iResolution.xy);
    f_color = fragColor;
}}
#else
void main() {{
{body_inline}
}}
#endif
"""

class M3ShaderRenderer:
    """
    A shader renderer that works on M3 Mac chips.
    This is a simplified version of the shader.py script in the glsl directory.
    """
    def __init__(self, shader_path, width, height):
        """
        Initialize the shader renderer.
        
        Args:
            shader_path (str): Path to the shader file
            width (int): Width of the output
            height (int): Height of the output
        """
        self.shader_path = shader_path
        self.width = width
        self.height = height
        self.start_time = time.time()
        
        print(f"Initializing M3 shader renderer for {shader_path} at {width}x{height}")
        
        # Initialize GLFW
        if not glfw.init():
            raise RuntimeError("GLFW initialization failed")
        
        # Configure GLFW window hints
        glfw.window_hint(glfw.VISIBLE, glfw.FALSE)  # Hidden window
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)  # Required for macOS
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        
        # Create an invisible window
        self.window = glfw.create_window(width, height, "Shader Renderer", None, None)
        if not self.window:
            glfw.terminate()
            raise RuntimeError("GLFW window creation failed")
        
        glfw.make_context_current(self.window)
        print("GLFW window created successfully")
        
        # Create ModernGL context
        self.ctx = moderngl.create_context()
        print(f"ModernGL context created: {self.ctx}")
        
        # Load shader from file
        has_main, body, inline = self.load_snippet(shader_path)
        
        # Build shader program
        self.prog = self.build_program(has_main, body, inline)
        
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
        
        # Create framebuffer for offscreen rendering
        self.fbo = self.ctx.framebuffer(
            color_attachments=[self.ctx.texture((width, height), 4)]
        )
        
        print(f"Shader initialization complete")
    
    def load_snippet(self, path):
        """
        Load a shader snippet from a file.
        
        Args:
            path (str): Path to the shader file
            
        Returns:
            tuple: (has_main, body, inline)
        """
        print(f"Loading shader snippet from: {path}")
        with open(path, 'r') as f:
            text = f.read()
        print(f"Shader content length: {len(text)} characters")
        
        # Check if the shader contains a mainImage function
        has_main = "mainImage" in text
        print(f"Shader has mainImage function: {has_main}")
        
        if has_main:
            body = "#define USE_MAIN_IMAGE\n" + text
            inline = ""
            print("Using mainImage mode for shader")
        else:
            body = ""
            inline = "\n".join("    " + line for line in text.splitlines())
            print("Using inline mode for shader")
        
        return has_main, body, inline
    
    def build_program(self, has_main, body, inline):
        """
        Build a shader program.
        
        Args:
            has_main (bool): Whether the shader has a mainImage function
            body (str): Shader body
            inline (str): Inline shader body
            
        Returns:
            moderngl.Program: Compiled shader program
        """
        src = FRAG_TEMPLATE.format(body=body, body_inline=inline)
        print(f"Compiled shader length: {len(src)} characters")
        
        try:
            program = self.ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=src)
            print("Shader program compiled successfully")
            return program
        except Exception as e:
            print(f"Error compiling shader program: {e}")
            # Print the first few lines of the shader for debugging
            print("Shader source (first 20 lines):")
            for i, line in enumerate(src.splitlines()[:20]):
                print(f"{i+1}: {line}")
            raise
    
    def render_frame(self, current_time=None):
        """
        Render a frame at the specified time.
        
        Args:
            current_time (float, optional): Time to use for rendering. If None, uses elapsed time.
            
        Returns:
            PIL.Image: The rendered frame
        """
        # Calculate time if not provided
        if current_time is None:
            current_time = time.time() - self.start_time
        
        # Set time uniform
        if 'iTime' in self.prog:
            self.prog['iTime'].value = current_time
        
        # Process GLFW events to keep the context alive
        glfw.poll_events()
        
        # Render to framebuffer
        self.fbo.use()
        self.ctx.clear(0.0, 0.0, 0.0, 1.0)
        self.vao.render()
        
        # Read pixels from framebuffer
        data = self.fbo.read(components=4)
        
        # Convert to PIL Image
        image = Image.frombytes('RGBA', (self.width, self.height), data).transpose(Image.FLIP_TOP_BOTTOM)
        
        return image
    
    def cleanup(self):
        """Clean up resources."""
        try:
            # Clean up ModernGL resources
            if hasattr(self, 'fbo'):
                self.fbo.release()
            if hasattr(self, 'quad'):
                self.quad.release()
            if hasattr(self, 'prog'):
                self.prog.release()
            
            # Clean up GLFW
            if hasattr(self, 'window') and self.window:
                glfw.destroy_window(self.window)
                glfw.terminate()
                print("GLFW resources cleaned up")
        except Exception as e:
            print(f"Error during cleanup: {e}")
            pass
    
    def __del__(self):
        """Ensure cleanup when the object is garbage collected."""
        self.cleanup()
