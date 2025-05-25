void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    // Buffer A resolution is typically small (e.g., 16x1 or 256x1).
    // Each pixel in Buffer A's output corresponds to a bar.

    // --- Constants (Match these with Image shader!) ---
    const int NUM_BARS = 24;
    const float OVERALL_MASTER_GAIN = 1.2;  // Reduced from 4.0 to 1.2 for more balanced response
    const float FREQ_GAIN_MIN_MULT = 0.5;   // Reduced from 0.7 to 0.5
    const float FREQ_GAIN_MAX_MULT = 0.7;   // Reduced from 0.9 to 0.7
    const float FREQ_GAIN_CURVE_POWER = 0.4;
    const float BAR_HEIGHT_POWER = 1.2;     // Increased from 0.8 to 1.2 for more dynamic range
    const float AMPLITUDE_COMPRESSION_POWER = 0.6; // Decreased from 0.8 to 0.6 for better quiet sound response

    // --- Peak Falloff Speed (Tune this!) ---
    // Rate at which the peak falls per second (normalized 0-1 height per second)
    const float PEAK_FALLOFF_RATE = 0.3; // Adjusted from 0.2 to 0.3 for more natural falloff

    // --- Calculate the bar index for this pixel in Buffer A ---
    // Map fragCoord.x to bar_index assuming Buffer A's width corresponds to NUM_BARS
    int bar_index = int(fragCoord.x * float(NUM_BARS) / iResolution.x);

    // Ensure bar_index is valid (should be if Buffer A width >= NUM_BARS)
    if (bar_index < 0 || bar_index >= NUM_BARS) {
        fragColor = vec4(0.0);
        return;
    }

    // --- Calculate Current Bar Height (Exact same logic as in Image shader) ---

    // Map bar index to frequency position for audio sampling
    // Use a more balanced frequency curve (1.5 instead of 1.7)
    float freq_pos = pow(float(bar_index) / float(NUM_BARS - 1), 1.5);

    // Sample raw amplitude from the Audio Channel (Input 0)
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

    // --- Read Previous Peak Height from Buffer A (feedback) ---
    // Read the previous frame's peak value from Input A (which IS Buffer A)
    // Use fragCoord.xy/iResolution.xy for normalized UV within Buffer A.

    // Initialize with a default value
    float previous_peak_height = 0.0;

    // Try to read from iChannel1 (Buffer A from previous frame)
    if (iFrame > 0) {  // Skip on the very first frame
        previous_peak_height = texture(iChannel1, fragCoord.xy / iResolution.xy).x;
    }

    // Debug: Force some movement in the first few frames
    if (iFrame < 5) {
        // Add some artificial movement for the first few frames
        previous_peak_height = max(previous_peak_height,
                                  sin(iTime * 5.0 + float(bar_index) * 0.2) * 0.5 + 0.5);
    }


    // --- Calculate New Peak Height ---

    // Hold: The new peak is the maximum of the current height and the previous peak
    float new_peak_height = max(current_bar_height_norm, previous_peak_height);

    // Fall: Subtract decay based on time elapsed since last frame (iTimeDelta)
    new_peak_height -= PEAK_FALLOFF_RATE * iTimeDelta;

    // Clamp: Ensure the peak stays between 0 and 1
    new_peak_height = clamp(new_peak_height, 0.0, 1.0);

    // --- Write New Peak Height to Buffer A ---
    // Store the peak height in the red channel (and others for convenience)
    fragColor = vec4(new_peak_height, new_peak_height, new_peak_height, 1.0);
}
