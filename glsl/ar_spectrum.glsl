/* By Marco van Hylckama Vlieg
   using Google Gemini 2.5 Pro
   Follow me on X: https://x.com/AIandDesign
*/

// [C]
// Classic Spectrum Analyzer
// by Marco van Hylckama Vlieg
// https://x.com/AIandDesign
// [/C]

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    // Normalize coordinates (0 to 1)
    vec2 uv = fragCoord.xy / iResolution.xy;

    // uv.y is 0 at the bottom, 1 at the top (standard fragCoord behavior)

    // --- Constants (Match these with Buffer A shader!) ---
    const int NUM_BARS = 24;
    const int SEGMENTS_PER_BAR = 20;

    // Define vertical position and height (using standard Y, 0=bottom)
    const float ANALYZER_BOTTOM_Y = 0.05;
    const float ANALYZER_HEIGHT   = 0.4;

    // Define horizontal position and width (using standard X, 0=left)
    const float ANALYZER_LEFT_X   = 0.1;
    const float ANALYZER_WIDTH_X  = 0.8;

    // Define spacing/borders relative to cell size
    const float BORDER_SIZE = 0.2;

    // --- Sensitivity and Gain Settings (Tune these carefully!) ---
    // Must match Buffer A shader!
    const float OVERALL_MASTER_GAIN = 1.2;  // Reduced from 4.0 to 1.2 for more balanced response
    const float FREQ_GAIN_MIN_MULT = 0.5;   // Reduced from 0.7 to 0.5
    const float FREQ_GAIN_MAX_MULT = 0.7;   // Reduced from 0.9 to 0.7
    const float FREQ_GAIN_CURVE_POWER = 0.4;
    const float BAR_HEIGHT_POWER = 1.2;     // Increased from 0.8 to 1.2 for more dynamic range
    const float AMPLITUDE_COMPRESSION_POWER = 0.6; // Decreased from 0.8 to 0.6 for better quiet sound response


    // --- Color Settings ---
    const vec3 COLOR_LIT_DARK    = vec3(0.0, 0.4, 0.4); // Base color for lit segments (bottom)
    const vec3 COLOR_LIT_BRIGHT  = vec3(0.2, 1.0, 1.0); // Color for lit segments (top) - brighter teal/cyan
    const vec3 COLOR_UNLIT        = vec3(0.0, 0.08, 0.08); // Slightly visible dark teal/cyan for unlit
    const vec3 COLOR_BORDER       = vec3(0.0, 0.0, 0.0); // Pure black

    // Peak Indicator Color (Tune this!)
    const vec3 COLOR_PEAK         = vec3(0.0, 0.8, 0.8); // *** Changed from Yellow to a Bright Teal ***

    // Optional: Brightness multiplier for main lit segments
    const float LIT_BRIGHTNESS_MULTIPLIER = 1.2;


    // --- Bounds Check: Is the pixel inside the analyzer's area? ---
    if (uv.x < ANALYZER_LEFT_X || uv.x > ANALYZER_LEFT_X + ANALYZER_WIDTH_X ||
        uv.y < ANALYZER_BOTTOM_Y || uv.y > ANALYZER_BOTTOM_Y + ANALYZER_HEIGHT)
    {
        fragColor = vec4(0.0, 0.0, 0.0, 1.0); // Black background outside the analyzer area
        return;
    }

    // --- Map the pixel coordinate to the analyzer grid ---

    // Normalize uv within the analyzer's band (0 to 1 for the band)
    float analyzer_uv_x = (uv.x - ANALYZER_LEFT_X) / ANALYZER_WIDTH_X;
    float analyzer_uv_y = (uv.y - ANALYZER_BOTTOM_Y) / ANALYZER_HEIGHT;

    // Scale normalized analyzer UV to the grid dimensions
    vec2 grid_uv = vec2(analyzer_uv_x * float(NUM_BARS),
                        analyzer_uv_y * float(SEGMENTS_PER_BAR));

    // Integer indices for bar and segment
    int bar_index = int(floor(grid_uv.x));
    int segment_index = int(floor(grid_uv.y)); // segment_index 0 is at the bottom of the analyzer band

    // Local UV within a single bar/segment cell (0 to 1 for each cell)
    vec2 local_uv = fract(grid_uv);

    // --- Check valid bar index (segment index already checked by initial Y bound) ---
     if (bar_index < 0 || bar_index >= NUM_BARS) {
        fragColor = vec4(COLOR_BORDER, 1.0); // Should not happen if initial bounds check works
        return;
    }

    // --- Check if pixel is part of the border ---
    if (local_uv.x < BORDER_SIZE || local_uv.x > 1.0 - BORDER_SIZE ||
        local_uv.y < BORDER_SIZE || local_uv.y > 1.0 - BORDER_SIZE)
    {
        fragColor = vec4(COLOR_BORDER, 1.0); // Draw border color
        return;
    }

    // --- Get Current Bar Height (Exact same logic as in Buffer A shader) ---

    // Map bar index to frequency position
    // Use a more balanced frequency curve (1.5 instead of 1.7)
    float freq_pos = pow(float(bar_index) / float(NUM_BARS - 1), 1.5);

    // Sample raw amplitude
    float raw_amplitude = texture(iChannel0, vec2(freq_pos, 0.0)).x; // Audio from iChannel0

    // Apply a noise gate to filter out very low amplitudes
    float noise_gate = 0.01;
    raw_amplitude = max(0.0, raw_amplitude - noise_gate);

    // Apply a soft knee compression curve
    float threshold = 0.6;
    float knee = 0.2;
    float ratio = 0.5; // Higher values = less compression
    float makeup_gain = 1.2;

    float knee_start = threshold - knee / 2.0;
    float knee_end = threshold + knee / 2.0;

    float compressed_amplitude;
    if (raw_amplitude < knee_start) {
        compressed_amplitude = raw_amplitude;
    } else if (raw_amplitude < knee_end) {
        float t = (raw_amplitude - knee_start) / knee;
        compressed_amplitude = knee_start + t * t * knee / 2.0;
    } else {
        compressed_amplitude = knee_end + (raw_amplitude - knee_end) * ratio;
    }

    // Apply amplitude compression power curve
    float processed_amplitude = pow(compressed_amplitude * makeup_gain, AMPLITUDE_COMPRESSION_POWER);

    // Apply frequency-dependent gain with a more balanced curve
    float bar_norm = float(bar_index) / float(NUM_BARS - 1);
    float curved_bar_norm = pow(bar_norm, FREQ_GAIN_CURVE_POWER);
    float freq_gain_multiplier = mix(FREQ_GAIN_MIN_MULT, FREQ_GAIN_MAX_MULT, curved_bar_norm);
    float amplitude_after_gain = processed_amplitude * OVERALL_MASTER_GAIN * freq_gain_multiplier;

    // Apply bar height power curve for more dynamic response
    float current_bar_height_norm = pow(amplitude_after_gain, BAR_HEIGHT_POWER); // Height 0.0 to 1.0

    // Clamp current height
    current_bar_height_norm = clamp(current_bar_height_norm, 0.0, 1.0);

    // Convert normalized height to segments
    int lit_segments_count = int(floor(current_bar_height_norm * float(SEGMENTS_PER_BAR)));


    // --- Read Peak Height from Buffer A ---
    // Read the peak height stored in Buffer A for this bar index from iChannel1
    // *** This requires Input A for the Image pass to be set to "Buffer A". ***
    // Buffer A resolution is typically small. Sample it based on the bar index.
    // Use +0.5 and divide by resolution to sample the center of the pixel for this bar.
    float peak_height_norm = current_bar_height_norm; // Default to current height if buffer not available

    // Check if iChannel1 is available and has valid dimensions
    if (textureSize(iChannel1, 0).x > 1) {
        peak_height_norm = texture(iChannel1, vec2((float(bar_index) + 0.5) / float(NUM_BARS), 0.5)).x; // *** Reads from iChannel1 (Input A) ***
    }

    // Convert normalized peak height to segments
    int peak_segments_count = int(floor(peak_height_norm * float(SEGMENTS_PER_BAR)));


    // --- Determine the final pixel color ---

    vec3 segment_color;

    // Lighting logic: segment_index 0 is at the bottom.
    // Check for peak indicator first.
    // The peak segment is the one at peak_segments_count.
    // Only draw the peak indicator if it's at or above the current main bar height.
    if (segment_index == peak_segments_count && peak_segments_count >= lit_segments_count && peak_segments_count >= 0) {
        // This segment is the peak indicator, and it's at or above the main bar height
         segment_color = COLOR_PEAK;

    } else if (segment_index < lit_segments_count) {
        // This segment is part of the main lit bar (below the peak if peak is higher)
        // Choose color based on segment height
        float segment_norm_height = float(segment_index) / float(SEGMENTS_PER_BAR);

        // Lit color gradient
        segment_color = mix(COLOR_LIT_DARK, COLOR_LIT_BRIGHT, segment_norm_height);

        // Apply brightness multiplier for lit segments
         segment_color *= LIT_BRIGHTNESS_MULTIPLIER;
         segment_color = clamp(segment_color, 0.0, 1.0); // Clamp after multiplying

    } else {
        // This segment is not lit by the main bar or the peak. Draw the unlit color.
        segment_color = COLOR_UNLIT;
    }

    // Output the final color
    fragColor = vec4(segment_color, 1.0);
}
