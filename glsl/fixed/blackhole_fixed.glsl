// Black Hole shader - Fixed version
// This shader creates a black hole effect with accretion disk.

// Noise texture function (replacement for iChannel0)
float noise(vec3 p) {
    return fract(sin(dot(p, vec3(12.9898, 78.233, 45.5432))) * 43758.5453);
}

void mainImage(out vec4 O, in vec2 C)
{
    // Initialize vectors
    vec3 x = vec3(0.22, 0.97, 0.0);
    vec3 r = iResolution;
    vec3 d = vec3((C+C) - r.xy, -r.y) / r.x;
    vec3 p = d;

    // Reset r
    r = vec3(0.0);

    // Initialize variables
    float R = 0.0;
    float a = 0.05;
    float i = a;
    float t = iTime/4.0 + 5.0;

    // Main ray marching loop
    p.z += 4.0;
    for(; i < 200.0; i += 1.0) {
        // Move ray
        p += d/40.0;

        // Calculate radius
        R = dot(p, p);

        // Update a
        a *= min(R, 0.2) / 0.2;

        // Create transformation matrix A
        vec3 A = mix(x*dot(p,x), p, cos(t)) - sin(t)*cross(p,x);

        // Sample noise and update color
        float n1 = noise(A);
        float n03 = noise(A * 0.3);

        // Fix: max() returns a float, not a vector, so we can't use .y
        float maxVal = max(dot(A,A)*800.0, R);
        r += (2.0+d) * n1 * n03 * a / maxVal / R;

        // Update direction
        d -= p/(500.0*R*R);
    }

    // Final calculation
    p = d;
    vec3 A = mix(x*dot(p,x), p, cos(t)) - sin(t)*cross(p,x);
    float n02 = noise(A * 0.2);
    float n5 = noise(vec3(5.0/length(d)));

    O.gbr = max(r + (2.0+d) / (R*R+0.02/a-9.0) + a*A*n02, n5/0.2 - 4.0);
    O.a = 1.0; // Add alpha channel
}