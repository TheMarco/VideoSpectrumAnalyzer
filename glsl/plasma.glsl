/*
    "Plasma" by @XorDev - Fixed version

    X Post:
    x.com/XorDev/status/1894123951401378051

*/
void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    // Resolution for scaling
    vec2 r = iResolution.xy;

    // Centered, ratio corrected, coordinates
    vec2 p = (fragCoord + fragCoord - r) / r.y;

    // Z depth
    vec2 z = vec2(0.0);

    // Fluid coordinates
    z.x += 4.0 - 4.0 * abs(0.7 - dot(p, p));
    vec2 f = p * z.x;

    // Initialize output color
    fragColor = vec4(0.0);

    // Iterator
    vec2 i = vec2(0.0, 0.0);

    // Loop 8 times
    for(int j = 0; j < 8; j++) {
        i.y = float(j + 1);

        // Set color waves and line brightness
        vec4 colorWave = vec4(sin(f.x) + 1.0, sin(f.y) + 1.0, sin(f.x) + 1.0, sin(f.y) + 1.0);
        fragColor += colorWave * abs(f.x - f.y);

        // Add fluid waves
        f += cos(f.yx * i.y + i + iTime) / i.y + 0.7;
    }

    // Tonemap, fade edges and color gradient
    vec4 colorGradient = vec4(-1.0, 1.0, 2.0, 0.0);
    fragColor = tanh(7.0 * exp(z.x - 4.0 - p.y * colorGradient) / fragColor);
}
