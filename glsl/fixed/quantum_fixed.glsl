// Quantum shader - Fixed version
// Original by @XorDev

void mainImage(out vec4 O, in vec2 I)
{
    // Initialize vectors
    vec3 p = vec3(0.0);
    vec3 q = vec3(0.0);
    vec3 r = iResolution;
    
    // Initialize variables
    float i = 1.0;
    float j = 1.0;
    float z = 0.0;
    
    // Clear output color
    O = vec4(0.0, 0.0, 0.0, 0.0);
    
    // Main loop
    for(i = 1.0; i > 0.0; i -= 0.02)
    {
        // Calculate z value
        p = (vec3(I+I, 0.0) - r) / r.y;
        z = i - dot(p, p);
        z = max(z, -z/1e5);
        z = sqrt(z);
        p.z = z;
        
        // Transform p
        p /= 2.0 + z;
        
        // Rotate p.xz
        float ct = cos(iTime);
        float st = sin(iTime);
        float ct2 = cos(iTime + 11.0);
        float st2 = sin(iTime + 11.0);
        p.xz = mat2(ct, -st2, st, ct2) * p.xz;
        
        // Update q and calculate j
        q += p;
        j = cos(j * dot(cos(q), sin(q.yzx)) / 0.3);
        
        // Add color
        vec4 color = vec4(0.0, 0.0, 0.0, 0.0);
        color = sin(i * 30.0 + vec4(0.0, 1.0, 2.0, 3.0)) + 1.0;
        color *= i * pow(z, 0.4) * pow(j + 1.0, 8.0) / 2000.0;
        O += color;
    }
    
    // Final color adjustment
    O *= O;
}
