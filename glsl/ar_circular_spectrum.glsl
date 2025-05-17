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
// ANOTHER CHANGE: Made the most inner segment of each bar 'always on'.
//
// [C]
// Circular Spectrum Analyzer
// by Marco van Hylckama Vlieg
// https://x.com/AIandDesign
// [/C]
//
void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    // --- Mathematical Constants ---
    const float PI = 3.14159265359; // Defined PI

    // --- Constants ---
    const int NUM_BARS = 36;
    const int SEGMENTS_PER_BAR = 15;

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
    const vec3 COLOR_UNLIT        = vec3(0.08, 0.08, 0.08); // Slightly visible dark teal/cyan for unlit
    const vec3 COLOR_BORDER       = vec3(0.0, 0.0, 0.0); // Pure black

    // Optional: Brightness multiplier for lit segments to make them stand out
    const float LIT_BRIGHTNESS_MULTIPLIER = 1.3;


    // --- Coordinate Mapping ---

    // Normalize coordinates (0..1, 0,0 is bottom-left)
    vec2 uv = fragCoord.xy / iResolution.xy;

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
        fragColor = vec4(0.0, 0.0, 0.0, 1.0); // Black background outside the ring
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

    // Check valid bar index
     if (bar_index < 0 || bar_index >= NUM_BARS) {
         fragColor = vec4(0.0, 0.0, 0.0, 1.0); // Should not happen if r_normalized check works
         return;
     }

    // --- Determine Segment Index based on Radial Position ---

    // Normalize radial position within the ring (0.0 at INNER_RADIUS, 1.0 at OUTER_RADIUS)
    float normalized_radial_pos_in_ring = (r_normalized - INNER_RADIUS) / (OUTER_RADIUS - INNER_RADIUS);

    // Integer index for the segment (based on this normalized radial position)
    // Segment 0 is innermost.
    int segment_index = int(floor(normalized_radial_pos_in_ring * float(SEGMENTS_PER_BAR)));

    // Check valid segment index
     if (segment_index < 0 || segment_index >= SEGMENTS_PER_BAR) {
         fragColor = vec4(0.0, 0.0, 0.0, 1.0); // Should not happen if r_normalized check works
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
        fragColor = vec4(0.0, 0.0, 0.0, 1.0); // Black background for the gap
        return;
    }

    // If we are within the bar slot [0, 1] horizontally, check if it's a border pixel.
    // The border check uses the local UVs within the conceptual 0-1 rectangle.
    if (local_horizontal_uv < BORDER_SIZE || local_horizontal_uv > 1.0 - BORDER_SIZE ||
        local_radial_uv < BORDER_SIZE || local_radial_uv > 1.0 - BORDER_SIZE)
    {
        fragColor = vec4(COLOR_BORDER, 1.0); // Draw border color
        return;
    }

    // --- If we reach here, the pixel is inside the non-border part of the segment. ---
    // Continue with getting audio data and determining segment color.


    // --- Get Audio Data for the Current Bar ---

    // Map the bar index to a frequency position (0.0 to 1.0) in the audio texture.
    float freq_pos = pow(float(bar_index) / float(NUM_BARS - 1), 1.7); // Adjust 1.7 for visual frequency mapping

    // Sample raw amplitude from the audio texture
    float raw_amplitude = texture(iChannel0, vec2(freq_pos, 0.0)).x; // Audio from iChannel0

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
    int lit_segments_count = int(floor(final_amplitude * float(SEGMENTS_PER_BAR)));

    // --- Determine the final pixel color ---

    vec3 segment_color;

    // Lighting logic: segment_index 0 is innermost.
    // The innermost segment (segment_index == 0) is always lit.
    if (segment_index < lit_segments_count || segment_index == 0) { // MODIFIED CONDITION HERE
        // This segment should be lit (either due to amplitude or because it's the innermost).
        // Choose color based on segment index (0=inner, 19=outer segment)
        float segment_norm_height = float(segment_index) / float(SEGMENTS_PER_BAR); // 0 for inner segment, approaches 1 for outer

        // Lit color gradient (from inner dark to outer bright teal)
        segment_color = mix(COLOR_LIT_DARK, COLOR_LIT_BRIGHT, segment_norm_height);

        // Apply brightness multiplier for lit segments
        segment_color *= LIT_BRIGHTNESS_MULTIPLIER;
        segment_color = clamp(segment_color, 0.0, 1.0); // Clamp after multiplying

    } else {
        // This segment is not lit. Draw the slightly visible unlit color.
        segment_color = COLOR_UNLIT;
    }

    // Output the final color
    fragColor = vec4(segment_color, 1.0);
}
