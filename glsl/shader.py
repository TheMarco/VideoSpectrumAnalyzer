#!/usr/bin/env python3
import sys
import time
import argparse
import pathlib
import textwrap
import os

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

def load_snippet(path):
    print(f"Loading shader snippet from: {path}")
    text = pathlib.Path(path).read_text()
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

def build_program(ctx, has_main, body, inline):
    src = FRAG_TEMPLATE.format(body=body, body_inline=inline)
    print(f"Compiled shader length: {len(src)} characters")

    try:
        program = ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=src)
        print("Shader program compiled successfully")

        # Print available uniforms for debugging
        try:
            print(f"Available uniforms: {', '.join(program.uniforms.keys())}")
        except AttributeError:
            # ModernGL version might not have uniforms attribute
            print("Uniforms not accessible via .uniforms attribute (ModernGL version difference)")

        return program
    except Exception as e:
        print(f"Error compiling shader program: {e}")
        # Print the first few lines of the shader for debugging
        print("Shader source (first 20 lines):")
        for i, line in enumerate(src.splitlines()[:20]):
            print(f"{i+1}: {line}")
        raise

def load_texture(ctx, path):
    img = Image.open(path).convert("RGBA")
    w, h = img.size
    tex = ctx.texture((w, h), 4, img.tobytes())
    tex.build_mipmaps()
    tex.repeat_x = tex.repeat_y = False
    tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
    return tex

def main():
    p = argparse.ArgumentParser()
    p.add_argument("snippet", help="Path to .glsl snippet")
    p.add_argument("--channel0", "-c0", help="Image for iChannel0")
    args = p.parse_args()

    if not glfw.init():
        print("GLFW init failed", file=sys.stderr)
        sys.exit(1)

    WIDTH, HEIGHT = 1280, 720
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    window = glfw.create_window(WIDTH, HEIGHT, "Shader Runner", None, None)
    if not window:
        print("GLFW window creation failed", file=sys.stderr)
        glfw.terminate()
        sys.exit(1)
    glfw.make_context_current(window)
    ctx = moderngl.create_context()

    has_main, body, inline = load_snippet(args.snippet)
    prog = build_program(ctx, has_main, body, inline)

    quad = ctx.buffer(np.array([
        -1, -1,   1, -1,   -1, 1,
        -1,  1,   1, -1,    1, 1,
    ], dtype='f4').tobytes())
    vao = ctx.simple_vertex_array(prog, quad, 'in_vert')

    # Set iResolution as vec3
    prog['iResolution'].value = (WIDTH, HEIGHT, 1.0)

    # Bind iChannel0 if used
    if 'iChannel0' in prog:
        tex0 = load_texture(ctx, args.channel0) if args.channel0 else ctx.texture((1,1), 4, b'\xff\xff\xff\xff')
        tex0.use(location=0)

    start = time.time()
    while not glfw.window_should_close(window):
        t = time.time() - start
        if 'iTime' in prog:
            prog['iTime'].value = t

        # Safe mouse
        try:
            x, y = glfw.get_cursor_pos(window)
            left = glfw.get_mouse_button(window, glfw.MOUSE_BUTTON_LEFT) == glfw.PRESS
            prog['iMouse'].value = (x, HEIGHT-y, float(left), 0.0)
        except Exception:
            pass

        ctx.clear(0.0, 0.0, 0.0, 1.0)
        vao.render()
        glfw.swap_buffers(window)
        glfw.poll_events()

    glfw.terminate()

class ShaderRenderer:
    """
    A class for rendering GLSL shaders to images.
    This class can be used to render frames from a shader file.
    """
    def __init__(self, shader_path, width=1280, height=720):
        """
        Initialize the shader renderer.

        Args:
            shader_path (str): Path to the shader file
            width (int): Width of the output image
            height (int): Height of the output image
        """
        self.shader_path = shader_path
        self.width = width
        self.height = height
        self.start_time = time.time()

        print(f"Initializing shader renderer for {shader_path} at {width}x{height}")

        # Initialize GLFW
        if not glfw.init():
            raise RuntimeError("GLFW initialization failed")

        # Configure GLFW window hints for offscreen rendering
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
        has_main, body, inline = load_snippet(shader_path)

        # Build shader program
        self.prog = build_program(self.ctx, has_main, body, inline)

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

    def render_frame(self, time_value=None):
        """
        Render a frame at the specified time.

        Args:
            time_value (float, optional): Time value for the shader. If None, uses elapsed time.

        Returns:
            PIL.Image: The rendered frame
        """
        # Calculate time if not provided
        if time_value is None:
            time_value = time.time() - self.start_time

        # Set time uniform
        if 'iTime' in self.prog:
            self.prog['iTime'].value = time_value

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

if __name__ == "__main__":
    main()
