/*
[C]by @XorDev
https://www.shadertoy.com/view/wXSXzV
[/C]
*/
// Nebula shader - Fixed version
// Original by @XorDev
// Based on tweet shader: https://x.com/XorDev/status/1918766627828515190

void mainImage(out vec4 O, in vec2 I)
{
    // Initialize variables
    float t = iTime;
    float i = 0.0;
    float z = 0.0;
    float d = 0.0;
    float s = 0.0;
    
    // Clear output color
    O = vec4(0.0, 0.0, 0.0, 0.0);
    
    // Main loop
    for(i = 0.0; i < 100.0; i += 1.0)
    {
        // Calculate ray position
        vec3 p = z * normalize(vec3(I+I, 0.0) - iResolution.xyy);
        
        // Offset by time
        p.z -= t;
        
        // Apply fractal distortion
        d = 1.0;
        for(float j = 0.0; j < 6.0; j += 1.0) // Limit iterations for performance
        {
            p += 0.7 * cos(p.yzx * d) / d;
            d *= 2.0; // Double the frequency each iteration
        }
        
        // Rotate based on depth
        p.xy *= mat2(cos(z * 0.2 + vec4(0.0, 11.0, 33.0, 0.0)));
        
        // Calculate distance and update s
        s = 3.0 - abs(p.x);
        
        // Update distance and depth
        d = 0.03 + 0.1 * max(s, -s * 0.2);
        z += d;
        
        // Add color
        O += (cos(s+s - vec4(5.0, 0.0, 1.0, 3.0)) + 1.4) / d / z;
    }
    
    // Apply tone mapping
    O = tanh(O * O / 400000.0);
}
