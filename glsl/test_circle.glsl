// Simple test shader to verify the rendering pipeline
// This just draws a colored circle

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    // Normalize coordinates (0..1, 0,0 is bottom-left)
    vec2 uv = fragCoord.xy / iResolution.xy;
    
    // Center and scale coordinates to -1..1 range, 0,0 is center
    vec2 centered_uv = (uv - 0.5) * 2.0;
    
    // Account for aspect ratio so the circle isn't stretched
    centered_uv.x *= iResolution.x / iResolution.y;
    
    // Calculate distance from center
    float dist = length(centered_uv);
    
    // Draw a simple circle
    if (dist < 0.5) {
        // Inside the circle - use a rainbow pattern
        float angle = atan(centered_uv.y, centered_uv.x);
        float normalized_angle = (angle + 3.14159) / (2.0 * 3.14159);
        
        // Create a rainbow color based on the angle
        vec3 color;
        color.r = 0.5 + 0.5 * sin(normalized_angle * 6.28318);
        color.g = 0.5 + 0.5 * sin((normalized_angle + 0.333) * 6.28318);
        color.b = 0.5 + 0.5 * sin((normalized_angle + 0.667) * 6.28318);
        
        fragColor = vec4(color, 1.0);
    } else {
        // Outside the circle - black
        fragColor = vec4(0.0, 0.0, 0.0, 1.0);
    }
}
