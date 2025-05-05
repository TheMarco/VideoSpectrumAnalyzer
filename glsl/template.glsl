// Template Shader for Audio Visualizer Suite
// This is a simple template you can use as a starting point for creating new shaders.

// Uniforms provided by the renderer:
// iResolution: Resolution of the output image (vec3)
// iTime: Current time in seconds (float)
// iMouse: Mouse position (vec4)
// iFrame: Current frame number (int)

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    // Normalized pixel coordinates (from 0 to 1)
    vec2 uv = fragCoord / iResolution.xy;
    
    // Time-based animation
    float time = iTime * 0.5;
    
    // Create a gradient background
    vec3 color1 = vec3(0.1, 0.2, 0.3);
    vec3 color2 = vec3(0.3, 0.1, 0.2);
    vec3 background = mix(color1, color2, uv.y + sin(time) * 0.2);
    
    // Add some animated circles
    float circle1 = length(uv - vec2(0.5 + sin(time * 0.7) * 0.3, 0.5 + cos(time * 0.5) * 0.2));
    float circle2 = length(uv - vec2(0.5 + cos(time * 0.8) * 0.3, 0.5 + sin(time * 0.6) * 0.2));
    
    // Create glowing circles
    vec3 glow1 = vec3(0.8, 0.4, 0.2) * 0.5 / (circle1 * 8.0);
    vec3 glow2 = vec3(0.2, 0.4, 0.8) * 0.5 / (circle2 * 8.0);
    
    // Combine everything
    vec3 finalColor = background + glow1 + glow2;
    
    // Output to screen
    fragColor = vec4(finalColor, 1.0);
}
