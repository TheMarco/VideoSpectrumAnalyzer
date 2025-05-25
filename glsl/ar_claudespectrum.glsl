// Claude's Spectrum
//
// An audio visualizer made by Marco van Hylckama Vlieg
// Using Claude 4.0 Sonnet
//
// Follow me on X: https://x.com/AIandDesign
//

// CONFIGURABLE SETTINGS
#define BAR_WIDTH 0.008       // Width of each bar
#define BAR_SPACING 0.014     // Fixed spacing between bars
#define MAX_BAR_HEIGHT 0.7    // Maximum bar height
#define BLOOM_SIZE 8.0        // Bloom/glow size
#define BLOOM_INTENSITY 0.3   // Bloom intensity
#define BLOOM_FALLOFF 2.0     // Bloom falloff rate

// COLOR SCHEME CONFIGURATION
#define COLOR_SCHEME 0        // 0=current, 1=single, 2=rainbow, 3=purple, 4=green, 5=blue
#define SINGLE_COLOR vec3(1.0, 1.0, 1.0)  // White for single color mode

// SCALING CONFIGURATION
#define USE_LOGARITHMIC_SCALE 1  // 1 = logarithmic, 0 = linear
#define LOG_SCALE_FACTOR 0.5     // Higher = more emphasis on low frequencies

// Center line settings
#define CENTER_LINE_THICKNESS 0.006  // Thickness of center line
#define CENTER_LINE_OVERHANG 0.05     // How much line extends beyond bars on each side
#define CENTER_LINE_COLOR vec3(0.6, 0.6, 0.6)  // Gray color for center line

// Visual settings
#define NUM_BARS 48           // Number of frequency bars (configurable up to 128)
#define CENTER_Y 0.5          // Vertical center position
#define WAVEFORM_WIDTH 0.8    // Total width of waveform (1.0 = full screen width)

// Color schemes
#define COLOR_LOW vec3(1.0, 0.2, 0.1)    // Red/Orange for low frequencies
#define COLOR_MID vec3(1.0, 1.0, 0.2)    // Yellow for mid frequencies
#define COLOR_HIGH vec3(0.2, 0.4, 1.0)   // Blue for high frequencies

// Convert bar index to frequency sampling position
float getFrequencySamplePosition(int barIndex) {
    float t = float(barIndex) / float(NUM_BARS - 1); // 0.0 to 1.0

    if (USE_LOGARITHMIC_SCALE == 1) {
        // Logarithmic scaling - more balanced curve to prevent rightmost bar oversensitivity
        // Use a more gradual curve that doesn't compress high frequencies as much
        float logValue = pow(t, 1.0 / (1.0 + LOG_SCALE_FACTOR));
        return logValue;
    } else {
        // Linear scaling - direct mapping
        return t;
    }
}

// Get audio frequency for a specific bar
float getFrequency(int barIndex) {
    float samplePos = getFrequencySamplePosition(barIndex);

    // Clamp to avoid sampling beyond valid frequency range (prevent rightmost bar issues)
    // Only use 90% of the frequency spectrum to avoid high-frequency noise
    samplePos = clamp(samplePos * 0.9, 0.0, 0.9);

    return texture(iChannel0, vec2(samplePos, 0.0)).x;
}

// HSV to RGB conversion for rainbow colors
vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

// Get color based on frequency position and color scheme
vec3 getBarColor(int barIndex) {
    float t = float(barIndex) / float(NUM_BARS - 1);

    if (COLOR_SCHEME == 0) {
        // Current scheme: Red/Orange -> Yellow -> Blue
        if (t < 0.5) {
            return mix(COLOR_LOW, COLOR_MID, t * 2.0);
        } else {
            return mix(COLOR_MID, COLOR_HIGH, (t - 0.5) * 2.0);
        }
    } else if (COLOR_SCHEME == 1) {
        // Single color
        return SINGLE_COLOR;
    } else if (COLOR_SCHEME == 2) {
        // Rainbow
        return hsv2rgb(vec3(t * 0.8, 1.0, 1.0)); // Hue from 0 to 0.8 (red to purple)
    } else if (COLOR_SCHEME == 3) {
        // Purple gradient
        vec3 darkPurple = vec3(0.3, 0.1, 0.5);
        vec3 brightPurple = vec3(0.8, 0.4, 1.0);
        return mix(darkPurple, brightPurple, t);
    } else if (COLOR_SCHEME == 4) {
        // Green gradient
        vec3 darkGreen = vec3(0.1, 0.3, 0.1);
        vec3 brightGreen = vec3(0.4, 1.0, 0.4);
        return mix(darkGreen, brightGreen, t);
    } else if (COLOR_SCHEME == 5) {
        // Blue gradient
        vec3 darkBlue = vec3(0.1, 0.2, 0.5);
        vec3 brightBlue = vec3(0.4, 0.8, 1.0);
        return mix(darkBlue, brightBlue, t);
    }

    // Fallback to current scheme
    return mix(COLOR_LOW, COLOR_HIGH, t);
}

// Proper distance to a capsule (rounded rectangle)
float distToRoundedBar(vec2 uv, float centerX, float width, float height) {
    // Transform to local coordinates centered on the bar
    vec2 p = uv - vec2(centerX, CENTER_Y);

    // Half dimensions
    float halfWidth = width * 0.5;
    float halfHeight = height * 0.5;

    // Radius for rounded ends (use half the width)
    float radius = halfWidth;

    // Ensure minimum height for proper capsule
    halfHeight = max(halfHeight, radius);

    // Distance to the line segment (the "spine" of the capsule)
    float lineHalfHeight = halfHeight - radius;

    // Clamp the y coordinate to the line segment
    float clampedY = clamp(p.y, -lineHalfHeight, lineHalfHeight);

    // Distance from point to the closest point on the line segment
    vec2 closestPointOnLine = vec2(0.0, clampedY);
    vec2 toPoint = p - closestPointOnLine;

    // Distance to the capsule surface
    return length(toPoint) - radius;
}

// Distance to horizontal center line
float distToCenterLine(vec2 uv, float startX, float endX) {
    float clampedX = clamp(uv.x, startX, endX);
    vec2 closestPoint = vec2(clampedX, CENTER_Y);
    return length(uv - closestPoint);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;

    vec3 finalColor = vec3(0.0);

    // Calculate pixel size for consistent rendering
    vec2 pixelSize = 1.0 / iResolution.xy;

    // Calculate waveform positioning - fixed spacing approach
    float totalWidth = WAVEFORM_WIDTH;
    float availableWidth = totalWidth - float(NUM_BARS) * BAR_WIDTH;
    float actualSpacing = min(BAR_SPACING, availableWidth / float(NUM_BARS - 1));

    // Calculate actual waveform width with fixed spacing
    float actualWaveformWidth = float(NUM_BARS) * BAR_WIDTH + float(NUM_BARS - 1) * actualSpacing;
    float startX = 0.5 - actualWaveformWidth * 0.5;

    // Calculate center line bounds (extends beyond bars)
    float lineStartX = startX - CENTER_LINE_OVERHANG * totalWidth;
    float lineEndX = startX + actualWaveformWidth + CENTER_LINE_OVERHANG * totalWidth;

    // Clamp line bounds to screen
    lineStartX = max(lineStartX, 0.0);
    lineEndX = min(lineEndX, 1.0);

    // Draw center line first
    float centerLineDist = distToCenterLine(uv, lineStartX, lineEndX);
    float centerLineThickness = CENTER_LINE_THICKNESS;

    // Create center line
    float centerLine = 1.0 - smoothstep(0.0, centerLineThickness, centerLineDist);

    // Center line glow - restored to original levels
    float centerGlowSize = BLOOM_SIZE * 0.5 / iResolution.y;
    float centerGlow = exp(-centerLineDist / centerGlowSize * BLOOM_FALLOFF) * (BLOOM_INTENSITY * 0.2);

    // Add center line to final color
    float centerIntensity = centerLine + centerGlow;
    finalColor += CENTER_LINE_COLOR * centerIntensity;

    // Draw frequency bars
    for (int i = 0; i < NUM_BARS; i++) {
        // Get frequency and color for this bar
        float freq = getFrequency(i);
        vec3 barColor = getBarColor(i);

        // Calculate bar position with fixed spacing
        float barCenterX = startX + float(i) * (BAR_WIDTH + actualSpacing) + BAR_WIDTH * 0.5;
        float barHeight = freq * MAX_BAR_HEIGHT;

        // Ensure minimum bar height for proper capsule (should be at least the width)
        barHeight = max(barHeight, BAR_WIDTH);

        // Calculate distance to this rounded bar (capsule)
        float dist = distToRoundedBar(uv, barCenterX, BAR_WIDTH, barHeight);

        // Create bar with sharp edges - use negative distance for inside
        float bar = 1.0 - smoothstep(-pixelSize.x, pixelSize.x, dist);

        // Bloom effect - restored to original Shadertoy levels
        float glowSize = BLOOM_SIZE / iResolution.y;

        // Simple single-layer glow like the original
        float glow = exp(-max(dist, 0.0) / glowSize * BLOOM_FALLOFF) * BLOOM_INTENSITY;

        float totalGlow = glow;

        // Combine bar and glow
        float intensity = bar + totalGlow;

        // Add to final color with screen blend (exactly like Shadertoy)
        vec3 layerColor = barColor * intensity;
        finalColor = finalColor + layerColor - finalColor * layerColor;
    }

    // Sample background texture (iChannel1) if available
    vec3 backgroundColor = texture(iChannel1, uv).rgb;

    // Composite spectrum over background
    vec3 result = backgroundColor + finalColor;

    fragColor = vec4(result, 1.0);
}
