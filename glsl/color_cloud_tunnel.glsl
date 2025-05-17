/*
[C]
by diatribes
https://www.shadertoy.com/view/w32XDc
[/C]
*/

// Helper function to create a point in 3D space
#define P(z) vec3(cos(vec2(.15,.2)*(z))*5.,z)

void mainImage(out vec4 o, vec2 u) {
    // Initialize variables
    float i = 0.0;
    float d = 0.0;
    float s = 0.0;
    float n = 0.0;
    float t = iTime * 3.0;
    
    // Initialize output color
    o = vec4(0.0, 0.0, 0.0, 0.0);
    
    // Setup camera and ray
    vec3 q = iResolution;
    vec3 p = P(t);
    vec3 Z = normalize(P(t+1.0) - p);
    vec3 X = normalize(vec3(Z.z, 0.0, -Z.x));
    vec3 D = vec3((u-q.xy/2.0)/q.y, 1.0) * mat3(-X, cross(X, Z), Z);
    
    // Ray marching loop
    for(i = 0.0; i < 100.0; i += 1.0) {
        // Move ray
        p += D * s;
        
        // Calculate new point
        q = P(p.z) + cos(t+p.yzx) * 0.3;
        
        // Calculate distance
        s = 2.0 - min(length((p-q).xy),
                 min(length(p.xy - q.y),
                     length(p.xy - q.x)));
        
        // Apply fractal distortion
        for (n = 0.1; n < 1.0; n += n) {
            s -= abs(dot(sin(p * n * 16.0), q-q+0.03)) / n;
        }
        
        // Update distance and color
        d += s = 0.04 + abs(s) * 0.2;
        o += (1.0 + cos(d + vec4(4.0, 2.0, 1.0, 0.0))) / s / d;
    }
    
    // Apply tone mapping
    o = tanh(o / 200.0);
}
