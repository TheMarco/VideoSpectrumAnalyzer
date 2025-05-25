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

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    // Normalize pixel coordinates [0, 1]
    vec2 uv = fragCoord.xy / iResolution.xy;    
    
    // Transform vertical UV to [-1, 1] space for easier centering and amplitude mapping.
    // X UV stays [0, 1] for audio sampling.
    vec2 uv_centered = vec2(uv.x, uv.y * 3.0 - 1.0);  

    // --- Audio Sampling ---
    // Sample the audio buffer based on the X-coordinate of the screen.
    // iChannel0 typically arranges audio data by time along its X-axis.
    // The Y-coordinate for sampling audio is usually 0.5 (middle of the 1-pixel height).
    float audio_time = uv.x; 
    float audio_sample = texture(iChannel0, vec2(audio_time, 1.5)).x; // Sample audio (assuming mono in .x)

    // --- Waveform Mapping ---
    // Map the audio amplitude [-1, 1] to a vertical position in the uv_centered [-1, 1] space.
    // Adjust audio_amplitude_uv_scale to make the overall audio waveform taller or shorter.
    // 0.8 means the wave will take up 80% of the screen height when audio peaks.
    float audio_amplitude_uv_scale = 1.0; // Tweak this value if you want it taller or shorter
    
    // Calculate the target vertical position for the waveform in [-1, 1] UV space.
    float target_uv_y = audio_sample * audio_amplitude_uv_scale;

    // --- Drawing the Line and Glow (Mimicking the specific style) ---
    // Calculate the vertical distance 'y' from the current pixel's uv_centered.y to the target_uv_y.
    // This 'y' is the distance in the normalized [-1, 1] vertical space, always non-negative.
    float y = abs(uv_centered.y - target_uv_y);
    
    // --- Control Thickness and Glow ---
    // This scaling factor influences the thickness of the line and the spread of the glow.
    // A *smaller* value here makes the line thicker and more glowy.
    // A *larger* value makes the line thinner and the glow tighter.
    // We set it to the requested 0.3.
    float thickness_scale = 0.3; // Set to the desired thickness multiplier (0.3 for thicker glow)

    // Multiply the distance 'y' by the thickness scale *before* feeding it into pow(..., 0.2)
    // This scales the effective distance used in the falloff calculation.
    y *= thickness_scale;

    // Calculate 'g' based on the scaled distance, using the original shader's pow(y, 0.2).
    // This value 'g' is small near the line (where y is small) and grows as distance increases.
    float g = pow(y, 0.2); 

    // Calculate the intensity based on 'g'. Intensity is high (near 1.0) when 'g' is low (near the line).
    // Clamp to 0.0 just in case g somehow exceeds 1, although unlikely with typical distances.
    float intensity = max(0.0, 1.0 - g);

    // Define the base color exactly as in your second shader.
    // The values > 1.0 are crucial for the intense glow effect after the power step.
    vec3 base_color = vec3(1.70, 1.48, 1.78); // The specific purple/pink-ish base color

    // Apply the color calculation structure from your second shader: col * (1-g) followed by pow(col, 4)
    // This creates the sharp, intense core and rapid glow fade.
    // base_color * intensity is equivalent to base_color * (1.0 - g) which was the original structure (col * -g + col is col * (1-g))
    vec3 final_color = base_color * intensity; 
    final_color *= final_color; // Square
    final_color *= final_color; // Square again (Total power of 4)

    // --- Final Pixel Color ---
    // The background is black where final_color is close to 0.
    fragColor = vec4(final_color, 1.0);                          
}
