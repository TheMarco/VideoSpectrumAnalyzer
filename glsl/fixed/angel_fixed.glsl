// Angel shader - Fixed version
// Original by @XorDev
// An experiment based on "3D Fire": https://www.shadertoy.com/view/3XXSWS

void mainImage(out vec4 O, in vec2 I)
{
    // Time for animation
    float t = iTime;
    // Raymarch iterator
    float i = 0.0;
    // Raymarch depth
    float z = 0.0;
    // Raymarch step size
    float d = 0.0;
    
    // Clear output color
    O = vec4(0.0, 0.0, 0.0, 0.0);
    
    // Raymarch loop (100 iterations)
    for(i = 0.0; i < 100.0; i += 1.0)
    {
        // Raymarch sample position
        vec3 p = z * normalize(vec3(I+I, 0.0) - iResolution.xyy);
        // Shift camera back
        p.z += 6.0;
        // Twist shape
        p.xz *= mat2(cos(p.y * 0.5 + vec4(0.0, 33.0, 11.0, 0.0)));
        
        // Distortion (turbulence) loop
        d = 1.0;
        for(float j = 0.0; j < 4.0; j += 1.0)
        {
            // Add distortion waves
            p += cos((p.yzx - t * vec3(3.0, 1.0, 0.0)) * d) / d;
            d /= 0.8;
        }
        
        // Compute distorted distance field of cylinder
        d = (0.1 + abs(length(p.xz) - 0.5)) / 20.0;
        z += d;
        
        // Sample coloring and glow attenuation
        O += (sin(z + vec4(2.0, 3.0, 4.0, 0.0)) + 1.1) / d;
    }
    
    // Tanh tonemapping
    O = tanh(O / 4000.0);
}
