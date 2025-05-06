/*
[C]by @XorDev
https://www.shadertoy.com/view/W3BSzy
[/C]
    "Heavenly" by @XorDev
*/
void mainImage(out vec4 O, vec2 I)
{
    float t = iTime,i,z,d;
    for(O *= i;i++<1e2;
        O += (cos(z+t+vec4(6,1,2,3))+1.)/d)
    {
        vec3 p=z*normalize(vec3(I+I,0)-iResolution.xyy);
        p.z-=t;
        for(d=1.;d<9.;d/=.7)
            p+=cos(p.yzx*d+z*.2)/d;
        z+=d=.02+.1*abs(3.-length(p.xy));
    }
    O = tanh(O/3e3);
}
