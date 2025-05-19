// Modifications by Marco van Hylckama Vlieg
// Follow me on X: https://x.com/AIandDesign
//
// Made with Google Gemini 2.5 Flash
// Original credits from 'Electro', the shader this was based on.
//
// Port of Humus Electro demo http://humus.name/index.php?page=3D&ID=35
// Not exactly right as the noise is wrong, but is the closest I could make it.
// Uses Simplex noise by Nikita Miropolskiy https://www.shadertoy.com/view/XsX3zB

/* Simplex code license
 * This work is licensed under a
 * Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License
 * http://creativecommons.org/licenses/by-nc-sa/3.0/
 *  - You must attribute the work in the source code
 *    (link to https://www.shadertoy.com/view/XsX3zB).
 *  - You may not use this work for commercial purposes.
 *  - You may distribute a derivative work only under the same license.
 */

// Add a uniform for frame persistence
// This will be used to blend the current frame with the previous frame
// Higher values (closer to 1.0) mean more persistence/trailing effect

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    // Normalize pixel coordinates [0, 1]
    vec2 uv = fragCoord.xy / iResolution.xy;

    // Sample the previous frame (if available)
    // We'll use this for the persistence effect
    vec4 prevFrame = texture(iChannel1, uv);

    // Transform vertical UV to [-1, 1] space for easier centering and amplitude mapping.
    // X UV stays [0, 1] for audio sampling.
    // Use exactly the same transformation as the original shader
    vec2 uv_centered = vec2(uv.x, uv.y * 3.0 - 1.0);

    // --- Audio Sampling ---
    // Sample the audio buffer based on the X-coordinate of the screen.
    // iChannel0 typically arranges audio data by time along its X-axis.
    // The Y-coordinate for sampling audio is usually 0.5 (middle of the 1-pixel height).
    float audio_time = uv.x;

    // Apply smoothing by sampling neighboring pixels and averaging
    float audio_sample = 0.0;

    if (iSmoothingFactor > 0.0) {
        // Calculate the number of samples to average based on smoothing factor
        // Higher smoothing factor = more samples
        // For standard settings, we use a high smoothing factor (0.8)
        float smoothing_factor = iUseOriginalSettings > 0.5 ? 0.8 : iSmoothingFactor;
        float sample_count = 1.0 + smoothing_factor * 20.0; // Using multiplier of 20.0 for noticeable effect
        float sample_step = 1.0 / iResolution.x; // Step size for neighboring samples

        // Sample neighboring pixels and average
        for (float i = -sample_count/2.0; i <= sample_count/2.0; i += 1.0) {
            float sample_pos = clamp(audio_time + i * sample_step, 0.0, 1.0);
            audio_sample += texture(iChannel0, vec2(sample_pos, 1.5)).x;
        }

        // Average the samples
        audio_sample /= (sample_count + 1.0);

        // Debug output - add a visual indicator when smoothing is applied
        // This will create a small red dot in the top-left corner when smoothing is active
        if (uv.x < 0.05 && uv.y < 0.05) {
            audio_sample = 0.8; // Create a visible marker
        }
    } else {
        // No smoothing, just sample the current pixel
        audio_sample = texture(iChannel0, vec2(audio_time, 1.5)).x;
    }

    // --- Waveform Mapping ---
    // Map the audio amplitude [-1, 1] to a vertical position in the uv_centered [-1, 1] space.
    // Increased default amplitude scale to match the screenshot

    // Calculate the target vertical position for the waveform in [-1, 1] UV space.
    float audio_amplitude_uv_scale = 4.0; // Updated to match new standard settings

    // Apply user's amplitude scale only if not using standard settings
    // Note: iUseOriginalSettings now represents whether to use standard settings
    if (iUseOriginalSettings < 0.5) {
        audio_amplitude_uv_scale = iAmplitudeScale;
    }

    // Scale the audio sample by the amplitude scale
    // This will make the waveform taller or shorter based on the scale
    float target_uv_y = audio_sample * audio_amplitude_uv_scale;

    // Apply the vertical offset from the uniform
    // For standard settings, use a vertical offset of -1.5
    float vertical_offset = iUseOriginalSettings > 0.5 ? -1.5 : iVerticalOffset;
    target_uv_y = target_uv_y + vertical_offset;

    // --- Drawing the Line and Glow (Mimicking the specific style) ---
    // Calculate the vertical distance 'y' from the current pixel's uv_centered.y to the target_uv_y.
    // This 'y' is the distance in the normalized [-1, 1] vertical space, always non-negative.
    float y = abs(uv_centered.y - target_uv_y);

    // --- Control Thickness and Glow ---
    // This scaling factor influences the thickness of the line and the spread of the glow.
    // A *smaller* value here makes the line thicker and more glowy.
    // A *larger* value makes the line thinner and the glow tighter.

    // Set thickness scale based on standard settings
    float thickness_scale = 0.1; // Updated to match new standard settings - smaller value for thicker line

    // Apply user's thickness scale only if not using standard settings
    if (iUseOriginalSettings < 0.5) {
        thickness_scale = iThicknessScale;
    }

    // Apply line thickness as a multiplier to make the effect more dramatic
    // Line thickness is expected to be in the range 1-10, with higher values making the line thicker
    #ifdef iLineThickness
        // For standard settings, use line thickness of 10
        float line_thickness = iUseOriginalSettings > 0.5 ? 10.0 : iLineThickness;

        // Convert line thickness (1-10) to a multiplier (1.0-0.1)
        // This makes higher line thickness values result in thicker lines
        float thickness_multiplier = 1.0 / line_thickness;
        thickness_scale *= thickness_multiplier;
    #endif

    // Multiply the distance 'y' by the thickness scale *before* feeding it into pow(..., 0.2)
    // This scales the effective distance used in the falloff calculation.
    // A smaller thickness_scale value makes the line thicker
    y *= thickness_scale;

    // Debug output - add visual indicators for thickness parameters
    // This will create a small green dot in the top-right corner when thickness scale is < 0.3
    if (uv.x > 0.95 && uv.y < 0.05 && thickness_scale < 0.3) {
        y = 0.01; // Create a visible marker
    }

    // This will create a small blue dot in the bottom-right corner when line thickness is > 2
    #ifdef iLineThickness
        if (uv.x > 0.95 && uv.y > 0.95 && iLineThickness > 2.0) {
            y = 0.01; // Create a visible marker
        }
    #endif

    // Calculate 'g' based on the scaled distance, using a slightly modified power function
    // This value 'g' is small near the line (where y is small) and grows as distance increases.
    // Adjusted from 0.2 to 0.18 to create a sharper core with slightly wider glow
    float g = pow(y, 0.18);

    // Calculate the intensity based on 'g'. Intensity is high (near 1.0) when 'g' is low (near the line).
    // Clamp to 0.0 just in case g somehow exceeds 1, although unlikely with typical distances.
    float intensity = max(0.0, 1.0 - g);

    // Define standard color (light yellow) based on user's preferred settings
    // The values > 1.0 are crucial for the intense glow effect after the power step.
    vec3 standard_color = vec3(1.0, 1.0, 0.9) * 1.7; // Light yellow color amplified for glow

    // Allow user to override with their own color if not using standard settings
    vec3 base_color;
    if (iUseOriginalSettings > 0.5) {
        // Use the standard color
        base_color = standard_color;
    } else {
        // Use the user's selected color
        base_color = iLineColor.rgb * 1.5; // Amplify for glow effect
    }

    // Apply the color calculation structure from your second shader: col * (1-g) followed by pow(col, 4)
    // This creates the sharp, intense core and rapid glow fade.
    vec3 final_color = base_color * intensity;
    final_color *= final_color; // Square
    final_color *= final_color; // Square again (Total power of 4)

    // --- Sample the background texture ---
    vec4 bg_color = texture(iChannel2, uv);  // Changed from iChannel1 to iChannel2 for background

    // --- Create the current frame with waveform and background ---
    vec3 current_frame_color = bg_color.rgb + final_color;

    // --- Apply persistence effect by blending with previous frame ---
    // Use the persistence factor from the uniform (0.0 = no persistence, higher values = more persistence)
    // If iPersistence is not available, default to 0.7
    float persistence = 0.7;

    // Use iPersistence uniform if available (passed from the renderer)
    // The uniform is defined in the fragment shader template in simple_gl_renderer.py
    persistence = iPersistence;

    // Blend current frame with previous frame
    vec3 persistent_color = mix(current_frame_color, prevFrame.rgb, persistence);

    // --- Final Pixel Color ---
    fragColor = vec4(persistent_color, 1.0);
}
