// Circular Spectrum Analyzer - Simplified Version
// By Marco van Hylckama Vlieg

// Forward declaration of uniforms
uniform int uNumBars;           // Number of bars around the circle
uniform int uSegmentsPerBar;    // Number of segments per bar
uniform float uInnerRadius;     // Inner radius of the circle (0-1)
uniform float uOuterRadius;     // Outer radius of the circle (0-1)
uniform float uBarWidth;        // Width of bars (0-1, where 1 means bars touch)
uniform float uDebugMode;       // Debug mode (0=off, 1=on)
uniform float uTime;            // Current time in seconds (for animation)
uniform float uSegmentSpacing;  // Spacing between segments in pixels

// Sensitivity and gain uniforms
uniform float uOverallMasterGain;
uniform float uFreqGainMinMult;
uniform float uFreqGainMaxMult;
uniform float uFreqGainCurvePower;
uniform float uBarHeightPower;
uniform float uAmplitudeCompressionPower;

// Color uniforms
uniform vec3 uColorLitBright;   // Color for all segments
uniform float uLitBrightnessMult; // Brightness multiplier for lit segments

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    // --- Constants ---
    const float PI = 3.14159265359;
    int NUM_BARS = max(uNumBars, 1);
    int SEGMENTS_PER_BAR = max(uSegmentsPerBar, 1);
    float INNER_RADIUS = max(uInnerRadius, 0.01);
    float OUTER_RADIUS = max(uOuterRadius, INNER_RADIUS + 0.01);
    float BAR_WIDTH = clamp(uBarWidth, 0.1, 1.0);
    float SEGMENT_SPACING = max(uSegmentSpacing, 0.0);

    // Sensitivity settings
    float OVERALL_GAIN = max(uOverallMasterGain, 0.1);
    float FREQ_GAIN_MIN = max(uFreqGainMinMult, 0.1);
    float FREQ_GAIN_MAX = max(uFreqGainMaxMult, 0.1);
    float FREQ_CURVE_POWER = max(uFreqGainCurvePower, 0.1);
    float BAR_HEIGHT_POWER = max(uBarHeightPower, 0.1);
    float AMPLITUDE_POWER = max(uAmplitudeCompressionPower, 0.1);

    // Color settings
    vec3 SEGMENT_COLOR = uColorLitBright;
    float BRIGHTNESS_MULT = max(uLitBrightnessMult, 0.1);

    // --- Coordinate Mapping ---
    vec2 uv = fragCoord.xy / iResolution.xy;
    vec4 bg_color = texture(iChannel1, uv);

    // Center coordinates
    vec2 centered = (uv - 0.5) * 2.0;
    centered.x *= iResolution.x / iResolution.y; // Aspect correction

    // Convert to polar coordinates
    float radius = length(centered) / 2.0;
    float angle = atan(centered.y, centered.x);

    // Check if we're in the ring
    if (radius < INNER_RADIUS || radius > OUTER_RADIUS) {
        fragColor = bg_color;
        return;
    }

    // Debug mode
    if (uDebugMode > 0.5) {
        // Show a rainbow ring
        float hue = (angle + PI) / (2.0 * PI);
        vec3 color = vec3(
            0.5 + 0.5 * sin(hue * 6.28318 + 0.0),
            0.5 + 0.5 * sin(hue * 6.28318 + 2.0944),
            0.5 + 0.5 * sin(hue * 6.28318 + 4.18879)
        );
        fragColor = vec4(color, 1.0);
        return;
    }

    // Determine bar index
    float normalized_angle = mod(angle + PI, 2.0 * PI) / (2.0 * PI);
    int bar_index = int(floor(normalized_angle * float(NUM_BARS)));

    // Determine segment index
    float normalized_radius = (radius - INNER_RADIUS) / (OUTER_RADIUS - INNER_RADIUS);
    int segment_index = int(floor(normalized_radius * float(SEGMENTS_PER_BAR)));

    // Apply segment spacing
    float pixel_to_normalized = 2.0 / min(iResolution.x, iResolution.y);
    float spacing = pixel_to_normalized * SEGMENT_SPACING;
    float segment_height = (OUTER_RADIUS - INNER_RADIUS) / float(SEGMENTS_PER_BAR);
    float segment_with_spacing = segment_height - spacing;

    // Check if we're in the spacing
    float segment_pos = float(segment_index) / float(SEGMENTS_PER_BAR);
    float segment_fract = fract(normalized_radius * float(SEGMENTS_PER_BAR));
    if (segment_fract > segment_with_spacing / segment_height) {
        fragColor = bg_color;
        return;
    }

    // Get audio data
    float freq_pos = pow(float(bar_index) / float(NUM_BARS - 1), 1.7);
    float amplitude = texture(iChannel0, vec2(freq_pos, 0.0)).x;

    // Process amplitude
    float processed = pow(amplitude, AMPLITUDE_POWER);
    float bar_norm = float(bar_index) / float(NUM_BARS - 1);
    float curved_norm = pow(bar_norm, FREQ_CURVE_POWER);
    float gain = mix(FREQ_GAIN_MIN, FREQ_GAIN_MAX, curved_norm);
    float final_amplitude = clamp(pow(processed * OVERALL_GAIN * gain, BAR_HEIGHT_POWER), 0.0, 1.0);

    // Determine lit segments
    int lit_segments = int(floor(final_amplitude * float(SEGMENTS_PER_BAR)));

    // For unlit segments, use the background color
    if (segment_index < lit_segments || segment_index == 0) {
        // Lit segment
        vec3 color = SEGMENT_COLOR;
        color *= BRIGHTNESS_MULT;
        color = clamp(color, 0.0, 1.0);
        fragColor = vec4(color, 1.0);
    } else {
        // Unlit segment - use background color
        fragColor = bg_color;
    }
}
