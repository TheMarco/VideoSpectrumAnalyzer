/*
    "Ghosts" by @XorDev
    
    More fun with Turbulence in 3D. Also see
    
    3D Fire:
    https://www.shadertoy.com/view/3XXSWS
    Ether:
    https://www.shadertoy.com/view/t3XXWj
    Angel:
    https://www.shadertoy.com/view/3XXSDB

    
    Tweet version:
    https://x.com/XorDev/status/1915763936957264357
*/

void mainImage(out vec4 O, vec2 I)
{
    //Time for animation
    float t = iTime,
    //Raymarch iterator
    i,
    //Raymarch depth
    z,
    //Raymarch step size and "Turbulence" frequency
    d;
    //Clear frag color and raymarch loop
    for (O *= i; i++ < 1e2;
        //Add color and glow falloff
        O += vec4(z / 7., 2, 3, 1) / d)
    {
        //Raymarch sample point
        vec3 p = z * normalize(vec3(I+I,0) - iResolution.xyy);
        //Twist with depth
        p.xy *= mat2(cos((z + t) * .1 + vec4(0, 33, 11, 0)));
        //Scroll forward
        p.z -= 5. * t;
        
        //Turbulence loop
        //https://www.shadertoy.com/view/WclSWn
        for (d = 1.; d < 9.; d /= .7)
            p += cos(p.yzx * d + t) / d;
        
        //Distance to irregular gyroid
        //https://www.shadertoy.com/view/XcBBRz
        z += d = .02 + abs(2. - dot(cos(p), sin(p.yzx * .6))) / 8.;
    }
    //Tanh tonemapping
    //https://www.shadertoy.com/view/ms3BD7
    O = tanh(O * O / 1e7);
}
