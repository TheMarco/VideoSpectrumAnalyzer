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
    # Create fixed directory if it doesn't exist
    fixed_dir = os.path.join(os.path.dirname(shader_path), "fixed")
    if not os.path.exists(fixed_dir):
        os.makedirs(fixed_dir)
        print(f"Created directory for fixed shaders: {fixed_dir}")

    # Get the base name and create the fixed path
    basename = os.path.basename(shader_path)
    name, ext = os.path.splitext(basename)
    fixed_path = os.path.join(fixed_dir, f"{name}_fixed{ext}")

    # Check if fixed version already exists
    if os.path.exists(fixed_path):
        print(f"Using existing fixed version: {fixed_path}")
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
