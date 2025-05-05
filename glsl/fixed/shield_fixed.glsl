// Shield shader - Fixed version
// Original by @XorDev
// Inspired by @cmzw's work: witter.com/cmzw_/status/1729148918225916406

void mainImage(out vec4 O, in vec2 I)
{
    // Iterator, z and time
    float i = 0.0;
    float z = 0.0;
    float t = iTime;

    // Clear frag color
    O = vec4(0.0, 0.0, 0.0, 0.0);

    // Loop 100 times
    for(i = 0.0; i < 1.0; i += 0.01)
    {
        // Resolution for scaling
        vec2 v = iResolution.xy;

        // Center and scale outward
        vec2 p = (I + I - v) / v.y * i;

        // Sphere distortion and compute z
        z = max(1.0 - dot(p, p), 0.0);
        p /= 0.2 + sqrt(z) * 0.3;

        // Offset for hex pattern
        p.x = p.x / 0.9 + t;
        p.y += fract(ceil(p.x) * 0.5) + t * 0.2;

        // Mirror quadrants
        v = abs(fract(p) - 0.5);

        // Add color and fade outward
        O += vec4(2.0, 3.0, 5.0, 1.0) / 2000.0 * z /
             (abs(max(v.x * 1.5 + v.y, v.x + v.y * 2.0) - 1.0) + 0.1 - i * 0.09);
    }

    // Tanh tonemap
    O = tanh(O * O);
}