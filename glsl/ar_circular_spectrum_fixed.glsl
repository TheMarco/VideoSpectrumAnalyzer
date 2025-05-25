// Extremely Simple Circular Spectrum Analyzer with Circles
// By Marco van Hylckama Vlieg

// Forward declaration of uniforms
uniform int uNumBars;           // Number of bars around the circle
uniform int uSegmentsPerBar;    // Number of segments per bar
uniform float uInnerRadius;     // Inner radius of the circle (0-1)
uniform float uOuterRadius;     // Outer radius of the circle (0-1)
uniform float uBarWidth;        // Width of bars (0-1, where 1 means bars touch)
uniform float uSensitivity;     // Sensitivity control
uniform vec3 uSegmentColor;     // Color for all lit segments
uniform float uDebugMode;       // Debug mode (0=off, 1=on)

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    // Constants
    const float PI = 3.14159265359;

    // Get parameters from uniforms with defaults
    int NUM_BARS = max(uNumBars, 36);
    int SEGMENTS_PER_BAR = max(uSegmentsPerBar, 15);
    float INNER_RADIUS = max(uInnerRadius, 0.2);
    float OUTER_RADIUS = max(uOuterRadius, 0.4);
    float BAR_WIDTH = max(uBarWidth, 0.8);
    float SENSITIVITY = max(uSensitivity, 1.0);
    vec3 SEGMENT_COLOR = max(uSegmentColor, vec3(1.0));

    // Start angle offset (bottom of circle)
    const float START_ANGLE = 3.0 * PI / 2.0;

    // Normalize coordinates
    vec2 uv = fragCoord.xy / iResolution.xy;

    // Get background color
    vec4 bg_color = texture(iChannel1, uv);

    // Center coordinates
    vec2 centered = (uv - 0.5) * 2.0;

    // Fix aspect ratio
    centered.x *= iResolution.x / iResolution.y;

    // Convert to polar coordinates
    float radius = length(centered);
    float angle = atan(centered.y, centered.x);

    // Normalize radius
    float r_norm = radius / 2.0;

    // Debug mode - show a simple colored ring
    if (uDebugMode > 0.5) {
        if (r_norm >= INNER_RADIUS && r_norm <= OUTER_RADIUS) {
            // Inside the ring - show a rainbow pattern
            float hue = (angle + PI) / (2.0 * PI);
            vec3 color = vec3(
                0.5 + 0.5 * cos(hue * 6.28318),
                0.5 + 0.5 * cos((hue + 0.33) * 6.28318),
                0.5 + 0.5 * cos((hue + 0.67) * 6.28318)
            );
            fragColor = vec4(color, 1.0);
        } else {
            // Outside the ring - show background
            fragColor = bg_color;
        }
        return;
    }

    // Check if we're in the ring area
    if (r_norm < INNER_RADIUS || r_norm > OUTER_RADIUS) {
        fragColor = bg_color;
        return;
    }

    // Calculate bar index based on angle
    float angle_0_2PI = angle + PI;
    float final_angle = mod(angle_0_2PI + START_ANGLE, 2.0 * PI);
    float normalized_angle = final_angle / (2.0 * PI);
    int bar_index = int(floor(normalized_angle * float(NUM_BARS)));

    // Get audio data for this bar
    float amplitude;

    // Use test pattern if debug mode is enabled (0.3-0.5 range)
    if (uDebugMode > 0.3 && uDebugMode < 0.5) {
        // Create a test pattern where every 4th bar is fully lit
        if (bar_index % 4 == 0) {
            amplitude = 1.0;  // Full amplitude
        } else if (bar_index % 4 == 1) {
            amplitude = 0.75;  // 75% amplitude
        } else if (bar_index % 4 == 2) {
            amplitude = 0.5;  // 50% amplitude
        } else {
            amplitude = 0.25;  // 25% amplitude
        }
    } else {
        // Normal mode - get amplitude from audio texture
        float freq_pos = float(bar_index) / float(NUM_BARS);
        amplitude = texture(iChannel0, vec2(freq_pos, 0.0)).x * SENSITIVITY;
        amplitude = clamp(amplitude, 0.0, 1.0);
    }

    // Calculate how many segments should be lit
    int lit_segments = int(floor(amplitude * float(SEGMENTS_PER_BAR)));

    // Calculate segment height
    float total_radius = OUTER_RADIUS - INNER_RADIUS;
    float segment_height = total_radius / float(SEGMENTS_PER_BAR);

    // Calculate bar angle
    float bar_angle = (float(bar_index) + 0.5) * (2.0 * PI / float(NUM_BARS));
    bar_angle = mod(bar_angle + START_ANGLE, 2.0 * PI);

    // Check each segment in this bar
    for (int i = 0; i < SEGMENTS_PER_BAR; i++) {
        // Only process lit segments and the innermost segment (always lit)
        if (i <= lit_segments || i == 0) {
            // Calculate segment radius
            float segment_radius = INNER_RADIUS + (float(i) + 0.5) * segment_height;

            // Calculate circle center
            vec2 circle_center = vec2(
                segment_radius * cos(bar_angle),
                segment_radius * sin(bar_angle)
            );

            // Calculate distance to circle center
            float dist = length(centered - circle_center);

            // Circle radius (make it MUCH larger to be clearly visible)
            float circle_radius = segment_height * 0.7 * BAR_WIDTH;

            // If inside circle, color it
            if (dist <= circle_radius) {
                fragColor = vec4(SEGMENT_COLOR, 1.0);
                return;
            }
        }
    }

    // If not inside any circle, show background
    fragColor = bg_color;
}
