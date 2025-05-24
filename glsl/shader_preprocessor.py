#!/usr/bin/env python3
"""
Shader Preprocessor for Audio Visualizer Suite

This module provides functions to preprocess GLSL shaders to make them compatible
with the Audio Visualizer Suite renderer. It identifies common patterns in shaders
and transforms them into more compatible forms.
"""
import os
import re
import pathlib

def fix_comma_separated_declarations(text):
    """
    Fix comma-separated variable declarations.

    Example:
        float t = iTime, i, z, d;

    Becomes:
        float t = iTime;
        float i = 0.0;
        float z = 0.0;
        float d = 0.0;
    """
    # Find lines with comma-separated declarations
    lines = text.split('\n')
    for i in range(len(lines)):
        # Look for lines with comma-separated declarations
        for type_name in ['float', 'vec2', 'vec3', 'vec4', 'int', 'bool']:
            pattern = rf'{type_name}\s+\w+\s*=.*,.*?;'
            if re.search(pattern, lines[i]):
                # Extract the type
                type_match = re.search(rf'({type_name})\s+', lines[i])
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
                        break  # Only apply one type fix per line

            # Look for lines with comma-separated declarations without initialization
            pattern = rf'{type_name}\s+\w+\s*,.*?;'
            if re.search(pattern, lines[i]):
                # Extract the type
                type_match = re.search(rf'({type_name})\s+', lines[i])
                if type_match:
                    type_name = type_match.group(1)
                    # Replace commas with semicolons and type declarations
                    line = lines[i].rstrip(';')
                    parts = line.split(',')
                    if len(parts) > 1:
                        result = parts[0].strip() + ";"
                        for j in range(1, len(parts)):
                            part = parts[j].strip()
                            result += f"\n{type_name} {part};"
                        lines[i] = result
                        break  # Only apply one type fix per line

    return '\n'.join(lines)

def fix_for_loop_initialization(text):
    """
    Fix for-loop with initialization and increment in unusual places.

    Example:
        for(O *= i; i++<1e2; O+=...)

    Becomes:
        O = vec4(0.0, 0.0, 0.0, 0.0);
        for(float i = 0.0; i < 100.0; i += 1.0) {
            // loop body
            O += ...;
        }
    """
    # Fix for-loops with O *= i initialization
    if "for (O *= i;" in text or "for(O *= i;" in text:
        text = re.sub(
            r'for\s*\(\s*O\s*\*=\s*i\s*;',
            'O = vec4(0.0, 0.0, 0.0, 0.0);\nfor(float i = 0.0;',
            text
        )

    # Fix i++<1e2 condition
    text = re.sub(
        r'i\+\+\s*<\s*1e2',
        'i < 100.0; i += 1.0',
        text
    )

    # Fix other scientific notation
    text = re.sub(
        r'(\d+)e(\d+)',
        lambda m: str(float(m.group(0))),
        text
    )

    # Fix increment in the third part of for-loop
    # This is more complex and might need specific handling

    return text

def fix_multiple_assignments(text):
    """
    Fix multiple assignments in one line.

    Example:
        z += d = .03+.1*max(s=3.-abs(p.x), -s*.2);

    Becomes:
        s = 3.0 - abs(p.x);
        d = 0.03 + 0.1 * max(s, -s * 0.2);
        z += d;
    """
    # This is a complex transformation that might need specific handling
    # for different patterns

    # Fix s=3.-abs(p.x) pattern
    text = re.sub(
        r's\s*=\s*3\.\s*-\s*abs\s*\(\s*p\.x\s*\)',
        's = 3.0 - abs(p.x)',
        text
    )

    # Fix z += d = ... pattern
    lines = text.split('\n')
    for i in range(len(lines)):
        if re.search(r'z\s*\+=\s*d\s*=', lines[i]):
            # Extract the right side of the assignment
            match = re.search(r'z\s*\+=\s*d\s*=\s*(.+);', lines[i])
            if match:
                right_side = match.group(1)
                lines[i] = f"d = {right_side};\nz += d;"

    return '\n'.join(lines)

def fix_compact_math(text):
    """
    Fix compact math expressions.

    Example:
        p.xy *= mat2(cos(p.y*.5+vec4(0,33,11,0)));

    Becomes:
        p.xy *= mat2(cos(p.y * 0.5 + vec4(0.0, 33.0, 11.0, 0.0)));
    """
    # Add spaces around operators
    text = re.sub(r'([+\-*/])', r' \1 ', text)

    # Fix missing .0 in float literals
    text = re.sub(r'(\d+)\.([^0-9])', r'\1.0\2', text)
    text = re.sub(r'([^0-9])\.(\d+)', r'\1 0.\2', text)

    # Fix vec2/vec3/vec4 constructors
    for vec_type in ['vec2', 'vec3', 'vec4']:
        # Find vec constructor calls
        pattern = rf'{vec_type}\s*\(([^)]*)\)'
        for match in re.finditer(pattern, text):
            args = match.group(1)
            # Add .0 to integer literals in the arguments
            fixed_args = re.sub(r'(\d+)(?!\.\d*|\d*\.)', r'\1.0', args)
            # Add spaces after commas
            fixed_args = re.sub(r',\s*', ', ', fixed_args)
            # Replace in the original text
            text = text.replace(match.group(0), f"{vec_type}({fixed_args})")

    return text

def fix_missing_semicolons(text):
    """
    Fix missing semicolons at the end of statements.
    """
    lines = text.split('\n')
    for i in range(len(lines)):
        line = lines[i].strip()
        if line and not line.endswith(';') and not line.endswith('{') and not line.endswith('}') and not line.startswith('//') and not line.startswith('#'):
            # Check if this is a function declaration or an if/for/while statement
            if not re.search(r'(void|float|vec[234]|int|bool)\s+\w+\s*\(', line) and not re.search(r'(if|for|while)\s*\(', line):
                lines[i] = lines[i] + ';'

    return '\n'.join(lines)

def strip_comments(text):
    """
    Strip all comments from GLSL code.

    Args:
        text (str): The shader source code

    Returns:
        str: The shader source code without comments
    """
    import re

    # First, remove multi-line comments (/* ... */)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)

    # Then, remove single-line comments (// ...)
    text = re.sub(r'//.*?$', '', text, flags=re.MULTILINE)

    return text

def fix_shader(text, shader_path=""):
    """
    Apply all fixes to a shader.

    Args:
        text (str): The shader source code
        shader_path (str): Path to the shader file (for debugging)

    Returns:
        str: The fixed shader source code
    """
    print(f"Applying pattern-based fixes to shader: {shader_path}")

    # First, strip all comments
    text = strip_comments(text)

    # Apply fixes in sequence
    text = fix_comma_separated_declarations(text)
    text = fix_for_loop_initialization(text)
    text = fix_multiple_assignments(text)
    text = fix_compact_math(text)
    text = fix_missing_semicolons(text)

    return text

def create_fixed_shader(shader_path):
    """
    Create a fixed version of a shader.

    Args:
        shader_path (str): Path to the shader file

    Returns:
        str: Path to the fixed shader file
    """
    # Create the fixed directory if it doesn't exist
    fixed_dir = os.path.join(os.path.dirname(shader_path), "fixed")
    os.makedirs(fixed_dir, exist_ok=True)

    # Get the shader filename
    basename = os.path.basename(shader_path)
    name, ext = os.path.splitext(basename)
    fixed_path = os.path.join(fixed_dir, f"{name}_fixed{ext}")

    # Special case for starnest.glsl
    if basename == "starnest.glsl":
        # Create a completely new fixed version
        fixed_text = """// Star Nest by Pablo Roman Andrioli - Fixed version
// License: MIT
// Based on https://www.shadertoy.com/view/XlfGRj

// Star Nest parameters
#define iterations 17
#define formuparam 0.53
#define volsteps 20
#define stepsize 0.1
#define zoom 0.800
#define tile 0.850
#define speed 0.010
#define brightness 0.0015
#define darkmatter 0.300
#define distfading 0.730
#define saturation 0.850

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    // Get coords and direction
    vec2 uv = fragCoord.xy/iResolution.xy-.5;
    uv.y *= iResolution.y/iResolution.x;
    vec3 dir = vec3(uv*zoom,1.);
    float t = iTime*speed+.25;

    // Mouse rotation
    float a1 = .5+iMouse.x/iResolution.x*2.;
    float a2 = .8+iMouse.y/iResolution.y*2.;
    mat2 rot1 = mat2(cos(a1),sin(a1),-sin(a1),cos(a1));
    mat2 rot2 = mat2(cos(a2),sin(a2),-sin(a2),cos(a2));
    dir.xz *= rot1;
    dir.xy *= rot2;
    vec3 from = vec3(1.,.5,0.5);
    from += vec3(t*2.,t,-2.);
    from.xz *= rot1;
    from.xy *= rot2;

    // Volumetric rendering
    float s = 0.1;
    float fade = 1.;
    vec3 v = vec3(0.);

    for (int r=0; r<volsteps; r++) {
        vec3 p = from + s*dir*.5;
        p = abs(vec3(tile) - mod(p, vec3(tile*2.))); // tiling fold
        float pa = 0.;
        float a = 0.;

        for (int i=0; i<iterations; i++) {
            p = abs(p)/dot(p,p) - formuparam; // the magic formula
            a += abs(length(p)-pa); // absolute sum of average change
            pa = length(p);
        }

        float dm = max(0., darkmatter-a*a*.001); // dark matter
        a *= a*a; // add contrast

        if (r>6) fade *= 1.-dm; // dark matter, don't render near

        v += fade;
        v += vec3(s, s*s, s*s*s*s)*a*brightness*fade; // coloring based on distance
        fade *= distfading; // distance fading
        s += stepsize;
    }

    v = mix(vec3(length(v)), v, saturation); // color adjust
    fragColor = vec4(v*.01, 1.);
}"""

        # Write the fixed shader
        with open(fixed_path, 'w') as f:
            f.write(fixed_text)

        print(f"Created fixed version for starnest.glsl: {fixed_path}")
        return fixed_path

    # Special case for starbirth.glsl
    elif basename == "starbirth.glsl":
        # Check if fixed version already exists
        if os.path.exists(fixed_path):
            print(f"Using existing fixed version for starbirth.glsl: {fixed_path}")
            return fixed_path

        # Create a simplified fixed version
        fixed_text = """// StarBirth: Fully AI vibe coded simulation of Hubble telescope images
// by Marco van Hylckama Vlieg (@AIandDesign on X / YouTube)
// Fixed version for Video Spectrum Analyzer

#define PI 3.14159265359
#define ITERATIONS_FBM   8
#define ITERATIONS_RAYMARCH 8
#define TIME_OFFSET 80

// Spatial-Density Starfield Settings
#define CELL_SIZE    40.0      // Size of grid cells for star placement
#define DENSITY      0.70      // Base probability a cell contains a star
#define DENSITY_VAR  0.45      // Variation in density across regions
#define REGION_CELLS 8.0       // Number of cells per density region
#define MAX_RADIUS   5.0       // Max radius for SMALL stars (in pixels)
#define BRIGHT_BOOST 1.0       // Brightness multiplier for SMALL stars

// Large Star Settings
#define BIG_STAR_THRESHOLD 0.93 // Probability threshold for a star to be large (0.0-1.0)
#define BIG_STAR_MIN_RADIUS 10.0 // Min radius for LARGE star bloom (in pixels)
#define BIG_STAR_MAX_RADIUS 40.0 // Max radius for LARGE star bloom (in pixels)
#define BIG_STAR_BRIGHT_MIN 0.7  // Min brightness multiplier for LARGE stars
#define BIG_STAR_BRIGHT_MAX 2.8  // Max brightness multiplier for LARGE stars
#define BIG_STAR_COLOR_WARM vec3(1.0, 0.8, 0.5) // Color option 1 for large stars
#define BIG_STAR_COLOR_COOL vec3(0.7, 0.8, 1.0) // Color option 2 for large stars

// Additional Fixed Large Stars Settings
#define EXTRA_STAR_1_POS vec2(-0.2, 0.15) // Position in uv space relative to center
#define EXTRA_STAR_1_RADIUS 0.13          // Radius in uv space
#define EXTRA_STAR_1_COLOR vec3(1.0, 0.9, 0.7) // Color (warm white)
#define EXTRA_STAR_1_BRIGHTNESS 1.2         // Brightness multiplier

#define EXTRA_STAR_2_POS vec2(0.25, -0.1) // Position in uv space relative to center
#define EXTRA_STAR_2_RADIUS 0.09          // Radius in uv space
#define EXTRA_STAR_2_COLOR vec3(0.8, 0.9, 1.0) // Color (cool blueish)
#define EXTRA_STAR_2_BRIGHTNESS 1.2         // Brightness multiplier

// Rotation Helper
mat2 rotate(float a) {
    float s = sin(a);
    float c = cos(a);
    return mat2(c, -s, s, c);
}

// Hash Helpers
float hash1(float n) {
    return fract(sin(n) * 43758.5453);
}

vec2 hash2(vec2 p) {
    return fract(
        sin(vec2(
            dot(p, vec2(127.1, 311.7)),
            dot(p, vec2(269.5, 183.3))
        )) * 43758.5453
    );
}

float hash(vec2 p) {
    p = fract(p * vec2(123.34, 345.45));
    p += dot(p, p + 34.345);
    return fract(p.x * p.y);
}

// 2D Value Noise & FBM
float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f*f*(3.0 - 2.0*f);
    float a = hash(i + vec2(0.0,0.0));
    float b = hash(i + vec2(1.0,0.0));
    float c = hash(i + vec2(0.0,1.0));
    float d = hash(i + vec2(1.0,1.0));
    return mix(mix(a,b,f.x), mix(c,d,f.x), f.y);
}

float fbm(vec2 p, float to) {
    float v = 0.0;
    float amp = 0.5;
    float freq = 1.0;
    p += to * 0.1;
    for (int i = 0; i < ITERATIONS_FBM; i++) {
        v += amp * noise(p * freq);
        freq *= 2.0;
        amp *= 0.5;
    }
    return v;
}

// Main Render Function
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // Normalize coordinates
    vec2 uv = (2.0*fragCoord - iResolution.xy)
              / min(iResolution.x, iResolution.y);
    float time = (iTime + float(TIME_OFFSET)) * 0.2;

    float distToCenter = length(uv);
    vec3 finalColor = vec3(0.005, 0.0, 0.015);

    // Central Glowing Core
    float core = pow(
        smoothstep(0.15, 0.0, distToCenter),
        3.0
    );
    core += pow(
        smoothstep(0.05, 0.0, distToCenter),
        5.0
    ) * 0.5;
    finalColor += vec3(1.0,0.8,0.5) * core * 2.0;
    float bCore = core; // Use bCore for masking nebula layers

    // Simplified God Rays / Volumetric Shafts
    float shafts = 0.0;
    if (distToCenter > 0.01) {
        vec2 dir = normalize(uv);
        for (int i = 0; i < ITERATIONS_RAYMARCH; i++) {
            float t = float(i)/float(ITERATIONS_RAYMARCH)*0.8;
            vec2 p = uv - dir*t*(0.5+0.5*sin(time));
            vec2 qr = vec2(
                fbm(p*2.0 + vec2(1.7,8.2), time*0.5),
                fbm(p*2.0 + vec2(5.4,3.1), time*0.5 + 0.1)
            );
            float d = fbm(p*3.0 + qr*0.5, time*0.3);
            d = smoothstep(0.4,0.6,d);
            shafts += d * (1.0 - t) * 0.15;
        }
    }
    shafts = pow(shafts,2.0) * (1.0 - smoothstep(0.0,1.5,distToCenter));
    finalColor += vec3(0.8,0.6,0.3) * shafts * (0.5 + bCore*0.5);

    // Add the two additional large stars
    // Star 1
    float dist1 = length(uv - EXTRA_STAR_1_POS);
    float bloom1 = pow(smoothstep(EXTRA_STAR_1_RADIUS * 0.7, 0.0, dist1), 3.0);
    bloom1 += pow(smoothstep(EXTRA_STAR_1_RADIUS * 0.4, 0.0, dist1), 5.0) * 0.5;
    finalColor += EXTRA_STAR_1_COLOR * bloom1 * EXTRA_STAR_1_BRIGHTNESS;

    // Star 2
    float dist2 = length(uv - EXTRA_STAR_2_POS);
    float bloom2 = pow(smoothstep(EXTRA_STAR_2_RADIUS * 0.7, 0.0, dist2), 3.0);
    bloom2 += pow(smoothstep(EXTRA_STAR_2_RADIUS * 0.4, 0.0, dist2), 5.0) * 0.5;
    finalColor += EXTRA_STAR_2_COLOR * bloom2 * EXTRA_STAR_2_BRIGHTNESS;

    // Final Gamma & Clamping
    finalColor = pow(finalColor, vec3(0.9));
    finalColor = clamp(finalColor, 0.0, 1.0);

    fragColor = vec4(finalColor, 1.0);
}"""

        # Write the fixed shader
        with open(fixed_path, 'w') as f:
            f.write(fixed_text)

        print(f"Created fixed version for starbirth.glsl: {fixed_path}")
        return fixed_path

    # Read the shader source
    text = pathlib.Path(shader_path).read_text()

    # Special case for known complex shaders
    if basename in ["abstractvortext.glsl", "newvortext.glsl", "molten_cube.glsl", "warptunnel.glsl", "cloudten.glsl"]:
        # For shaders that need a completely rewritten version
        if basename in ["molten_cube.glsl", "warptunnel.glsl", "cloudten.glsl"]:
            # Use the existing fixed version
            with open(fixed_path, 'r') as f:
                fixed_text = f.read()
            return fixed_path
        # For vortex shaders, use a common implementation
        elif basename in ["abstractvortext.glsl", "newvortext.glsl"]:
            shader_title = "Abstract Vortex" if basename == "abstractvortext.glsl" else "New Vortex"
        fixed_text = f"""// {shader_title} shader - Fixed version
// Original by @XorDev

void mainImage(out vec4 O, vec2 I)
{{
    // Clear fragcolor
    O = vec4(0.0, 0.0, 0.0, 0.0);

    // Resolution for scaling
    vec2 v = iResolution.xy;

    // Center and scale
    vec2 p = (I + I - v) / v.y;

    // Loop through arcs (i=radius, l=length)
    for(float i = 0.2, l = 0.0; i < 1.0; i += 0.05)
    {{
        // Compute polar coordinate position
        v = vec2(mod(atan(p.y, p.x) + i + i * iTime, 6.28) - 3.14, 1.0) * length(p) - i;

        // Clamp to light length
        float temp = v.x + i;
        v.x -= clamp(temp, -i, i);

        // Calculate length
        l = length(v) + 0.003;

        // Pick color for each arc and shade/attenuate light
        O += (cos(i * 5.0 + vec4(0.0, 1.0, 2.0, 3.0)) + 1.0) * (1.0 + v.y / l) / l;
    }}

    // Tanh tonemap
    O = tanh(O / 100.0);
}}"""
    else:
        # Apply automatic fixes for other shaders
        fixed_text = fix_shader(text, shader_path)

    # Write the fixed shader
    with open(fixed_path, 'w') as f:
        f.write(fixed_text)

    print(f"Created fixed version: {fixed_path}")
    return fixed_path

def get_fixed_shader_path(shader_path):
    """
    Get the path to the fixed version of a shader.

    Args:
        shader_path (str): Path to the original shader file

    Returns:
        str: Path to the fixed shader file
    """
    fixed_dir = os.path.join(os.path.dirname(shader_path), "fixed")
    basename = os.path.basename(shader_path)
    name, ext = os.path.splitext(basename)
    return os.path.join(fixed_dir, f"{name}_fixed{ext}")

def is_problematic_shader(shader_path):
    """
    Check if a shader is likely to be problematic.

    Args:
        shader_path (str): Path to the shader file

    Returns:
        bool: True if the shader is likely to be problematic
    """
    # Check if it's a known problematic shader
    basename = os.path.basename(shader_path)
    if basename in ["starnest.glsl", "starbirth.glsl"]:
        return True

    # Read the shader source
    text = pathlib.Path(shader_path).read_text()

    # Check for common problematic patterns
    patterns = [
        r'for\s*\(\s*O\s*\*=',  # for(O *= i;
        r'i\+\+\s*<\s*1e',      # i++<1e2
        r'float\s+\w+\s*=.*,',  # float t = iTime, i, z, d;
        r'z\s*\+=\s*d\s*=',     # z += d = ...
        r's\s*=\s*3\.\s*-\s*abs' # s=3.-abs(p.x)
    ]

    for pattern in patterns:
        if re.search(pattern, text):
            return True

    return False

if __name__ == "__main__":
    # Test the preprocessor
    import sys
    if len(sys.argv) > 1:
        shader_path = sys.argv[1]
        fixed_path = create_fixed_shader(shader_path)
        print(f"Fixed shader saved to: {fixed_path}")
    else:
        print("Usage: python shader_preprocessor.py <shader_path>")
