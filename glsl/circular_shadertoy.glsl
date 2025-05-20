// Circular 1990s Style Spectrum Analyzer - Rectangular Segments
// Variation on https://www.shadertoy.com/view/wfdGW8
// By Marco van Hylckama Vlieg
//
// Google Gemini 2.5 Pro
//
// Follow me on X: https://x.com/AIandDesign
//
// ONE CHANGE: Modified bar geometry to have constant arc width at all radii,
// instead of fanning out radially.
// REMOVED: Inner segment is no longer 'always on'.
// REMOVED: Unlit segments are now black instead of faintly visible.
//
// Forward declaration of uniforms
// These will be set from the renderer
uniform int uNumBars;           // Number of bars around the circle
uniform int uSegmentsPerBar;    // Number of segments per bar
uniform float uInnerRadius;     // Inner radius of the circle (0-1)
uniform float uOuterRadius;     // Outer radius of the circle (0-1)
uniform float uBorderSize;      // Border size for segments (0-1)
uniform float uBarWidth;        // Width of bars (0-1, where 1 means bars touch)
uniform float uRectangularBars; // Use rectangular bars (0=radial/trapezoid, 1=rectangular)
uniform float uDebugMode;       // Debug mode (0=off, 1=on)
uniform float uTime;            // Current time in seconds (for animation)

// Sensitivity and gain uniforms
uniform float uOverallMasterGain;
uniform float uFreqGainMinMult;
uniform float uFreqGainMaxMult;
uniform float uFreqGainCurvePower;
uniform float uBarHeightPower;
uniform float uAmplitudeCompressionPower;

// Fallback constants in case uniforms aren't set
const int NUM_BARS = 36;
const int SEGMENTS_PER_BAR = 15;

// Enhanced debug function to visualize the audio texture at the bottom of the screen
vec4 debugAudioTexture(vec2 uv) {
    // Only show in the bottom 15% of the screen
    if (uv.y > 0.15) return vec4(0.0);

    // Map x coordinate to audio texture position
    float x_pos = uv.x;

    // Sample the audio texture using regular texture sampling
    float amplitude = texture(iChannel0, vec2(x_pos, 0.0)).x;

    // Draw a simple bar graph
    float bar_height = amplitude * 0.15; // Scale to fit in the bottom 15%

    // Draw the bar - only if amplitude is above a threshold
    // This prevents the solid bar at the bottom
    if (uv.y < bar_height && amplitude > 0.01) {
        // Color based on amplitude (blue for low, green for high)
        return vec4(0.0, amplitude, 1.0 - amplitude, 1.0);
    }

    // Draw a reference line at the top
    if (abs(uv.y - 0.15) < 0.002) {
        return vec4(1.0, 1.0, 1.0, 1.0);
    }

    // Draw a reference line at the bottom
    if (abs(uv.y - 0.001) < 0.001) {
        return vec4(0.5, 0.5, 0.5, 1.0);
    }

    // Draw markers for each bar's sampling position
    // Use uNumBars if set, otherwise fall back to NUM_BARS constant
    int numBars = (uNumBars > 0) ? uNumBars : NUM_BARS;

    for (int i = 0; i < numBars; i++) {
        // Calculate the texel position for this bar (same calculation as in mainImage)
        float texels_per_bar = 512.0 / float(numBars);
        float texel_pos = (float(i) + 0.5) * texels_per_bar;
        float marker_pos = texel_pos / 512.0; // Normalize to 0-1

        // Draw a vertical line at each bar's sampling position
        if (abs(uv.x - marker_pos) < 0.001) {
            // Alternate colors for better visibility
            if (i % 2 == 0) {
                return vec4(1.0, 1.0, 0.0, 1.0); // Yellow
            } else {
                return vec4(0.0, 1.0, 1.0, 1.0); // Cyan
            }
        }

        // Draw bar index numbers for every 5th bar
        if (i % 5 == 0) {
            // Draw a small horizontal line
            if (abs(uv.x - marker_pos) < 0.005 && abs(uv.y - 0.02) < 0.002) {
                return vec4(1.0, 1.0, 1.0, 1.0);
            }
        }
    }

    // Background - more transparent and darker
    return vec4(0.05, 0.05, 0.05, 0.5);
}

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    // --- Mathematical Constants ---
    const float PI = 3.14159265359; // Defined PI

    // --- Constants ---
    // NUM_BARS and SEGMENTS_PER_BAR are already defined at the top of the file

    // Define the radial bounds of the analyzer ring (normalized 0-1 from center to edge)
    // These are relative to the distance from the center to the NEAREST screen edge after aspect correction.
    // Use uniform values if set, otherwise fall back to constants
    float innerRadius = (uInnerRadius > 0.0) ? uInnerRadius : 0.20;
    float outerRadius = (uOuterRadius > 0.0) ? uOuterRadius : 0.40;

    // Angle offset for the start of the spectrum (e.g., 0.0 for right, PI/2.0 for top, PI for left, 3*PI/2.0 for bottom)
    // Let's start the lowest frequency bar at the bottom (3*PI/2) and go counter-clockwise.
    const float START_ANGLE_OFFSET = 3.0 * PI / 2.0; // Start at the bottom (270 degrees or -90 degrees)

    // Define spacing/borders relative to the SIZE OF THE RECTANGULAR CELL (0.0 to 1.0)
    // This refers to the local coordinate system within a single segment rectangle.
    float borderSize = (uBorderSize > 0.0) ? uBorderSize : 0.08;

    // --- Sensitivity and Gain Settings (Use uniforms if set, otherwise use defaults) ---
    float overallMasterGain = (uOverallMasterGain > 0.0) ? uOverallMasterGain : 0.8;
    float freqGainMinMult = (uFreqGainMinMult > 0.0) ? uFreqGainMinMult : 0.3;
    float freqGainMaxMult = (uFreqGainMaxMult > 0.0) ? uFreqGainMaxMult : 1.2;
    float freqGainCurvePower = (uFreqGainCurvePower > 0.0) ? uFreqGainCurvePower : 0.7;
    float barHeightPower = (uBarHeightPower > 0.0) ? uBarHeightPower : 1.2;
    float amplitudeCompressionPower = (uAmplitudeCompressionPower > 0.0) ? uAmplitudeCompressionPower : 0.9;

    // --- Color Settings ---
    const vec3 COLOR_LIT_DARK    = vec3(0.4, 0.4, 0.4); // Base color for lit segments (inner)
    const vec3 COLOR_LIT_BRIGHT  = vec3(1.0, 1.0, 1.0); // Color for lit segments (outer) - brighter teal/cyan
    // const vec3 COLOR_UNLIT        = vec3(0.08, 0.08, 0.08); // Removed - will draw black instead
    const vec3 COLOR_BORDER       = vec3(0.0, 0.0, 0.0); // Pure black

    // Optional: Brightness multiplier for lit segments to make them stand out
    const float LIT_BRIGHTNESS_MULTIPLIER = 1.3;


    // --- Coordinate Mapping ---

    // Normalize coordinates (0..1, 0,0 is bottom-left)
    vec2 uv = fragCoord.xy / iResolution.xy;

    // Debug visualization of audio texture
    vec4 debug_color = debugAudioTexture(uv);
    if (debug_color.a > 0.0) {
        fragColor = debug_color;
        return;
    }

    // Sample background color from channel 1 (image/video background)
    vec4 bg_color = texture(iChannel1, uv);

    // Center and scale coordinates to -1..1 range, 0,0 is center
    vec2 centered_uv_scaled = (uv - 0.5) * 2.0;

    // Account for aspect ratio so the circle isn't stretched
    // Scale the x-axis to match the y-axis scale
    centered_uv_scaled.x *= iResolution.x / iResolution.y;

    // Convert aspect-corrected coordinates to polar
    // Radius: Distance from center. Normalize by 2.0 to get 0..1 where 0.5 is the edge of the shorter axis.
    float r_normalized = length(centered_uv_scaled) / 2.0;
    // Angle: Angle in radians (-PI to PI)
    float theta = atan(centered_uv_scaled.y, centered_uv_scaled.x);


    // --- Check if pixel is within the analyzer ring ---
    // r_normalized is 0 at center, 0.5 at nearest edge.
    if (r_normalized < innerRadius || r_normalized > outerRadius) {
        // Outside the analyzer ring: show background
        fragColor = bg_color;
        return;
    }

    // Debug visualization - only shown when debug mode is enabled
    if (uDebugMode > 1.5) {
        // Show a simple colored ring to verify the ring dimensions are correct
        vec3 debug_color = vec3(0.0);

        // Divide the ring into 8 sectors with different colors
        // Add time-based rotation to verify animation is working
        float rotating_theta = theta + uTime * 0.5; // Rotate slowly over time
        float angle_sector = mod(rotating_theta + PI, 2.0 * PI) / (PI / 4.0);
        int sector = int(floor(angle_sector));

        // Assign different colors to each sector
        if (sector == 0) debug_color = vec3(1.0, 0.0, 0.0); // Red
        else if (sector == 1) debug_color = vec3(1.0, 0.5, 0.0); // Orange
        else if (sector == 2) debug_color = vec3(1.0, 1.0, 0.0); // Yellow
        else if (sector == 3) debug_color = vec3(0.0, 1.0, 0.0); // Green
        else if (sector == 4) debug_color = vec3(0.0, 1.0, 1.0); // Cyan
        else if (sector == 5) debug_color = vec3(0.0, 0.0, 1.0); // Blue
        else if (sector == 6) debug_color = vec3(0.5, 0.0, 1.0); // Purple
        else debug_color = vec3(1.0, 0.0, 1.0); // Magenta

        // Add a pulsing effect based on time to verify animation
        float pulse = 0.5 + 0.5 * sin(uTime * 2.0);

        // Vary brightness based on radius and pulse
        float brightness = ((r_normalized - innerRadius) / (outerRadius - innerRadius)) * (0.7 + 0.3 * pulse);
        debug_color *= brightness;

        // Show the debug visualization
        fragColor = vec4(debug_color, 1.0);

        // Exit early in full debug mode
        return;
    }

    // --- Determine Bar Index based on Angle ---

    // Normalize angle over the full circle (0.0 to 1.0) after applying offset
    // atan gives -PI to PI. Add PI to shift range to [0, 2*PI].
    // Then add START_ANGLE_OFFSET and wrap using mod. Normalize to 0..1.
    float angle_0_2PI = theta + PI; // Shift from [-PI, PI] to [0, 2*PI]
    float final_angle = mod(angle_0_2PI + START_ANGLE_OFFSET, 2.0 * PI); // Add offset and wrap
    float normalized_angle = final_angle / (2.0 * PI); // Normalize to [0, 1)

    // Use uNumBars if set, otherwise fall back to NUM_BARS constant
    int numBars = (uNumBars > 0) ? uNumBars : NUM_BARS;

    // Integer index for bar (based on angle)
    int bar_index = int(floor(normalized_angle * float(numBars)));

    // Check valid bar index (shouldn't be needed if r_normalized check is right, but good practice)
     if (bar_index < 0 || bar_index >= numBars) {
         fragColor = vec4(0.0, 0.0, 0.0, 1.0);
         return;
     }

    // --- Determine Segment Index based on Radial Position ---

    // Normalize radial position within the ring (0.0 at innerRadius, 1.0 at outerRadius)
    float normalized_radial_pos_in_ring = (r_normalized - innerRadius) / (outerRadius - innerRadius);

    // Use uSegmentsPerBar if set, otherwise fall back to SEGMENTS_PER_BAR constant
    int segmentsPerBar = (uSegmentsPerBar > 0) ? uSegmentsPerBar : SEGMENTS_PER_BAR;

    // Integer index for the segment (based on this normalized radial position)
    // Segment 0 is innermost.
    int segment_index = int(floor(normalized_radial_pos_in_ring * float(segmentsPerBar)));

    // Check valid segment index (shouldn't be needed if r_normalized check is right, but good practice)
    if (segment_index < 0 || segment_index >= segmentsPerBar) {
        // Invalid segment index: show background
        fragColor = bg_color;
        return;
    }

    // --- Calculate Local UV and Bar Shape ---

    // The 'vertical' local coordinate (0..1) is based on the radial position within the segment's radial band
    float local_radial_uv = fract(normalized_radial_pos_in_ring * float(segmentsPerBar)); // Position within the segment's radial slice

    // --- Calculate Local Horizontal UV ---
    // We support two modes: rectangular bars (consistent width) or radial bars (trapezoid)

    // Calculate the angle span for each bar
    float bar_angle_span = 2.0 * PI / float(numBars);

    // Calculate the center angle for this bar
    float bar_center_angle = (float(bar_index) * bar_angle_span) + (bar_angle_span * 0.5) + START_ANGLE_OFFSET;

    // Get the bar width factor (how much of the available space each bar takes)
    float barWidthFactor = (uBarWidth > 0.0) ? clamp(uBarWidth, 0.1, 0.95) : 0.8;

    float local_horizontal_uv;

    // Calculate the current angle relative to the bar's center angle
    float angle_diff = theta - bar_center_angle;

    // Wrap the angle difference to ensure it's in the range [-PI, PI]
    while (angle_diff > PI) angle_diff -= 2.0 * PI;
    while (angle_diff < -PI) angle_diff += 2.0 * PI;

    // --- SIMPLE RADIAL BAR MODE ---
    // This is a simplified version that we know works

    // Calculate the half-width of the bar in radians
    float half_bar_angle = (bar_angle_span * 0.5) * barWidthFactor;

    // Normalize the position within the bar to [0,1] range
    // 0 = left edge, 0.5 = center, 1 = right edge
    local_horizontal_uv = (angle_diff + half_bar_angle) / (2.0 * half_bar_angle);

    // Debug: Force local_horizontal_uv to be in valid range for testing
    // Uncomment this line to make all pixels within the ring show as part of a bar
    if (uDebugMode > 1.5) {
        // Full debug mode - show all pixels in the ring
        local_horizontal_uv = 0.5;
    }

    // --- Determine pixel color based on position within the constant-width bar rectangle ---

    // Debug: Show a solid color for all bars to verify bar geometry
    if (uDebugMode > 0.5 && uDebugMode < 1.0) {
        // Show a solid color based on the bar index
        vec3 bar_color = vec3(0.5);
        if (bar_index % 2 == 0) {
            bar_color = vec3(0.8, 0.8, 0.8); // Lighter for even bars
        }
        fragColor = vec4(bar_color, 1.0);
        return;
    }

    // If the pixel is outside the conceptual bar slot (i.e., in the gap), draw black.
    // The bar slot occupies the local_horizontal_uv range [0, 1].
    if (local_horizontal_uv < 0.0 || local_horizontal_uv > 1.0) {
        // Gap between bars: show background
        fragColor = bg_color;
        return;
    }

    // If we are within the bar slot [0, 1] horizontally, check if it's a border pixel.
    // Show background in the border area instead of a solid color.
    float border = max(0.01, borderSize); // Ensure border is at least 0.01
    if (local_horizontal_uv < border || local_horizontal_uv > 1.0 - border ||
        local_radial_uv < border || local_radial_uv > 1.0 - border)
    {
        fragColor = bg_color; // Show background in border areas
        return;
    }

    // --- If we reach here, the pixel is inside the non-border part of the segment. ---
    // Continue with getting audio data and determining segment color.


    // --- Get Audio Data for the Current Bar ---

    // Map the bar index directly to a position in the audio texture
    // The audio texture has 512 pixels, and we've distributed our NUM_BARS bars across it
    // Each bar occupies multiple texels in the texture, so we need to sample from the correct position

    // Calculate how many texels each bar occupies in the texture
    float texels_per_bar = 512.0 / float(numBars);

    // Calculate the center position for this bar's texels
    // This ensures we sample from the middle of the bar's range in the texture
    // Add a small offset to avoid edge cases at the first and last bars
    float texel_pos = (float(bar_index) + 0.5) * texels_per_bar;

    // Adjust the first and last bars to ensure they get proper data
    if (bar_index == 0) {
        // First bar - sample a bit further in to avoid edge effects
        texel_pos = max(texel_pos, 2.0);
    } else if (bar_index == numBars - 1) {
        // Last bar - sample a bit before the edge
        texel_pos = min(texel_pos, 510.0);
    }

    // Convert to normalized texture coordinates (0-1 range)
    float freq_pos = texel_pos / 512.0;

    // Ensure freq_pos is within valid range [0,1]
    freq_pos = clamp(freq_pos, 0.01, 0.99); // Avoid the very edges

    // Sample raw amplitude from the audio texture
    // The audio texture has frequencies mapped along the X-axis
    float raw_amplitude = texture(iChannel0, vec2(freq_pos, 0.0)).r;

    // Debug: Force amplitude for testing
    if (uDebugMode > 0.0 && uDebugMode < 0.5) {
        // Create a pattern where every 4th bar is fully lit
        if (bar_index % 4 == 0) {
            raw_amplitude = 1.0;  // Full amplitude
        } else if (bar_index % 4 == 1) {
            raw_amplitude = 0.75;  // 75% amplitude
        } else if (bar_index % 4 == 2) {
            raw_amplitude = 0.5;  // 50% amplitude
        } else {
            raw_amplitude = 0.25;  // 25% amplitude
        }
    }

    // Simple debug mode for testing
    if (uDebugMode > 0.5) {
        // Create a test pattern
        if (bar_index % 4 == 0) {
            raw_amplitude = 1.0;  // Full amplitude
        } else if (bar_index % 4 == 1) {
            raw_amplitude = 0.75;  // 75% amplitude
        } else if (bar_index % 4 == 2) {
            raw_amplitude = 0.5;  // 50% amplitude
        } else {
            raw_amplitude = 0.25;  // 25% amplitude
        }
    }

    // Debug: Uncomment to verify bar index to texture mapping
    // if (bar_index == 0) raw_amplitude = 1.0;  // Force first bar to full amplitude
    // if (bar_index == NUM_BARS/4) raw_amplitude = 0.8;  // Force quarter-way bar to 80%
    // if (bar_index == NUM_BARS/2) raw_amplitude = 0.6;  // Force half-way bar to 60%
    // if (bar_index == 3*NUM_BARS/4) raw_amplitude = 0.4;  // Force three-quarter-way bar to 40%
    // if (bar_index == NUM_BARS-1) raw_amplitude = 0.2;  // Force last bar to 20%

    // Debug mode: Force specific bars to light up
    // This helps identify if the issue is with the shader or the audio data
    bool debug_mode = false;  // Set to true to test with fixed pattern
    if (debug_mode) {
        // Create a pattern where every 3rd bar is fully lit, others are partially lit or off
        if (bar_index % 3 == 0) {
            raw_amplitude = 1.0;  // Full amplitude
        } else if (bar_index % 3 == 1) {
            raw_amplitude = 0.6;  // Medium amplitude
        } else {
            raw_amplitude = 0.0;  // No amplitude (should be off)
        }
    }

    // Debug: Force specific amplitudes for testing
    // if (bar_index == 0) raw_amplitude = 1.0;
    // if (bar_index == 1) raw_amplitude = 0.8;
    // if (bar_index == 2) raw_amplitude = 0.6;
    // if (bar_index == 3) raw_amplitude = 0.4;
    // if (bar_index == 4) raw_amplitude = 0.2;

    // Don't apply a noise floor - let zero values be zero
    // This ensures bars with no audio signal remain off

    // --- Apply Sensitivity and Frequency-Dependent Gain ---
    float processed_amplitude = pow(raw_amplitude, amplitudeCompressionPower);
    float bar_norm = float(bar_index) / float(numBars - 1); // 0 for first bar, 1 for last
    float curved_bar_norm = pow(bar_norm, freqGainCurvePower);
    float freq_gain_multiplier = mix(freqGainMinMult, freqGainMaxMult, curved_bar_norm);
    float amplitude_after_gain = processed_amplitude * overallMasterGain * freq_gain_multiplier;
    float final_amplitude = pow(amplitude_after_gain, barHeightPower); // Height 0.0 to 1.0 after power curve

    // Clamp the final amplitude to be between 0 and 1
    final_amplitude = clamp(final_amplitude, 0.0, 1.0);

    // --- Determine how many segments are lit based on final amplitude ---
    // Note: This will be a float value between 0 and segmentsPerBar
    float lit_segments_float = final_amplitude * float(segmentsPerBar);

    // Don't force the innermost segment to be lit - only light segments based on amplitude
    // Use ceiling to ensure proper segment lighting
    int lit_segments_count = int(ceil(lit_segments_float));

    // Only light segments if there's actual audio signal
    // Don't force any segments to be lit when there's no signal

    // Debug: Force all segments to be lit for testing
    // lit_segments_count = SEGMENTS_PER_BAR;


    // --- Determine the final pixel color ---

    // Simple segment color calculation
    vec3 final_segment_color;

    // Lighting logic: segment_index 0 is innermost.
    // Check if the current segment index is less than the count of segments that should be lit.
    // This lights up segments from the inside outwards up to the amplitude level.
    // Only light segments if there's actual audio signal
    if (segment_index < lit_segments_count) { // Only light segments based on amplitude
        // This segment should be lit.
        // Choose color based on segment index (0=inner, segmentsPerBar-1=outer segment)
        float segment_norm_height = float(segment_index) / float(segmentsPerBar - 1); // 0 for inner segment, approaches 1 for outer

        // Normal mode: Lit color gradient (from inner dark to outer bright teal/cyan)
        final_segment_color = mix(COLOR_LIT_DARK, COLOR_LIT_BRIGHT, segment_norm_height);

        // Apply brightness multiplier for lit segments
        final_segment_color *= LIT_BRIGHTNESS_MULTIPLIER;
        final_segment_color = clamp(final_segment_color, 0.0, 1.0); // Clamp after multiplying

        // Optional: Add a subtle glow effect towards the edges of the lit bars
        // This makes the transition slightly smoother and glowier.
        // A simple way is to mix in more of the bright color based on how close the *amplitude* is
        // to lighting up the *next* segment, or based on the position within the *current* lit segment.

        // Option A: Based on position within the currently lit segment band (local_radial_uv)
        // float glow_edge = smoothstep(1.0 - BORDER_SIZE * 3.0, 1.0 - BORDER_SIZE, local_radial_uv); // Glow near the outer edge of the segment cell
        // final_segment_color = mix(final_segment_color, COLOR_LIT_BRIGHT * LIT_BRIGHTNESS_MULTIPLIER, glow_edge * 0.5); // Mix in some extra bright glow

        // Option B: Based on how close the *amplitude* is to the *next* segment threshold
        // This creates a glow effect on the *top* segment of the bar.
        float fractional_segment = fract(lit_segments_float); // How far into lighting the next segment we are
        if (segment_index == lit_segments_count - 1 && lit_segments_count > 0) { // Only apply glow to the topmost lit segment (if any)
             float glow_intensity = pow(fractional_segment, 2.0); // Power curve makes glow stronger when closer to full
             final_segment_color = mix(final_segment_color, COLOR_LIT_BRIGHT * LIT_BRIGHTNESS_MULTIPLIER * 1.5, glow_intensity); // Mix in bright glow
             final_segment_color = clamp(final_segment_color, 0.0, 1.0); // Clamp again
        }


    } else {
        // Non-lit segment: completely black (no overlay)
        fragColor = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }

    // Output the final lit segment color
    fragColor = vec4(final_segment_color, 1.0);
}
