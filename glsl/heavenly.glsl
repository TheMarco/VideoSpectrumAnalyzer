/*
[C]by @XorDev
https://www.shadertoy.com/view/W3BSzy
[/C]
    "Heavenly" by @XorDev
*/
void mainImage(out vec4 O, vec2 I)
{
    // Time for animation
    float t = iTime;
    // Raymarch iterator
    float i = 0.0;
    // Raymarch depth
    float z = 0.0;
    // Step distance
    float d = 0.0;
    
    // Clear output color
    O = vec4(0.0, 0.0, 0.0, 0.0);
    
    // Raymarch with 100 iterations
    for(float i = 0.0; i < 100.0; i++)
    {
        // Compute raymarch sample point
        vec3 p = z * normalize(vec3(I+I, 0.0) - iResolution.xyy);
        
        // Offset z by time for animation
        p.z -= t;
        
        // Turbulence loop
        for(float d = 1.0; d < 9.0; d /= 0.7)
        {
            p += cos(p.yzx * d + z * 0.2) / d;
        }
        
        // Compute step distance
        d = 0.02 + 0.1 * abs(3.0 - length(p.xy));
        
        // Advance ray
        z += d;
        
        // Accumulate color
        O += (cos(z + t + vec4(6.0, 1.0, 2.0, 3.0)) + 1.0) / d;
    }
    
    // Apply tone mapping
    O = tanh(O / 3000.0);
}
