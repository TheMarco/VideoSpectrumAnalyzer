// Smooth Curves
//
// An audio visualizer made by Marco van Hylckama Vlieg
// Using Claude 4.0 Sonnet
//
// Follow me on X: https://x.com/AIandDesign
//

// [C]
// Smooth Curves
// by Marco van Hylckama Vlieg
// https://x.com/AIandDesign
// [/C]

// CONFIGURABLE SETTINGS
#define LINE_THICKNESS 3.0    // Line thickness in pixels (adjust this!)
#define BLOOM_SIZE 20.0       // Bloom/glow size - INCREASED for more visible glow
#define BLOOM_INTENSITY 0.5   // Bloom intensity - INCREASED for brighter glow
#define BLOOM_FALLOFF 1.5     // Bloom falloff rate (higher = sharper falloff)
#define FILL_ENABLED true     // Enable/disable semi-transparent fill
#define FILL_OPACITY 0.3      // Fill opacity (0.0 to 1.0) - increased for visibility

// Other configuration
#define SCALE 0.2
#define SHIFT 0.05  // Relative to screen width
#define WIDTH 0.06  // Relative to screen width
#define AMP 1.0

// Reactivity settings - these will be overridden by uniforms
#define DECAY_SPEED 0.2       // How quickly the visualization decays (0.0-1.0, higher = faster)
#define ATTACK_SPEED 1.0      // How quickly the visualization responds to new audio (0.0-1.0)
#define NOISE_GATE 0.03       // Minimum audio level to respond to (0.0-1.0)

// Colors matching the original
#define COLOR1 vec3(203.0, 36.0, 128.0) / 255.0   // Pink/Magenta
#define COLOR2 vec3(41.0, 200.0, 192.0) / 255.0   // Cyan
#define COLOR3 vec3(24.0, 137.0, 218.0) / 255.0   // Blue

// Shuffle array for frequency selection
const int shuffle[5] = int[5](1, 3, 0, 4, 2);

// Previous frame's audio data (stored in iChannel1)
float getPrevFreq(int channel, int i) {
    int band = 2 * channel + shuffle[i] * 6;
    float normalizedBand = float(band) / 32.0;
    return texture(iChannel1, vec2(normalizedBand, 0.0)).x;
}

// Get frequency for given channel and index with decay and attack
float getFreq(int channel, int i) {
    int band = 2 * channel + shuffle[i] * 6;
    float normalizedBand = float(band) / 32.0;

    // Get current raw audio data
    float currentAudio = texture(iChannel0, vec2(normalizedBand, 0.0)).x;

    // Apply noise gate (use uniform if available, otherwise fallback to define)
    float noiseGate = iNoiseGate > 0.0 ? iNoiseGate : NOISE_GATE;
    currentAudio = max(0.0, currentAudio - noiseGate);

    // Get previous frame's processed value
    float prevValue = getPrevFreq(channel, i);

    // Apply attack and decay (use uniforms if available, otherwise fallback to defines)
    float attackSpeed = iAttackSpeed > 0.0 ? iAttackSpeed : ATTACK_SPEED;
    float decaySpeed = iDecaySpeed > 0.0 ? iDecaySpeed : DECAY_SPEED;

    float result;
    if (currentAudio > prevValue) {
        // Attack phase - rise quickly to new level
        result = mix(prevValue, currentAudio, attackSpeed);
    } else {
        // Decay phase - fall gradually
        result = prevValue * (1.0 - decaySpeed);
    }

    return result;
}

// Scale factor for the given value index
float getScale(int i) {
    float x = abs(2.0 - float(i)); // 2,1,0,1,2
    float s = 3.0 - x;             // 1,2,3,2,1
    return s / 3.0 * AMP;
}

// Smooth cubic interpolation for curves
float smoothCubic(float t) {
    return t * t * (3.0 - 2.0 * t);
}

// Inversion factor - curves bulge outward at ends, inward in middle
float getInversionFactor(int index) {
    // Index 0 and 4 (ends) should be inverted (negative)
    // Index 1, 2, 3 (middle) should be normal (positive)
    if (index == 0 || index == 4) {
        return -1.0; // Invert at ends
    } else {
        return 1.0;  // Normal in middle
    }
}

// Sample curve at parameter t with smooth transitions and inverted ends
float sampleCurveY(float t, float y[5], bool upper) {
    t = clamp(t, 0.0, 1.0);

    // Extended curve for smooth transitions at ends
    float extendedT = t * 1.4 - 0.2; // Map to -0.2 to 1.2 for smooth ends

    if (extendedT <= 0.0) {
        // Smooth transition from baseline to first peak (INVERTED)
        float blend = smoothCubic((extendedT + 0.2) / 0.2);
        float displacement = (y[0] - 0.5) * getInversionFactor(0);
        float result = 0.5 + displacement * blend;
        return upper ? result : (1.0 - result);
    } else if (extendedT >= 1.0) {
        // Smooth transition from last peak to baseline (INVERTED)
        float blend = smoothCubic(1.0 - (extendedT - 1.0) / 0.2);
        float displacement = (y[4] - 0.5) * getInversionFactor(4);
        float result = 0.5 + displacement * blend;
        return upper ? result : (1.0 - result);
    }

    // Map to the 5 frequency peaks with smooth interpolation
    float scaledT = extendedT * 4.0; // 0 to 4
    int index = int(scaledT);
    float frac = fract(scaledT);

    // Smooth cubic interpolation between peaks
    frac = smoothCubic(frac);

    float y1, y2;
    float inv1, inv2;

    if (index >= 4) {
        y1 = y2 = y[4];
        inv1 = inv2 = getInversionFactor(4);
    } else {
        y1 = y[index];
        y2 = y[min(index + 1, 4)];
        inv1 = getInversionFactor(index);
        inv2 = getInversionFactor(min(index + 1, 4));
    }

    // Apply inversion to displacements
    float disp1 = (y1 - 0.5) * inv1;
    float disp2 = (y2 - 0.5) * inv2;

    float displacement = mix(disp1, disp2, frac);
    float result = 0.5 + displacement;

    if (!upper) {
        result = 1.0 - result; // Mirror for lower curve
    }

    return result;
}

// Get fill intensity for a point (0.0 = outside, 1.0 = inside)
float getFillIntensity(vec2 uv, int channel) {
    float m = 0.5; // middle of canvas

    // Calculate shape bounds
    float totalWidth = 15.0 * WIDTH;
    float offset = (1.0 - totalWidth) / 2.0;
    float channelShift = float(channel) * SHIFT;

    // Shape bounds
    float startX = offset + channelShift;
    float endX = offset + channelShift + totalWidth;

    // Early exit for performance - if we're outside the curve area
    if (uv.x < startX || uv.x > endX) {
        return 0.0;
    }

    // Calculate y values based on frequencies
    float y[5];
    for (int i = 0; i < 5; i++) {
        float freq = getFreq(channel, i);
        float scaleFactor = getScale(i);
        y[i] = max(0.0, m - scaleFactor * SCALE * freq);
    }

    // Map UV x to curve parameter t
    float t = (uv.x - startX) / (endX - startX);

    // Sample upper and lower curves
    float upperY = sampleCurveY(t, y, true);
    float lowerY = sampleCurveY(t, y, false);

    // Ensure proper ordering
    float minY = min(upperY, lowerY);
    float maxY = max(upperY, lowerY);

    // Binary result for better performance
    return (uv.y >= minY && uv.y <= maxY) ? 1.0 : 0.0;
}

// Get the outline distance for one channel with smooth curves
float getOutlineDistance(vec2 uv, int channel) {
    float m = 0.5; // middle of canvas

    // Calculate shape bounds
    float totalWidth = 15.0 * WIDTH;
    float offset = (1.0 - totalWidth) / 2.0;
    float channelShift = float(channel) * SHIFT;

    // Extended bounds for smooth curve transitions
    float startX = offset + channelShift;
    float endX = offset + channelShift + totalWidth;

    // Early exit for pixels far from the curve area (major performance optimization)
    float margin = 0.1; // Margin to account for glow
    if (uv.x < startX - margin || uv.x > endX + margin) {
        return 1.0; // Return a large enough distance to not render anything
    }

    // Calculate y values based on frequencies
    float y[5];
    for (int i = 0; i < 5; i++) {
        float freq = getFreq(channel, i);
        float scaleFactor = getScale(i);
        y[i] = max(0.0, m - scaleFactor * SCALE * freq);
    }

    float minDist = 1000.0;

    // Check if we're in the curve area
    if (uv.x >= startX && uv.x <= endX) {
        // Map UV x to curve parameter t
        float t = (uv.x - startX) / (endX - startX);

        // Sample upper and lower curves with smooth transitions and inverted ends
        float upperY = sampleCurveY(t, y, true);
        float lowerY = sampleCurveY(t, y, false);

        // Distance to upper and lower curves
        minDist = min(minDist, abs(uv.y - upperY));
        minDist = min(minDist, abs(uv.y - lowerY));
    } else {
        // Distance to baseline outside curve area
        minDist = abs(uv.y - m);
    }

    return minDist;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord / iResolution.xy;

    // Sample background texture if available
    vec4 backgroundColor = texture(iChannel2, uv);

    // Start with background color or black if no background
    vec3 finalColor = backgroundColor.a > 0.0 ? backgroundColor.rgb : vec3(0.0, 0.0, 0.0);

    // CONFIGURABLE line thickness and bloom - precalculate for performance
    vec2 pixelSize = 1.0 / iResolution.xy;
    float lineThickness = LINE_THICKNESS * length(pixelSize);
    float glowSize = BLOOM_SIZE * length(pixelSize);

    // Draw three channels
    for (int channel = 0; channel < 3; channel++) {
        // Get channel color
        vec3 channelColor;
        if (channel == 0) channelColor = COLOR1;
        else if (channel == 1) channelColor = COLOR2;
        else channelColor = COLOR3;

        // Get distance to the outline (in UV space) - do this first for early exit
        float dist = getOutlineDistance(uv, channel);

        // Early exit if we're far from the curve (major performance optimization)
        // Only process pixels that are close enough to be affected by the glow
        if (dist > glowSize * 3.0) continue;

        // Add fill if enabled
        if (FILL_ENABLED) {
            float fillIntensity = getFillIntensity(uv, channel);
            if (fillIntensity > 0.0) {
                vec3 fillColor = channelColor * FILL_OPACITY * fillIntensity;
                finalColor += fillColor;
            }
        }

        // Create smooth thin line stroke with CONFIGURABLE thickness
        float stroke = 1.0 - smoothstep(0.0, lineThickness, dist);

        // ENHANCED BLOOM/GLOW with multiple layers
        // Primary glow
        float glow1 = exp(-dist * BLOOM_FALLOFF / glowSize) * BLOOM_INTENSITY;

        // Secondary wider glow for more dramatic effect
        float glow2 = exp(-dist * (BLOOM_FALLOFF * 0.5) / (glowSize * 2.0)) * (BLOOM_INTENSITY * 0.5);

        // Combine glows
        float totalGlow = glow1 + glow2;

        // Combine stroke and glow
        float intensity = stroke + totalGlow;

        // Screen blend mode approximation
        vec3 layerColor = channelColor * intensity;
        finalColor = finalColor + layerColor - finalColor * layerColor;
    }

    // Preserve alpha from background or use 1.0 if no background
    float alpha = backgroundColor.a > 0.0 ? backgroundColor.a : 1.0;
    fragColor = vec4(finalColor, alpha);
}
