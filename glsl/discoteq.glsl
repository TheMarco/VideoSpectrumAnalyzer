[C]
By beans_please
https://www.shadertoy.com/view/ctjfDc
[/C]

#define S smoothstep
#define R iResolution.xy
#define T iTime

float c(vec2 u) { return  S( 5./R.y, 0., abs(length(u) - .25)); }
float t (float s) { return .5 + sin(T * s) * .5; }
mat2 r (float a) { return mat2(cos(a), sin(-a), sin(a), cos(a)); }

vec3 render(vec2 I)
{
    vec2 u =(I-.5*R)/R.y*r(T*.3);
    vec4 O = vec4(0);
    for (float i = 0.; i < 1.; i += 1./50.) {
        float n = cnoise(vec3(u * 2.5  + i * .3, .9 * T + i * 1.2));
        float l = c(u + n * .14);
        vec3 c = mix(vec3(t(.4), t(.8), t(3.)), vec3(t(.8), t(1.2), t(.5)), i);
        O += vec4(l * c * .3, i);
    }
    return O.rgb;
}

void mainImage( out vec4 O, in vec2 I )
{
    // Linear RGB
    vec3 col = pow(render(I), vec3(2.2));

    // Saturation
    col = mix(vec3(dot(col, vec3(1. / 3.))), col, 1.2);

    // flim
    col = flim_transform(col, -.5, iChannel0);

    // Output
    O = vec4(col, 1);
}

