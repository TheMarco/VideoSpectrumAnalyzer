# Shader Testing Tool for Audio Visualizer Suite

This tool allows you to test GLSL shaders before using them in the main application. It renders a short preview of the shader and saves it as a video file.

## Usage

```bash
python test_shader.py [shader_path] [options]
```

### List Available Shaders

To list all available shaders in the `glsl` directory:

```bash
python test_shader.py list
```

### Test a Shader

To test a specific shader:

```bash
python test_shader.py glsl/singularity.glsl
```

This will render a 5-second preview of the shader and save it as `output_singularity.mp4`.

### Options

- `--output`, `-o`: Path to save the rendered video (default: `output_<shader_name>.mp4`)
- `--duration`, `-d`: Duration of the video in seconds (default: 5.0)
- `--fps`, `-f`: Frames per second (default: 30)
- `--width`, `-W`: Width of the video (default: 1280)
- `--height`, `-H`: Height of the video (default: 720)
- `--play`, `-p`: Play the video after rendering
- `--verbose`, `-v`: Print detailed information

### Examples

Test a shader with custom settings:

```bash
python test_shader.py glsl/plasma.glsl --duration 3.0 --fps 60 --width 1920 --height 1080
```

Test a shader and play the video after rendering:

```bash
python test_shader.py glsl/gears.glsl --play
```

Save the output to a specific file:

```bash
python test_shader.py glsl/biomine.glsl --output my_test_shader.mp4
```

## Creating New Shaders

When creating new shaders, follow these guidelines:

1. Save your shader files in the `glsl` directory with a `.glsl` extension.
2. Your shader must include a `mainImage` function with the following signature:

```glsl
void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    // Your shader code here
}
```

3. The `fragCoord` parameter provides the pixel coordinates, and `fragColor` is the output color.
4. You can use the following uniforms in your shader:
   - `iResolution`: Resolution of the output image (vec3)
   - `iTime`: Current time in seconds (float)
   - `iMouse`: Mouse position (vec4)
   - `iFrame`: Current frame number (int)
   - `iChannel0` through `iChannel3`: Texture samplers (sampler2D)

5. Test your shader with the testing tool before using it in the main application.

## Shadertoy Compatibility

The shader renderer includes a compatibility layer for Shadertoy shaders. This allows you to use shaders from Shadertoy with minimal modifications. The following features are supported:

1. **Texture samplers**: `iChannel0` through `iChannel3` are available as uniform samplers.
2. **Compatibility functions**: `texture2D()` is available for backward compatibility.
3. **Compatibility variables**: `time`, `mouse`, and `resolution` are available as alternatives to `iTime`, `iMouse`, and `iResolution`.

If you're importing a shader from Shadertoy that doesn't work, check for these common issues:

1. **Missing variable declarations**: Make sure all variables are properly declared.
2. **Texture access**: If the shader uses textures, you may need to provide texture files.
3. **Buffer access**: Shadertoy's multi-pass buffer system is not supported. You'll need to modify shaders that use this feature.

Example of fixing a Shadertoy shader:

```glsl
// Original Shadertoy shader with issues
void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    // This will cause an error because rg is not declared
    vec2 uv = fragCoord.xy / iResolution.xy;
    vec4 tex = texture(iChannel0, uv);
    fragColor = tex * vec4(rg, 0.5, 1.0);
}

// Fixed version
void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    // Properly declare all variables
    vec2 uv = fragCoord.xy / iResolution.xy;
    vec4 tex = texture(iChannel0, uv);
    vec2 rg = uv;  // Define rg variable
    fragColor = tex * vec4(rg, 0.5, 1.0);
}
```

## Pattern-Based Shader Fixing

The Audio Visualizer Suite includes a sophisticated pattern-based shader fixing system that can handle many common issues in GLSL shaders, particularly those from Shadertoy. The system:

1. **Automatically detects problematic patterns** in shaders, such as:
   - Comma-separated variable declarations (`float t = iTime, i, z, d;`)
   - For-loop with initialization and increment in unusual places (`for(O *= i; i++<1e2; O+=...)`)
   - Multiple assignments in one line (`z += d = .03+.1*max(s=3.-abs(p.x), -s*.2);`)
   - Compact math expressions (`p.xy *= mat2(cos(p.y*.5+vec4(0,33,11,0)));`)
   - Missing semicolons and other syntax issues
   - Problematic comments that cause syntax errors

2. **Applies transformations** to fix these patterns:
   - Strips all comments to avoid syntax issues
   - Expands comma-separated declarations into separate lines
   - Restructures for-loops with proper initialization, condition, and increment
   - Separates multiple assignments into individual statements
   - Adds spaces around operators and proper decimal points
   - Adds missing semicolons

3. **Creates fixed versions** in the `glsl/fixed` directory:
   - More readable with proper formatting
   - Compatible with our renderer
   - Automatically used when you run the original shader

These fixes are applied automatically when you run the shader, so you don't need to manually modify the shader files.

### How It Works

When you run a shader using the `render_shader.py` script:

1. The system checks if the shader contains problematic patterns
2. If it does, it creates a fixed version in the `glsl/fixed` directory (if one doesn't already exist)
3. It then uses the fixed version for rendering
4. The original shader file remains unchanged

For particularly complex shaders, the system uses pre-written fixed versions that have been carefully crafted to work correctly with our renderer. This ensures that even the most complex shaders can be rendered properly.

You can also examine these fixed versions to understand how the shader works or to make your own modifications.

## Troubleshooting

If a shader doesn't work correctly despite the automatic fixes, check for these common issues:

1. **Syntax errors**: Make sure your GLSL code is syntactically correct.
2. **Missing mainImage function**: Ensure your shader includes the `mainImage` function.
3. **Performance issues**: If the shader renders very slowly, it might be too complex for real-time use.
4. **Compatibility issues**: Some GLSL features might not be supported by the renderer.

If you encounter any issues, try running the test with the `--verbose` flag to get more detailed information:

```bash
python test_shader.py glsl/your_shader.glsl --verbose
```

## Special Shaders

Some shaders require special handling due to their unique requirements or syntax. The Audio Visualizer Suite includes special renderers for these shaders.

### Universal Shader Renderer

To simplify the process of rendering different types of shaders, we've created a universal shader renderer that automatically detects which renderer to use based on the shader file:

```bash
python render_shader.py glsl/your_shader.glsl --duration 5.0 --play
```

This script will automatically use the appropriate renderer for the shader, ensuring compatibility with all shader types.

### Shield Shader

The shield shader (`glsl/shield.glsl`) uses a special renderer that bypasses the normal shader compilation process. When using the universal renderer, it will automatically detect and use the special renderer for this shader:

```bash
python render_shader.py glsl/shield.glsl --duration 5.0 --play
```

You can also use the dedicated shield shader test script directly:

```bash
python test_shield_shader.py --duration 5.0 --play
```

### Black Hole Shader

The black hole shader (`glsl/blackhole.glsl`) uses a special implementation that replaces the original shader with a more compatible version. This is necessary because the original shader uses complex macros and texture sampling that are difficult to support in our renderer:

```bash
python render_shader.py glsl/blackhole.glsl --duration 5.0 --play
```

The special implementation provides the same visual effect but with a more compatible GLSL syntax.

### Quantum Shader

The quantum shader (`glsl/quantum.glsl`) uses a special implementation that replaces the original shader with a more compatible version. The original shader uses compact syntax with comma-separated operations that are difficult to parse correctly:

```bash
python render_shader.py glsl/quantum.glsl --duration 5.0 --play
```

The special implementation expands the compact syntax into more readable and compatible GLSL code while preserving the visual effect.

### Angel Shader

The angel shader (`glsl/angel.glsl`) uses a special implementation that replaces the original shader with a more compatible version. The original shader uses complex for-loop initialization and multiple operations per line that are difficult to parse correctly:

```bash
python render_shader.py glsl/angel.glsl --duration 5.0 --play
```

The special implementation expands the compact syntax into more readable and compatible GLSL code while preserving the beautiful angel-like effect.

### Nebula Shader

The nebula shader (`glsl/nebula.glsl`) uses a special implementation that replaces the original shader with a more compatible version. The original shader uses compact syntax with uninitialized variables and complex for-loop structures:

```bash
python render_shader.py glsl/nebula.glsl --duration 5.0 --play
```

The special implementation expands the compact syntax into more readable and compatible GLSL code while preserving the beautiful nebula effect.

### Vortex Shaders

The vortex shaders (`glsl/abstractvortext.glsl` and `glsl/newvortext.glsl`) use special implementations that replace the original shaders with more compatible versions. The original shaders use extremely compact syntax with comma-separated operations and complex for-loop structures:

```bash
python render_shader.py glsl/abstractvortext.glsl --duration 5.0 --play
python render_shader.py glsl/newvortext.glsl --duration 5.0 --play
```

The special implementations expand the compact syntax into more readable and compatible GLSL code while preserving the beautiful vortex effects.

### Molten Cube Shader

The molten cube shader (`glsl/molten_cube.glsl`) uses a special implementation that replaces the original shader with a more compatible version. The original shader uses extremely compact syntax with complex operations and a unique ray marching technique:

```bash
python render_shader.py glsl/molten_cube.glsl --duration 5.0 --play
```

The special implementation expands the compact syntax into more readable and compatible GLSL code while preserving the glowing cube effect. This shader demonstrates a clever technique for rendering a cube using axis sorting and rotation.

### Warp Tunnel Shader

The warp tunnel shader (`glsl/warptunnel.glsl`) is a complex shader that creates a stunning tunnel effect with reflections and lighting. The original shader uses advanced ray marching techniques and complex mathematical operations:

```bash
python render_shader.py glsl/warptunnel.glsl --duration 5.0 --play
```

The special implementation simplifies some of the texture operations while preserving the core tunnel effect. This shader demonstrates advanced techniques for creating 3D tunnel effects with reflections and lighting.

### Optical Deconstruction Shader

The optical deconstruction shader (`glsl/optical_deconstruction.glsl`) is a particularly complex shader based on the Optical-Circuit demo scene 5. It uses advanced ray marching techniques and complex mathematical operations:

```bash
python render_shader.py glsl/optical_deconstruction.glsl --duration 5.0 --play
```

The special implementation completely rewrites the shader with proper syntax and structure while preserving the stunning visual effect of the original. This shader is computationally intensive and may render more slowly than other shaders.

### Options

The universal shader renderer supports the same options as the regular test script:

- `--output`, `-o`: Path to save the rendered video (default: `output_<shader_name>.mp4`)
- `--duration`, `-d`: Duration of the video in seconds (default: 5.0)
- `--fps`, `-f`: Frames per second (default: 30)
- `--width`, `-W`: Width of the video (default: 1280)
- `--height`, `-H`: Height of the video (default: 720)
- `--play`, `-p`: Play the video after rendering
- `--verbose`, `-v`: Print detailed information

### Video Format

The renderer creates MP4 videos that are compatible with QuickTime Player on macOS. The videos use the following settings:

- H.264 codec with Main profile
- Level 4.0 for maximum compatibility
- Medium preset for a good balance of quality and file size
- High quality (CRF 17)
- Fast start optimization for better streaming
- Standard MP4 v2 container format

## Shader Fixer Utility

The Audio Visualizer Suite includes a shader fixer utility that can automatically fix common issues in GLSL shaders, particularly those from Shadertoy. This tool can help you quickly adapt shaders that don't work with our renderer.

### Usage

```bash
python fix_shader.py [shader_path] [options]
```

### Options

- `--output`, `-o`: Path to save the fixed shader (default: overwrite input)
- `--no-backup`, `-n`: Don't create a backup of the original file
- `--verbose`, `-v`: Print detailed information

### Examples

Fix a shader and save the result to a new file:

```bash
python fix_shader.py glsl/broken_shader.glsl --output glsl/fixed_shader.glsl
```

Fix a shader in place (with automatic backup):

```bash
python fix_shader.py glsl/broken_shader.glsl
```

### Common Fixes

The shader fixer utility can automatically fix these common issues:

1. **Trailing code**: Removes any code after the closing brace of the `mainImage` function
2. **Variable declarations**: Fixes comma-separated declarations
3. **For loops**: Fixes for loops with missing initialization
4. **Parameter names**: Standardizes parameter names in the `mainImage` function
5. **Shorthand operators**: Replaces shorthand operators with full expressions
6. **Missing semicolons**: Adds missing semicolons at the end of lines
7. **Float precision**: Adds explicit float precision for numbers
8. **Vector construction**: Fixes vector construction from other vectors

For more complex issues, you may need to manually edit the shader after running the fixer.
