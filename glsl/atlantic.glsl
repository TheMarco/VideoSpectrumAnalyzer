/*
[C]
by @XorDev
https://www.shadertoy.com/view/3ct3WS
*/
// mod of @XorDev Atlantic - https://x.com/XorDev/status/1922716290545783182
mat3 rotate3D(const in float r, in vec3 a) {
    a = normalize(a);
    float s = sin(r);
    float c = cos(r);
    float oc = 1.0 - c;
    vec3 col1 = vec3(oc * a.x * a.x + c, oc * a.x * a.y + a.z * s, oc * a.z * a.x - a.y * s);
    vec3 col2 = vec3(oc * a.x * a.y - a.z * s, oc * a.y * a.y + c, oc * a.y * a.z + a.x * s);
    vec3 col3 = vec3(oc * a.z * a.x + a.y * s, oc * a.y * a.z - a.x * s, oc * a.z * a.z + c);
    return mat3(col1, col2, col3);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 FC = fragCoord;
    vec2 r = iResolution.xy;
    float t = iTime;
    vec4 o = vec4(0.0, 0.0, 0.0, 1.0);

    float i = 0., d = 0., z = 3.;
    for(; i++ < 1e2; o += 1.2 / d / z) { // Outer loop, runs 100 times, accumulating color
        vec3 p = z * (vec3(FC, 1.0) * 2. - r.xyy) / r.y; // Direction vector
        for(d = 1.; d < 3e1; d /= .7) // Wave distortion
            p += .3 * sin(p * rotate3D(d, r.xyy) * d + t) / d;
        z += d = .01 + .4 * max(d = p.y + p.z * .5 + 2., -d * .1);
    }
    o = tanh((o / vec4(9, 6, 3, 1)) / 2e2);

    fragColor = o;
}

