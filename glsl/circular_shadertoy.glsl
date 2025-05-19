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
// Forward declaration of constants
const int NUM_BARS = 36;
const int SEGMENTS_PER_BAR = 15;

// Debug function to visualize the audio texture at the bottom of the screen
vec4 debugAudioTexture(vec2 uv) {
    // Only show in the bottom 10% of the screen
    if (uv.y > 0.1) return vec4(0.0);

    // Map x coordinate to audio texture position
    float x_pos = uv.x;

    // Sample the audio texture using regular texture sampling
    float amplitude = texture(iChannel0, vec2(x_pos, 0.0)).x;

    // Draw a simple bar graph
    float bar_height = amplitude * 0.1; // Scale to fit in the bottom 10%

    if (uv.y < bar_height) {
        // Color based on amplitude (red for low, green for high)
        return vec4(1.0 - amplitude, amplitude, 0.0, 1.0);
    }

    // Draw a reference line at the top
    if (abs(uv.y - 0.1) < 0.002) {
        return vec4(1.0, 1.0, 1.0, 1.0);
    }

    // Background
    return vec4(0.1, 0.1, 0.1, 0.5);
}

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    // --- Mathematical Constants ---
    const float PI = 3.14159265359; // Defined PI

    // --- Constants ---
    // NUM_BARS and SEGMENTS_PER_BAR are already defined at the top of the file

    // Define the radial bounds of the analyzer ring (normalized 0-1 from center to edge)
    // These are relative to the distance from the center to the NEAREST screen edge after aspect correction.
    const float INNER_RADIUS = 0.20; // Inner edge of the segments (0 is center)
    const float OUTER_RADIUS = 0.40; // Outer edge of the segments (0.5 would reach top/bottom/left/right edge)

    // Angle offset for the start of the spectrum (e.g., 0.0 for right, PI/2.0 for top, PI for left, 3*PI/2.0 for bottom)
    // Let's start the lowest frequency bar at the bottom (3*PI/2) and go counter-clockwise.
    const float START_ANGLE_OFFSET = 3.0 * PI / 2.0; // Start at the bottom (270 degrees or -90 degrees)

    // Define spacing/borders relative to the SIZE OF THE RECTANGULAR CELL (0.0 to 1.0)
    // This refers to the local coordinate system within a single segment rectangle.
    const float BORDER_SIZE = 0.08; // How much of the local cell is border space

    // --- Sensitivity and Gain Settings (Tune these!) ---
    const float OVERALL_MASTER_GAIN = 1.0; // *** Set to 1.0 as requested ***
    const float FREQ_GAIN_MIN_MULT = 0.4; // Gain multiplier for lowest freq bar
    const float FREQ_GAIN_MAX_MULT = 1.8; // Gain multiplier for highest freq bar
    const float FREQ_GAIN_CURVE_POWER = 0.6; // Shapes the transition (lower = more gain towards high freqs)

    const float BAR_HEIGHT_POWER = 1.1; // Non-linear height mapping (>1.0 makes high segments harder to light)
    const float AMPLITUDE_COMPRESSION_POWER = 1.0; // Amplitude compression (1.0 disables)

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
    if (r_normalized < INNER_RADIUS || r_normalized > OUTER_RADIUS) {
        // Outside the analyzer ring: show background
        fragColor = bg_color;
        return;
    }

    // --- Determine Bar Index based on Angle ---

    // Normalize angle over the full circle (0.0 to 1.0) after applying offset
    // atan gives -PI to PI. Add PI to shift range to [0, 2*PI].
    // Then add START_ANGLE_OFFSET and wrap using mod. Normalize to 0..1.
    float angle_0_2PI = theta + PI; // Shift from [-PI, PI] to [0, 2*PI]
    float final_angle = mod(angle_0_2PI + START_ANGLE_OFFSET, 2.0 * PI); // Add offset and wrap
    float normalized_angle = final_angle / (2.0 * PI); // Normalize to [0, 1)

    // Integer index for bar (based on angle)
    int bar_index = int(floor(normalized_angle * float(NUM_BARS)));

    // Check valid bar index (shouldn't be needed if r_normalized check is right, but good practice)
     if (bar_index < 0 || bar_index >= NUM_BARS) {
         fragColor = vec4(0.0, 0.0, 0.0, 1.0);
         return;
     }

    // --- Determine Segment Index based on Radial Position ---

    // Normalize radial position within the ring (0.0 at INNER_RADIUS, 1.0 at OUTER_RADIUS)
    float normalized_radial_pos_in_ring = (r_normalized - INNER_RADIUS) / (OUTER_RADIUS - INNER_RADIUS);

    // Integer index for the segment (based on this normalized radial position)
    // Segment 0 is innermost.
    int segment_index = int(floor(normalized_radial_pos_in_ring * float(SEGMENTS_PER_BAR)));

    // Check valid segment index (shouldn't be needed if r_normalized check is right, but good practice)
    if (segment_index < 0 || segment_index >= SEGMENTS_PER_BAR) {
        // Invalid segment index: show background
        fragColor = bg_color;
        return;
    }

    // --- Calculate Local UV and Bar Shape ---

    // The 'vertical' local coordinate (0..1) is based on the radial position within the segment's radial band
    float local_radial_uv = fract(normalized_radial_pos_in_ring * float(SEGMENTS_PER_BAR)); // Position within the segment's radial slice

    // --- Calculate Local Horizontal UV for Constant Width Bars ---
    // We need a horizontal coordinate that maps the arc length within the bar's sector
    // to a 0-1 range, such that the total arc length corresponding to 0-1 is constant
    // regardless of radius. Let this constant total arc length be the arc length of
    // the bar sector at the INNER_RADIUS.

    float bar_angle_span = 2.0 * PI / float(NUM_BARS);
    float total_slot_arc_width = bar_angle_span * INNER_RADIUS; // Constant width based on inner radius

    // Calculate the angle within the current bar's sector (range 0 to bar_angle_span)
    // Use the fact that normalized_angle * NUM_BARS has an integer part (bar_index)
    // and a fractional part (position within the angular sector).
    float angle_within_bar_sector = fract(normalized_angle * float(NUM_BARS)) * bar_angle_span;

    // Calculate the arc length at the current radius corresponding to this angle
    float arc_length_at_current_radius = angle_within_bar_sector * r_normalized;

    // Map this arc length to a local horizontal coordinate (0..1), where 1.0 corresponds
    // to the total_slot_arc_width.
    float local_horizontal_uv = arc_length_at_current_radius / total_slot_arc_width;

    // --- Determine pixel color based on position within the constant-width bar rectangle ---

    // If the pixel is outside the conceptual constant-width bar slot (i.e., in the gap), draw black.
    // The constant-width bar slot occupies the local_horizontal_uv range [0, 1].
    if (local_horizontal_uv < 0.0 || local_horizontal_uv > 1.0) {
        // Gap between bars: show background
        fragColor = bg_color;
        return;
    }

    // If we are within the bar slot [0, 1] horizontally, check if it's a border pixel.
    // Show background in the border area instead of a solid color.
    if (local_horizontal_uv < BORDER_SIZE || local_horizontal_uv > 1.0 - BORDER_SIZE ||
        local_radial_uv < BORDER_SIZE || local_radial_uv > 1.0 - BORDER_SIZE)
    {
        fragColor = bg_color; // Show background in border areas
        return;
    }

    // --- If we reach here, the pixel is inside the non-border part of the segment. ---
    // Continue with getting audio data and determining segment color.


    // --- Get Audio Data for the Current Bar ---

    // Map the bar index directly to a position in the audio texture
    // We need to map the bar index to the correct position in the audio texture
    // The audio texture has 512 pixels, but we only have NUM_BARS bars
    // So we need to sample at specific positions to get the right data

    // Calculate the exact texel position for this bar
    // This ensures we sample exactly at the center of each texel
    float texel_pos = float(bar_index) / float(NUM_BARS) * 512.0;

    // Add 0.5 to sample at the center of the texel
    texel_pos = texel_pos + 0.5;

    // Convert to normalized texture coordinates
    float freq_pos = texel_pos / 512.0;

    // Ensure freq_pos is within valid range [0,1]
    freq_pos = clamp(freq_pos, 0.0, 1.0);

    // Sample raw amplitude from the audio texture
    // The audio texture has frequencies mapped along the X-axis
    float raw_amplitude = texture(iChannel0, vec2(freq_pos, 0.0)).r;

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
    float processed_amplitude = pow(raw_amplitude, AMPLITUDE_COMPRESSION_POWER);
    float bar_norm = float(bar_index) / float(NUM_BARS - 1); // 0 for first bar, 1 for last
    float curved_bar_norm = pow(bar_norm, FREQ_GAIN_CURVE_POWER);
    float freq_gain_multiplier = mix(FREQ_GAIN_MIN_MULT, FREQ_GAIN_MAX_MULT, curved_bar_norm);
    float amplitude_after_gain = processed_amplitude * OVERALL_MASTER_GAIN * freq_gain_multiplier;
    float final_amplitude = pow(amplitude_after_gain, BAR_HEIGHT_POWER); // Height 0.0 to 1.0 after power curve

    // Clamp the final amplitude to be between 0 and 1
    final_amplitude = clamp(final_amplitude, 0.0, 1.0);

    // --- Determine how many segments are lit based on final amplitude ---
    // Note: This will be a float value between 0 and SEGMENTS_PER_BAR
    float lit_segments_float = final_amplitude * float(SEGMENTS_PER_BAR);

    // Don't force the innermost segment to be lit - only light segments based on amplitude
    // Use ceiling to ensure proper segment lighting
    int lit_segments_count = int(ceil(lit_segments_float));

    // Only light segments if there's actual audio signal
    // Don't force any segments to be lit when there's no signal

    // Debug: Force all segments to be lit for testing
    // lit_segments_count = SEGMENTS_PER_BAR;


    // --- Determine the final pixel color ---

    vec3 segment_color;

    // Lighting logic: segment_index 0 is innermost.
    // Check if the current segment index is less than the count of segments that should be lit.
    // This lights up segments from the inside outwards up to the amplitude level.
    // Only light segments if there's actual audio signal
    if (segment_index < lit_segments_count) { // Only light segments based on amplitude
        // This segment should be lit.
        // Choose color based on segment index (0=inner, SEGMENTS_PER_BAR-1=outer segment)
        float segment_norm_height = float(segment_index) / float(SEGMENTS_PER_BAR -1); // 0 for inner segment, approaches 1 for outer

        // Lit color gradient (from inner dark to outer bright teal/cyan)
        segment_color = mix(COLOR_LIT_DARK, COLOR_LIT_BRIGHT, segment_norm_height);

        // Apply brightness multiplier for lit segments
        segment_color *= LIT_BRIGHTNESS_MULTIPLIER;
        segment_color = clamp(segment_color, 0.0, 1.0); // Clamp after multiplying

        // Optional: Add a subtle glow effect towards the edges of the lit bars
        // This makes the transition slightly smoother and glowier.
        // A simple way is to mix in more of the bright color based on how close the *amplitude* is
        // to lighting up the *next* segment, or based on the position within the *current* lit segment.

        // Option A: Based on position within the currently lit segment band (local_radial_uv)
        // float glow_edge = smoothstep(1.0 - BORDER_SIZE * 3.0, 1.0 - BORDER_SIZE, local_radial_uv); // Glow near the outer edge of the segment cell
        // segment_color = mix(segment_color, COLOR_LIT_BRIGHT * LIT_BRIGHTNESS_MULTIPLIER, glow_edge * 0.5); // Mix in some extra bright glow

        // Option B: Based on how close the *amplitude* is to the *next* segment threshold
        // This creates a glow effect on the *top* segment of the bar.
        float fractional_segment = fract(lit_segments_float); // How far into lighting the next segment we are
        if (segment_index == lit_segments_count - 1 && lit_segments_count > 0) { // Only apply glow to the topmost lit segment (if any)
             float glow_intensity = pow(fractional_segment, 2.0); // Power curve makes glow stronger when closer to full
             segment_color = mix(segment_color, COLOR_LIT_BRIGHT * LIT_BRIGHTNESS_MULTIPLIER * 1.5, glow_intensity); // Mix in bright glow
             segment_color = clamp(segment_color, 0.0, 1.0); // Clamp again
        }


    } else {
        // Non-lit segment: completely black (no overlay)
        fragColor = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }

    // Output the final lit segment color
    fragColor = vec4(segment_color, 1.0);
}
