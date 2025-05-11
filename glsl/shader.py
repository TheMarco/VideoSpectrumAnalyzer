#!/usr/bin/env python3
import sys
import time
import argparse
import pathlib
import textwrap
import os
import logging

logger = logging.getLogger('audio_visualizer.shader')

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
uniform sampler2D iChannel0;
uniform int iFrame;
uniform vec3 iChannelResolution[4];

// Placeholder texture function if needed
vec4 texture2D(sampler2D s, vec2 c) {{
    return texture(s, c);
}}

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

def preprocess_shader(text, shader_path=""):
    """
    Preprocess shader code to fix common issues.

    Args:
        text (str): Original shader code
        shader_path (str): Path to the shader file (for debugging)

    Returns:
        str: Preprocessed shader code
    """
    import re

    # Get the filename for special case handling
    filename = os.path.basename(shader_path)

    # Create fixed directory if it doesn't exist
    fixed_dir = os.path.join(os.path.dirname(shader_path), "fixed")
    if not os.path.exists(fixed_dir):
        os.makedirs(fixed_dir)
        print(f"Created directory for fixed shaders: {fixed_dir}")

    # Get the base name without extension
    basename = os.path.splitext(filename)[0]

    # Check if we have a known problematic shader
    known_problematic = filename in ["angel.glsl", "quantum.glsl", "blackhole.glsl", "shield.glsl", "ghosts.glsl"]

    # Special case for nebula.glsl
    if filename == "nebula.glsl":
        fixed_path = os.path.join(fixed_dir, "nebula_fixed.glsl")

        # Check if fixed version exists
        if not os.path.exists(fixed_path):
            print(f"Creating fixed version of {filename} at {fixed_path}")

            # Create the fixed version
            fixed_content = """// Nebula shader - Fixed version
// Original by @XorDev
// Based on tweet shader: https://x.com/XorDev/status/1918766627828515190

void mainImage(out vec4 O, in vec2 I)
{
    // Initialize variables
    float t = iTime;
    float i = 0.0;
    float z = 0.0;
    float d = 0.0;
    float s = 0.0;

    // Clear output color
    O = vec4(0.0, 0.0, 0.0, 0.0);

    // Main loop
    for(i = 0.0; i < 100.0; i += 1.0)
    {
        // Calculate ray position
        vec3 p = z * normalize(vec3(I+I, 0.0) - iResolution.xyy);

        // Offset by time
        p.z -= t;

        // Apply fractal distortion
        d = 1.0;
        for(float j = 0.0; j < 6.0; j += 1.0) // Limit iterations for performance
        {
            p += 0.7 * cos(p.yzx * d) / d;
            d *= 2.0; // Double the frequency each iteration
        }

        // Rotate based on depth
        p.xy *= mat2(cos(z * 0.2 + vec4(0.0, 11.0, 33.0, 0.0)));

        // Calculate distance and update s
        s = 3.0 - abs(p.x);

        // Update distance and depth
        d = 0.03 + 0.1 * max(s, -s * 0.2);
        z += d;

        // Add color
        O += (cos(s+s - vec4(5.0, 0.0, 1.0, 3.0)) + 1.4) / d / z;
    }

    // Apply tone mapping
    O = tanh(O * O / 400000.0);
}"""

            # Write the fixed version to file
            with open(fixed_path, 'w') as f:
                f.write(fixed_content)

        print(f"Using fixed version of {filename} from {fixed_path}")
        text = pathlib.Path(fixed_path).read_text()
        return text

    # Special case for angel.glsl
    if filename == "angel.glsl":
        fixed_path = os.path.join(fixed_dir, "angel_fixed.glsl")

        # Check if fixed version exists
        if not os.path.exists(fixed_path):
            print(f"Creating fixed version of {filename} at {fixed_path}")

            # Create the fixed version
            fixed_content = """// Angel shader - Fixed version
// Original by @XorDev
// An experiment based on "3D Fire": https://www.shadertoy.com/view/3XXSWS

void mainImage(out vec4 O, in vec2 I)
{
    // Time for animation
    float t = iTime;
    // Raymarch iterator
    float i = 0.0;
    // Raymarch depth
    float z = 0.0;
    // Raymarch step size
    float d = 0.0;

    // Clear output color
    O = vec4(0.0, 0.0, 0.0, 0.0);

    // Raymarch loop (100 iterations)
    for(i = 0.0; i < 100.0; i += 1.0)
    {
        // Raymarch sample position
        vec3 p = z * normalize(vec3(I+I, 0.0) - iResolution.xyy);
        // Shift camera back
        p.z += 6.0;
        // Twist shape
        p.xz *= mat2(cos(p.y * 0.5 + vec4(0.0, 33.0, 11.0, 0.0)));

        // Distortion (turbulence) loop
        d = 1.0;
        for(float j = 0.0; j < 4.0; j += 1.0)
        {
            // Add distortion waves
            p += cos((p.yzx - t * vec3(3.0, 1.0, 0.0)) * d) / d;
            d /= 0.8;
        }

        // Compute distorted distance field of cylinder
        d = (0.1 + abs(length(p.xz) - 0.5)) / 20.0;
        z += d;

        // Sample coloring and glow attenuation
        O += (sin(z + vec4(2.0, 3.0, 4.0, 0.0)) + 1.1) / d;
    }

    // Tanh tonemapping
    O = tanh(O / 4000.0);
}"""

            # Write the fixed version to file
            with open(fixed_path, 'w') as f:
                f.write(fixed_content)

        print(f"Using fixed version of {filename} from {fixed_path}")
        text = pathlib.Path(fixed_path).read_text()
        return text

    # Special case for quantum.glsl
    if filename == "quantum.glsl":
        fixed_path = os.path.join(fixed_dir, "quantum_fixed.glsl")

        # Check if fixed version exists
        if not os.path.exists(fixed_path):
            print(f"Creating fixed version of {filename} at {fixed_path}")

            # Create the fixed version
            fixed_content = """// Quantum shader - Fixed version
// Original by @XorDev

void mainImage(out vec4 O, in vec2 I)
{
    // Initialize vectors
    vec3 p = vec3(0.0);
    vec3 q = vec3(0.0);
    vec3 r = iResolution;

    // Initialize variables
    float i = 1.0;
    float j = 1.0;
    float z = 0.0;

    // Clear output color
    O = vec4(0.0, 0.0, 0.0, 0.0);

    // Main loop
    for(i = 1.0; i > 0.0; i -= 0.02)
    {
        // Calculate z value
        p = (vec3(I+I, 0.0) - r) / r.y;
        z = i - dot(p, p);
        z = max(z, -z/1e5);
        z = sqrt(z);
        p.z = z;

        // Transform p
        p /= 2.0 + z;

        // Rotate p.xz
        float ct = cos(iTime);
        float st = sin(iTime);
        float ct2 = cos(iTime + 11.0);
        float st2 = sin(iTime + 11.0);
        p.xz = mat2(ct, -st2, st, ct2) * p.xz;

        // Update q and calculate j
        q += p;
        j = cos(j * dot(cos(q), sin(q.yzx)) / 0.3);

        // Add color
        vec4 color = vec4(0.0, 0.0, 0.0, 0.0);
        color = sin(i * 30.0 + vec4(0.0, 1.0, 2.0, 3.0)) + 1.0;
        color *= i * pow(z, 0.4) * pow(j + 1.0, 8.0) / 2000.0;
        O += color;
    }

    // Final color adjustment
    O *= O;
}"""

            # Write the fixed version to file
            with open(fixed_path, 'w') as f:
                f.write(fixed_content)

        print(f"Using fixed version of {filename} from {fixed_path}")
        text = pathlib.Path(fixed_path).read_text()
        return text

    # Special case for blackhole.glsl
    if filename == "blackhole.glsl" or "#define A" in text:
        print("Detected blackhole.glsl or similar shader, applying fixes...")

        # For the original blackhole.glsl, use the special version
        if filename == "blackhole.glsl":
            fixed_path = os.path.join(fixed_dir, "blackhole_fixed.glsl")

            # Check if fixed version exists
            if not os.path.exists(fixed_path):
                print(f"Creating fixed version of {filename} at {fixed_path}")

                # Create the fixed version
                fixed_content = """// Black Hole shader - Fixed version
// This shader creates a black hole effect with accretion disk.

// Noise texture function (replacement for iChannel0)
float noise(vec3 p) {
    return fract(sin(dot(p, vec3(12.9898, 78.233, 45.5432))) * 43758.5453);
}

void mainImage(out vec4 O, in vec2 C)
{
    // Initialize vectors
    vec3 x = vec3(0.22, 0.97, 0.0);
    vec3 r = iResolution;
    vec3 d = vec3((C+C) - r.xy, -r.y) / r.x;
    vec3 p = d;

    // Reset r
    r = vec3(0.0);

    // Initialize variables
    float R = 0.0;
    float a = 0.05;
    float i = a;
    float t = iTime/4.0 + 5.0;

    // Main ray marching loop
    p.z += 4.0;
    for(; i < 200.0; i += 1.0) {
        // Move ray
        p += d/40.0;

        // Calculate radius
        R = dot(p, p);

        // Update a
        a *= min(R, 0.2) / 0.2;

        // Create transformation matrix A
        vec3 A = mix(x*dot(p,x), p, cos(t)) - sin(t)*cross(p,x);

        // Sample noise and update color
        float n1 = noise(A);
        float n03 = noise(A * 0.3);

        // Fix: max() returns a float, not a vector, so we can't use .y
        float maxVal = max(dot(A,A)*800.0, R);
        r += (2.0+d) * n1 * n03 * a / maxVal / R;

        // Update direction
        d -= p/(500.0*R*R);
    }

    // Final calculation
    p = d;
    vec3 A = mix(x*dot(p,x), p, cos(t)) - sin(t)*cross(p,x);
    float n02 = noise(A * 0.2);
    float n5 = noise(vec3(5.0/length(d)));

    O.gbr = max(r + (2.0+d) / (R*R+0.02/a-9.0) + a*A*n02, n5/0.2 - 4.0);
    O.a = 1.0; // Add alpha channel
}"""

                # Write the fixed version to file
                with open(fixed_path, 'w') as f:
                    f.write(fixed_content)

            print(f"Using fixed version of {filename} from {fixed_path}")
            text = pathlib.Path(fixed_path).read_text()
            return text

    # Special case for shield.glsl
    if filename == "shield.glsl":
        fixed_path = os.path.join(fixed_dir, "shield_fixed.glsl")

        # Check if fixed version exists
        if not os.path.exists(fixed_path):
            print(f"Creating fixed version of {filename} at {fixed_path}")

            # Create the fixed version
            fixed_content = """// Shield shader - Fixed version
// Original by @XorDev
// Inspired by @cmzw's work: witter.com/cmzw_/status/1729148918225916406

void mainImage(out vec4 O, in vec2 I)
{
    // Iterator, z and time
    float i = 0.0;
    float z = 0.0;
    float t = iTime;

    // Clear frag color
    O = vec4(0.0, 0.0, 0.0, 0.0);

    // Loop 100 times
    for(i = 0.0; i < 1.0; i += 0.01)
    {
        // Resolution for scaling
        vec2 v = iResolution.xy;

        // Center and scale outward
        vec2 p = (I + I - v) / v.y * i;

        // Sphere distortion and compute z
        z = max(1.0 - dot(p, p), 0.0);
        p /= 0.2 + sqrt(z) * 0.3;

        // Offset for hex pattern
        p.x = p.x / 0.9 + t;
        p.y += fract(ceil(p.x) * 0.5) + t * 0.2;

        // Mirror quadrants
        v = abs(fract(p) - 0.5);

        // Add color and fade outward
        O += vec4(2.0, 3.0, 5.0, 1.0) / 2000.0 * z /
             (abs(max(v.x * 1.5 + v.y, v.x + v.y * 2.0) - 1.0) + 0.1 - i * 0.09);
    }

    // Tanh tonemap
    O = tanh(O * O);
}"""

            # Write the fixed version to file
            with open(fixed_path, 'w') as f:
                f.write(fixed_content)

        print(f"Using fixed version of {filename} from {fixed_path}")
        text = pathlib.Path(fixed_path).read_text()
        return text

    # For other shaders with similar patterns to blackhole.glsl
    if "#define A" in text and "#define N(p)" in text and "iChannel0" in text:
        # Create a placeholder texture sampler
        texture_sampler = """
// Placeholder texture sampler
vec4 sampleTexture(vec3 p) {
    return vec4(length(p)); // Simple placeholder
}
"""
        # Replace the #define with a function
        text = re.sub(r'#define\s+N\s*\(\s*p\s*\)\s*texture\s*\(\s*iChannel0\s*,\s*A\s*\*\s*p\s*\)\s*\.r',
                      "// Original: #define N(p) texture(iChannel0, A*p).r\n// Using placeholder texture sampler\n#define N(p) sampleTexture(A*p).r",
                      text)

        # Add the texture sampler function at the beginning
        text = texture_sampler + text

        # Fix comma-separated vector declarations
        lines = text.split('\n')
        for i in range(len(lines)):
            # Look for lines with comma-separated vector declarations like "vec3 x = vec3(.22,.97,0),"
            if re.search(r'vec[234]\s+\w+\s*=.*,', lines[i]):
                # Extract the type
                type_match = re.search(r'(vec[234])\s+', lines[i])
                if type_match:
                    type_name = type_match.group(1)
                    # Replace commas with semicolons and type declarations
                    parts = lines[i].split(',')
                    if len(parts) > 1:
                        # First part already has the type
                        result = parts[0].strip()
                        # Add type to other parts
                        for j in range(1, len(parts)):
                            part = parts[j].strip()
                            if j == len(parts) - 1 and ';' in part:
                                part = part.replace(';', '')
                                result += f";\n{type_name} {part};"
                            else:
                                result += f";\n{type_name} {part}"
                        lines[i] = result

        # Fix statements with multiple operations separated by commas
        for i in range(len(lines)):
            # Look for lines with multiple operations separated by commas
            if re.search(r'[^(,]\s*,\s*[^),]', lines[i]) and not re.search(r'vec[234]\s*\(', lines[i]):
                # Replace commas with semicolons
                parts = re.split(r'([^(,]\s*),(\s*[^),])', lines[i])
                if len(parts) > 1:
                    result = parts[0]
                    for j in range(1, len(parts), 3):
                        if j+2 < len(parts):
                            result += parts[j] + ";" + parts[j+1] + parts[j+2]
                        else:
                            result += parts[j]
                    lines[i] = result

        # Reassemble the shader
        text = '\n'.join(lines)

    # Special case for ghosts.glsl
    if filename == "ghosts.glsl":
        fixed_path = os.path.join(fixed_dir, "ghosts_fixed.glsl")

        # Check if fixed version exists
        if not os.path.exists(fixed_path):
            print(f"Creating fixed version of {filename} at {fixed_path}")

            # Create the fixed version
            fixed_content = """// Ghosts shader - Fixed version
// Original by @XorDev

void mainImage(out vec4 O, in vec2 I)
{
    // Time for animation
    float t = iTime;
    // Raymarch iterator
    float i = 0.0;
    // Raymarch depth
    float z = 0.0;
    // Raymarch step size and "Turbulence" frequency
    float d = 0.0;

    // Clear frag color
    O = vec4(0.0, 0.0, 0.0, 0.0);

    // Raymarch loop
    for (i = 0.0; i < 100.0; i += 1.0)
    {
        // Raymarch sample point
        vec3 p = z * normalize(vec3(I+I, 0.0) - iResolution.xyy);
        // Twist with depth
        p.xy *= mat2(cos((z + t) * 0.1 + vec4(0.0, 33.0, 11.0, 0.0)));
        // Scroll forward
        p.z -= 5.0 * t;

        // Turbulence loop
        d = 1.0;
        for (float j = 0.0; j < 4.0; j += 1.0)
        {
            p += cos(p.yzx * d + t) / d;
            d /= 0.7;
        }

        // Distance to irregular gyroid
        d = 0.02 + abs(2.0 - dot(cos(p), sin(p.yzx * 0.6))) / 8.0;
        z += d;

        // Add color and glow falloff
        O += vec4(z / 7.0, 2.0, 3.0, 1.0) / d;
    }

    // Tanh tonemapping
    O = tanh(O * O / 10000000.0);
}"""

            # Write the fixed version to file
            with open(fixed_path, 'w') as f:
                f.write(fixed_content)

        print(f"Using fixed version of {filename} from {fixed_path}")
        text = pathlib.Path(fixed_path).read_text()
        return text

    # General fixes for other shaders with similar patterns to ghosts.glsl
    if "for (O *= i; i++" in text:
        print("Detected shader with compact for-loop syntax, applying fixes...")

        # Fix 1: Extract variable declarations from the for loop
        text = text.replace("for (O *= i; i++", "O = vec4(0.0, 0.0, 0.0, 0.0);\nfor (float i = 0.0; i++")

        # Fix 2: Fix variable declarations with commas
        lines = text.split('\n')
        for i in range(len(lines)):
            # Look for lines with comma-separated declarations like "float t = iTime, i, z, d;"
            if re.search(r'float\s+\w+\s*=.*,', lines[i]):
                # Extract the type
                type_match = re.search(r'(float|vec[234])\s+', lines[i])
                if type_match:
                    type_name = type_match.group(1)
                    # Replace commas with semicolons and type declarations
                    parts = lines[i].split(',')
                    if len(parts) > 1:
                        # First part already has the type
                        result = parts[0].strip()
                        # Add type to other parts
                        for j in range(1, len(parts)):
                            part = parts[j].strip()
                            if j == len(parts) - 1 and ';' in part:
                                part = part.replace(';', '')
                                result += f";\n{type_name} {part};"
                            else:
                                result += f";\n{type_name} {part}"
                        lines[i] = result

        # Reassemble the shader
        text = '\n'.join(lines)

    # General fixes for all shaders - only apply to specific shaders that need it
    if filename == "blackhole_special.glsl":
        # Fix 1: Add missing semicolons after statements
        lines = text.split('\n')
        for i in range(len(lines)):
            line = lines[i].strip()
            if line and not line.endswith(';') and not line.endswith('{') and not line.endswith('}') and not line.startswith('//') and not line.startswith('#'):
                # Check if this is a function declaration or an if/for/while statement
                if not re.search(r'(void|float|vec[234]|int|bool)\s+\w+\s*\(', line) and not re.search(r'(if|for|while)\s*\(', line):
                    lines[i] = lines[i] + ';'

        # Reassemble the shader
        text = '\n'.join(lines)

    return text

def load_snippet(path):
    print(f"Loading shader snippet from: {path}")
    text = pathlib.Path(path).read_text()
    print(f"Shader content length: {len(text)} characters")

    # Preprocess the shader to fix common issues
    text = preprocess_shader(text, path)

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
        logger.info("Shader program compiled successfully")

        # Log available uniforms at debug level only
        try:
            logger.debug(f"Available uniforms: {', '.join(program.uniforms.keys())}")
        except AttributeError:
            logger.debug("Uniforms not accessible via .uniforms attribute")
        
        return program
    except Exception as e:
        logger.error(f"Error compiling shader program: {e}")
        # Only log first few lines at error level
        for i, line in enumerate(src.splitlines()[:20]):
            logger.error(f"{i+1}: {line}")
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
        if 'iFrame' in self.prog:
            self.prog['iFrame'].value = 0

        # Create textures for iChannel uniforms
        self.textures = []
        if 'iChannel0' in self.prog:
            # Use the high-quality noise texture for iChannel0
            noise_path = os.path.join(os.path.dirname(shader_path), "textures", "noise_hq.png")
            # Fall back to regular noise.png if high-quality version doesn't exist
            if not os.path.exists(noise_path):
                noise_path = os.path.join(os.path.dirname(shader_path), "textures", "noise.png")
            if os.path.exists(noise_path):
                try:
                    # Load the noise texture
                    img = Image.open(noise_path).convert("RGBA")
                    w, h = img.size
                    tex = self.ctx.texture((w, h), 4, img.tobytes())
                    tex.build_mipmaps()
                    tex.use(location=0)
                    self.textures.append(tex)
                    print(f"Loaded noise texture from {noise_path} for iChannel0")

                    # Set iChannelResolution if needed
                    if 'iChannelResolution' in self.prog:
                        self.prog['iChannelResolution'].value = ((w, h, 1.0), (1.0, 1.0, 1.0), (1.0, 1.0, 1.0), (1.0, 1.0, 1.0))
                except Exception as e:
                    print(f"Error loading noise texture: {e}")
                    # Fallback to procedural noise
                    noise_size = 256
                    noise_data = np.random.randint(0, 255, (noise_size, noise_size, 4), dtype=np.uint8)
                    tex = self.ctx.texture((noise_size, noise_size), 4, noise_data.tobytes())
                    tex.use(location=0)
                    self.textures.append(tex)
                    print("Created procedural noise texture for iChannel0 (fallback)")
            else:
                # Fallback to procedural noise
                noise_size = 256
                noise_data = np.random.randint(0, 255, (noise_size, noise_size, 4), dtype=np.uint8)
                tex = self.ctx.texture((noise_size, noise_size), 4, noise_data.tobytes())
                tex.use(location=0)
                self.textures.append(tex)
                print(f"Noise texture not found at {noise_path}, using procedural noise")

        # Create framebuffer for offscreen rendering
        self.fbo = self.ctx.framebuffer(
            color_attachments=[self.ctx.texture((width, height), 4)]
        )

        print(f"Shader initialization complete")

    def update_audio_texture(self, audio_texture_path):
        """
        Update the audio texture with a new texture file.

        Args:
            audio_texture_path (str): Path to the audio texture file
        """
        if not os.path.exists(audio_texture_path):
            print(f"Warning: Audio texture file not found: {audio_texture_path}")
            return

        try:
            # Check if we already have an audio texture
            has_audio_texture = False
            for i, tex in enumerate(self.textures):
                if hasattr(tex, 'is_audio_texture') and tex.is_audio_texture:
                    # Replace the existing audio texture
                    tex.release()

                    # Load the new audio texture
                    img = Image.open(audio_texture_path).convert("RGBA")
                    w, h = img.size
                    new_tex = self.ctx.texture((w, h), 4, img.tobytes())
                    new_tex.build_mipmaps()
                    new_tex.use(location=0)  # Use location 0 for audio texture
                    new_tex.is_audio_texture = True
                    self.textures[i] = new_tex
                    has_audio_texture = True
                    break

            if not has_audio_texture and 'iChannel0' in self.prog:
                # Create a new audio texture
                img = Image.open(audio_texture_path).convert("RGBA")
                w, h = img.size
                tex = self.ctx.texture((w, h), 4, img.tobytes())
                tex.build_mipmaps()
                tex.use(location=0)  # Use location 0 for audio texture
                tex.is_audio_texture = True
                self.textures.append(tex)

                # Set iChannelResolution if needed
                if 'iChannelResolution' in self.prog:
                    self.prog['iChannelResolution'].value = ((w, h, 1.0), (1.0, 1.0, 1.0), (1.0, 1.0, 1.0), (1.0, 1.0, 1.0))

        except Exception as e:
            print(f"Error updating audio texture: {e}")

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

        # Update frame counter
        if 'iFrame' in self.prog:
            if not hasattr(self, 'frame_count'):
                self.frame_count = 0
            self.prog['iFrame'].value = self.frame_count
            self.frame_count += 1

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

            # Release texture resources
            if hasattr(self, 'textures'):
                for tex in self.textures:
                    tex.release()

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
