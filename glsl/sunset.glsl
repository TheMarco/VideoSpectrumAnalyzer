/*
[C]by @XorDev
https://www.shadertoy.com/view/wXjSRt
[/C]
*/

// Sunset Shader - A beautiful sunset sky with clouds
// Based on techniques from various Shadertoy examples
// License: Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License

void mainImage(out vec4 O, in vec2 I)
{
    // Time for animation
    float t = iTime;
    // Raymarch iterator
    float i = 0.0;
    // Raymarch depth
    float z = 0.0;
    // Step distance
    float d = 0.0;
    // Signed distance
    float s = 0.0;
    
    // Normalized coordinates
    vec2 uv = I / iResolution.xy;
    
    // Clear fragcolor and raymarch with 100 iterations
    O = vec4(0.0);
    for(i = 0.0; i < 100.0; i++)
    {
        // Compute raymarch sample point
        vec3 p = z * normalize(vec3((I - 0.5 * iResolution.xy) / iResolution.y, 1.0));
        
        // Turbulence loop
        // https://www.shadertoy.com/view/3XXSWS
        for(d = 5.0; d < 200.0; d += d)
        {
            p += 0.6 * sin(p.yzx * d - 0.2 * t) / d;
        }
            
        // Compute distance (smaller steps in clouds when s is negative)
        s = 0.3 - abs(p.y);
        z += d = 0.005 + max(s, -s * 0.2) / 4.0;
        
        // Coloring with sine wave using cloud depth and x-coordinate
        O += (cos(s / 0.07 + p.x + 0.5 * t - vec4(0, 1, 2, 3) - 3.0) + 1.5) * exp(s / 0.1) / d;
    }
    
    // Tanh tonemapping
    // https://www.shadertoy.com/view/ms3BD7
    O = tanh(O * O / 4e8);
}
