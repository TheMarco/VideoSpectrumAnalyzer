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

// Forward declaration of uniforms
// These will be set from the renderer
uniform int uNumBars;           // Number of bars around the circle
uniform int uSegmentsPerBar;    // Number of segments per bar
uniform float uInnerRadius;     // Inner radius of the circle (0-1)
uniform float uOuterRadius;     // Outer radius of the circle (0-1)
uniform float uBarWidth;        // Width of bars (0-1, where 1 means bars touch)
uniform float uBorderSize;      // Border size (0-0.2, where 0.1 means 10% of segment is border)
uniform float uDebugMode;       // Debug mode (0=off, 1=on)
uniform float uTime;            // Current time in seconds (for animation)
uniform float uSegmentSpacing;  // Spacing between segments in pixels

// Sensitivity uniform
uniform float uSensitivity; // Single sensitivity control

// Color uniforms
uniform vec3 uSegmentColor;     // Color for all lit segments
void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    // --- Mathematical Constants ---
    const float PI = 3.14159265359; // Defined PI

    // --- Constants ---
    // Use uniform values if set, otherwise fall back to constants
    int NUM_BARS = (uNumBars > 0) ? uNumBars : 36;
    int SEGMENTS_PER_BAR = (uSegmentsPerBar > 0) ? uSegmentsPerBar : 15;

    // Define the radial bounds of the analyzer ring (normalized 0-1 from center to edge)
    // These are relative to the distance from the center to the NEAREST screen edge after aspect correction.
    float INNER_RADIUS = (uInnerRadius > 0.0) ? uInnerRadius : 0.20; // Inner edge of the segments (0 is center)
    float OUTER_RADIUS = (uOuterRadius > 0.0) ? uOuterRadius : 0.40; // Outer edge of the segments (0.5 would reach top/bottom/left/right edge)

    // Angle offset for the start of the spectrum (e.g., 0.0 for right, PI/2.0 for top, PI for left, 3*PI/2.0 for bottom)
    // Let's start the lowest frequency bar at the bottom (3*PI/2) and go counter-clockwise.
    const float START_ANGLE_OFFSET = 3.0 * PI / 2.0; // Start at the bottom (270 degrees or -90 degrees)

    // Define spacing/borders relative to the SIZE OF THE RECTANGULAR CELL (0.0 to 1.0)
    // This refers to the local coordinate system within a single segment rectangle.
    float BORDER_SIZE = (uBorderSize > 0.0) ? uBorderSize : 0.08; // How much of the local cell is border space

    // Define bar width (0.0 to 1.0)
    // This refers to the width of bars relative to the available space
    float BAR_WIDTH = (uBarWidth > 0.0) ? uBarWidth : 0.8; // Width of bars (0-1, where 1 means bars touch)

    // --- Sensitivity Setting (Use uniform if set, otherwise use default) ---
    float SENSITIVITY = (uSensitivity > 0.0) ? uSensitivity : 1.0;

    // --- Color Settings ---
    // Use uniform value if set, otherwise fall back to default white
    vec3 SEGMENT_COLOR = (uSegmentColor.r >= 0.0 || uSegmentColor.g >= 0.0 || uSegmentColor.b >= 0.0) ?
                         uSegmentColor : vec3(1.0, 1.0, 1.0); // Color for all lit segments


    // --- Coordinate Mapping ---

    // Normalize coordinates (0..1, 0,0 is bottom-left)
    vec2 uv = fragCoord.xy / iResolution.xy;

    // Sample background color from channel 1 (image/video background)
    vec4 bg_color = texture(iChannel1, uv);

    // Enhanced debug function to visualize the audio texture at the bottom of the screen
    if (uDebugMode > 0.0 && uv.y < 0.15) {
        // Only show in the bottom 15% of the screen

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
            fragColor = vec4(0.0, amplitude, 1.0 - amplitude, 1.0);
            return;
        }

        // Draw a reference line at the top
        if (abs(uv.y - 0.15) < 0.002) {
            fragColor = vec4(1.0, 1.0, 1.0, 1.0);
            return;
        }

        // Draw a reference line at the bottom
        if (abs(uv.y - 0.001) < 0.001) {
            fragColor = vec4(0.5, 0.5, 0.5, 1.0);
            return;
        }

        // Draw markers for each bar's sampling position
        for (int i = 0; i < NUM_BARS; i++) {
            // Calculate the texel position for this bar
            float texels_per_bar = 512.0 / float(NUM_BARS);
            float texel_pos = (float(i) + 0.5) * texels_per_bar;
            float marker_pos = texel_pos / 512.0; // Normalize to 0-1

            // Draw a vertical line at each bar's sampling position
            if (abs(uv.x - marker_pos) < 0.001) {
                // Alternate colors for better visibility
                if (i % 2 == 0) {
                    fragColor = vec4(1.0, 1.0, 0.0, 1.0); // Yellow
                    return;
                } else {
                    fragColor = vec4(0.0, 1.0, 1.0, 1.0); // Cyan
                    return;
                }
            }

            // Draw bar index numbers for every 5th bar
            if (i % 5 == 0) {
                // Draw a small horizontal line
                if (abs(uv.x - marker_pos) < 0.005 && abs(uv.y - 0.02) < 0.002) {
                    fragColor = vec4(1.0, 1.0, 1.0, 1.0);
                    return;
                }
            }
        }

        // Background - more transparent and darker
        fragColor = vec4(0.05, 0.05, 0.05, 0.5);
        return;
    }

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

    // Debug visualization - only shown when debug mode is enabled
    if (uDebugMode > 0.5) {
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
        float brightness = ((r_normalized - INNER_RADIUS) / (OUTER_RADIUS - INNER_RADIUS)) * (0.7 + 0.3 * pulse);
        debug_color *= brightness;

        // Show the debug visualization
        fragColor = vec4(debug_color, 1.0);

        // Exit early in debug mode
        return;
    }

    // --- Determine Bar Index based on Angle ---

    // Normalize angle over the full circle (0.0 to 1.0) after applying offset
    // atan gives -PI to PI. Add PI to shift range to [0, 2*PI].
    // Then add START_ANGLE_OFFSET and wrap using mod. Normalize to 0..1.
    float angle_0_2PI = atan(centered_uv_scaled.y, centered_uv_scaled.x) + PI; // Recalculate directly to ensure precision
    float final_angle = mod(angle_0_2PI + START_ANGLE_OFFSET, 2.0 * PI); // Add offset and wrap
    float normalized_angle = final_angle / (2.0 * PI); // Normalize to [0, 1)

    // Integer index for bar (based on angle)
    int bar_index = int(floor(normalized_angle * float(NUM_BARS)));

    // Check valid bar index
     if (bar_index < 0 || bar_index >= NUM_BARS) {
         fragColor = bg_color; // Show background
         return;
     }

    // --- Determine Segment Index based on Radial Position ---

    // Convert segment spacing from pixels to normalized coordinates
    float pixel_to_normalized = 2.0 / min(iResolution.x, iResolution.y); // Convert pixels to normalized coordinates
    float normalized_segment_spacing = pixel_to_normalized * uSegmentSpacing;

    // Total available radius for segments
    float total_radius = OUTER_RADIUS - INNER_RADIUS;

    // Calculate segment height without spacing
    float raw_segment_height = total_radius / float(SEGMENTS_PER_BAR);

    // Calculate total space needed for spacing between all segments
    float total_spacing = normalized_segment_spacing * (float(SEGMENTS_PER_BAR) - 1.0);

    // Calculate actual segment height with spacing accounted for
    float segment_height = (total_radius - total_spacing) / float(SEGMENTS_PER_BAR);

    // Normalize radial position within the ring (0.0 at INNER_RADIUS, 1.0 at OUTER_RADIUS)
    float normalized_radial_pos = (r_normalized - INNER_RADIUS) / total_radius;

    // Calculate which segment this pixel belongs to
    int segment_index = -1;
    float segment_start = 0.0;
    float segment_end = 0.0;

    // Iterate through segments to find which one this pixel belongs to
    for (int i = 0; i < SEGMENTS_PER_BAR; i++) {
        segment_start = (float(i) * (segment_height + normalized_segment_spacing)) / total_radius;
        segment_end = segment_start + (segment_height / total_radius);

        if (normalized_radial_pos >= segment_start && normalized_radial_pos < segment_end) {
            segment_index = i;
            break;
        }
    }

    // If we're not in any segment, show background
    if (segment_index == -1) {
        fragColor = bg_color;
        return;
    }

    // --- Calculate Local UV and Bar Shape ---

    // The 'vertical' local coordinate (0..1) is based on the radial position within the segment
    // We don't need this anymore since we're using segment_start and segment_end
    float local_radial_uv = (normalized_radial_pos - segment_start) / (segment_end - segment_start);

    // --- Calculate Local Horizontal UV for Constant Width Bars ---
    // We need a horizontal coordinate that maps the arc length within the bar's sector
    // to a 0-1 range, such that the total arc length corresponding to 0-1 is constant
    // regardless of radius. This ensures rectangular (not trapezoid) bars.

    float bar_angle_span = 2.0 * PI / float(NUM_BARS);

    // Calculate the angle within the current bar's sector (range 0 to bar_angle_span)
    // Use the fact that normalized_angle * NUM_BARS has an integer part (bar_index)
    // and a fractional part (position within the angular sector).
    float angle_within_bar_sector = fract(normalized_angle * float(NUM_BARS)) * bar_angle_span;

    // For constant-width rectangular bars, we need to ensure the arc length is consistent
    // at all radii. We'll use the inner radius as our reference.

    // Calculate the center angle of the current bar
    float center_angle_of_bar = (float(bar_index) + 0.5) * bar_angle_span;

    // Calculate the angle from the current position to the center of the bar
    float angle_from_center = angle_within_bar_sector - (bar_angle_span / 2.0);

    // Calculate the arc length at the current radius
    float arc_length_at_current_radius = angle_from_center * r_normalized;

    // Calculate the maximum arc length at the inner radius (half the bar width)
    float max_arc_length = (bar_angle_span / 2.0) * INNER_RADIUS;

    // Normalize to get a value from -1 to 1 (where 0 is the center of the bar)
    float normalized_pos_in_bar = arc_length_at_current_radius / max_arc_length;

    // Map from -1..1 to 0..1 for UV coordinates
    float local_horizontal_uv = (normalized_pos_in_bar + 1.0) / 2.0;

    // --- Determine pixel color based on position within the constant-width bar rectangle ---

    // Check if the pixel is within the bar's horizontal bounds
    // The local_horizontal_uv is already normalized from 0 to 1 across the bar
    // Apply the BAR_WIDTH setting to create gaps between bars if needed

    // If local_horizontal_uv is outside the range [0,1], it's outside the bar's angular sector
    if (local_horizontal_uv < 0.0 || local_horizontal_uv > 1.0) {
        fragColor = bg_color; // Show background
        return;
    }

    // Apply bar width to create gaps if BAR_WIDTH < 1.0
    // Center the bar within its slot
    float half_gap = (1.0 - BAR_WIDTH) / 2.0;

    // If the pixel is in the gap area, show background
    if (local_horizontal_uv < half_gap || local_horizontal_uv > (1.0 - half_gap)) {
        fragColor = bg_color; // Show background for the gap
        return;
    }

    // Normalize the horizontal UV within the actual bar (not the slot)
    local_horizontal_uv = (local_horizontal_uv - half_gap) / BAR_WIDTH;

    // If we are within the bar slot [0, 1] horizontally, check if it's a border pixel.
    // The border check uses the local UVs within the conceptual 0-1 rectangle.
    if (local_horizontal_uv < BORDER_SIZE || local_horizontal_uv > 1.0 - BORDER_SIZE ||
        local_radial_uv < BORDER_SIZE || local_radial_uv > 1.0 - BORDER_SIZE)
    {
        // Use the background color for borders too - this ensures perfect transparency
        fragColor = bg_color;
        return;
    }

    // --- If we reach here, the pixel is inside the non-border part of the segment. ---
    // Continue with getting audio data and determining segment color.


    // --- Get Audio Data for the Current Bar ---

    // Map the bar index to a frequency position (0.0 to 1.0) in the audio texture.
    float freq_pos = pow(float(bar_index) / float(NUM_BARS - 1), 1.7); // Adjust 1.7 for visual frequency mapping

    // Sample raw amplitude from the audio texture
    float raw_amplitude = texture(iChannel0, vec2(freq_pos, 0.0)).x; // Audio from iChannel0

    // Debug: Force specific amplitudes for testing if debug mode is enabled
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

    // --- Apply Simple Sensitivity ---
    // Apply a simple sensitivity multiplier to the raw amplitude
    float final_amplitude = raw_amplitude * SENSITIVITY;

    // Clamp the final amplitude to be between 0 and 1
    final_amplitude = clamp(final_amplitude, 0.0, 1.0);

    // --- Determine how many segments are lit based on final amplitude ---
    int lit_segments_count = int(floor(final_amplitude * float(SEGMENTS_PER_BAR)));

    // --- Determine the final pixel color ---

    // Lighting logic: segment_index 0 is innermost.
    // The innermost segment (segment_index == 0) is always lit.
    if (segment_index < lit_segments_count || segment_index == 0) {
        // This segment should be lit (either due to amplitude or because it's the innermost).
        // Use the single segment color for all lit segments

        // Output lit segments with full opacity
        fragColor = vec4(SEGMENT_COLOR, 1.0);
    } else {
        // This segment is not lit - use the background color directly
        // This ensures perfect blending with the background
        fragColor = bg_color;
    }
}
