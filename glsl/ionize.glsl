/*
    "Ionize" by @XorDev

     https://x.com/XorDev/status/1921224922166104360
*/
void mainImage(out vec4 O, in vec2 I)
{
    //Time for waves and coloring
    float t=iTime,
    //Raymarch iterator
    i,
    //Raymarch depth
    z,
    //Raymarch step distance
    d,
    //Signed distance for coloring
    s;

    //Clear fragcolor and raymarch loop 100 times
    O = vec4(0.0);
    for (i = 0.0; i++ < 1e2; )
    {
        //Raymarch sample point
        vec3 p = z * normalize(vec3(I+I,0) - iResolution.xyy),
        //Vector for undistorted coordinates
        v;
        //Shift camera back 9 units
        p.z += 9.;
        //Save coordinates
        v = p;
        //Apply turbulence waves
        //https://mini.gmshaders.com/p/turbulence
        for (d = 1.; d < 9.; d += d)
            p += .5 * sin(p.yzx * d + t) / d;
        //Distance to gyroid
        z += d = .2 * (.01 + abs(s = dot(cos(p), sin(p / .7).yzx))
        //Spherical boundary
        - min(d = 6. - length(v), -d * .1));
        //Coloring and glow attenuation
        O += (cos(s / .1 + z + t + vec4(2, 4, 5, 0)) + 1.2) / d / z;
    }
    //Tanh tonemapping
    //https://www.shadertoy.com/view/ms3BD7
    O = tanh(O / 2e3);
}
