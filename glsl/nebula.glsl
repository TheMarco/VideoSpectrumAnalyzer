/*
    "Nebula 3" by @XorDev
    
    Based on my tweet shader:
    https://x.com/XorDev/status/1918766627828515190
*/
void mainImage(out vec4 O, vec2 I)
{
    float t = iTime, i, z, d, s;
    for(O *= i; i++<1e2;
        O+=(cos(s+s-vec4(5,0,1,3))+1.4)/d/z)
    {
        vec3 p = z * normalize(vec3(I+I,0) - iResolution.xyy);
        p.z -= t;
        for(d = 1.; d < 64.; d += d)
            p += .7 * cos(p.yzx*d) / d;
        p.xy *= mat2(cos(z*.2 + vec4(0,11,33,0)));
        z += d = .03+.1*max(s=3.-abs(p.x), -s*.2);
    }
    O = tanh(O*O/4e5);
}
