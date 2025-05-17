



void mainImage(out vec4 O, in vec2 I)
{

    float t = iTime;

    float i = 0.0;

    float z = 0.0;

    float d = 0.0;

    float s = 0.0;


    vec2 uv = I / iResolution.xy;


    O = vec4(0.0);
    for(i = 0.0; i < 100.0; i++)
    {
        vec3 p = z * normalize(vec3((I - 0.5 * iResolution.xy) / iResolution.y, 1.0));

        for(d = 5.0; d < 200.0; d += d)
        {
            p += 0.6 * sin(p.yzx * d - 0.2 * t) / d;
        }

        s = 0.3 - abs(p.y);
        d = 0.005 + max(s, -s * 0.2) / 4.0;
        z += d;

        O += (cos(s / 0.07 + p.x + 0.5 * t - vec4(0.0, 1.0, 2.0, 3.0) - 3.0) + 1.5) * exp(s / 0.1) / d;
    }

    O = tanh(O * O / 400000000.0);
}
