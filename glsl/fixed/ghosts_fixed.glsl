// Ghosts shader - Fixed version
// Original by @XorDev

void mainImage(out vec4 O, in vec2 I)
{
    // Time for animation
    float t = iTime;
    // Raymarch iterator
    float i = 0.0;
    // Raymarch depth
    float z = 0.0;
    // Raymarch step size and "Turbulence" frequency
    float d = 0.0;

    // Clear frag color
    O = vec4(0.0, 0.0, 0.0, 0.0);

    // Raymarch loop
    for (i = 0.0; i < 100.0; i += 1.0)
    {
        // Raymarch sample point
        vec3 p = z * normalize(vec3(I+I, 0.0) - iResolution.xyy);
        // Twist with depth
        p.xy *= mat2(cos((z + t) * 0.1 + vec4(0.0, 33.0, 11.0, 0.0)));
        // Scroll forward
        p.z -= 5.0 * t;

        // Turbulence loop
        d = 1.0;
        for (float j = 0.0; j < 4.0; j += 1.0)
        {
            p += cos(p.yzx * d + t) / d;
            d /= 0.7;
        }

        // Distance to irregular gyroid
        d = 0.02 + abs(2.0 - dot(cos(p), sin(p.yzx * 0.6))) / 8.0;
        z += d;

        // Add color and glow falloff
        O += vec4(z / 7.0, 2.0, 3.0, 1.0) / d;
    }

    // Tanh tonemapping
    O = tanh(O * O / 10000000.0);
}
