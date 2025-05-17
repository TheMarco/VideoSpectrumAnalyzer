/*
    "Singularity" by @XorDev

    A whirling blackhole.
    Feel free to code golf!

    FabriceNeyret2: -19
    dean_the_coder: -12
    iq: -4
*/

void mainImage(out vec4 O, vec2 F)
{
    float i = 0.2;
    float a;

    vec2 r = iResolution.xy,
         p = (F + F - r) / r.y / 0.7,
         d = vec2(-1.0, 1.0),
         b = p - i * d,
         c = p * mat2(1, 1, d / (0.1 + i / dot(b,b))),
         v = c * mat2(cos(0.5 * log(a=dot(c,c)) + iTime * i + vec4(0.0, 33.0, 11.0, 0.0))) / i,
         w;

    for(; i++ < 9.0; w += 1.0 + sin(v))
        v += 0.7 * sin(v.yx * i + iTime) / i + 0.5;

    i = length(sin(v / 0.3) * 0.4 + c * (3.0 + d));

    O = 1.0 - exp(-exp(c.x * vec4(0.6, -0.4, -1.0, 0.0))
                   / w.xyyx
                   / (2.0 + i * i / 4.0 - i)
                   / (0.5 + 1.0 / a)
                   / (0.03 + abs(length(p) - 0.7))
             );
    }

