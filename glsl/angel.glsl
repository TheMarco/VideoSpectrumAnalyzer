/*
    "Angel" by @XorDev
    
    An experiment based on my "3D Fire":
    https://www.shadertoy.com/view/3XXSWS
*/
void mainImage(out vec4 O, vec2 I)
{
    //Time for animation
    float t = iTime,
    //Raymarch iterator
    i,
    //Raymarch depth
    z,
    //Raymarch step size
    d;
    //Raymarch loop (100 iterations)
    for(O *= i; i++<1e2;
        //Sample coloring and glow attenuation
        O+=(sin(z+vec4(2,3,4,0))+1.1)/d)
    {
        //Raymarch sample position
        vec3 p = z * normalize(vec3(I+I,0) - iResolution.xyy);
        //Shift camera back
        p.z += 6.;
        //Twist shape
        p.xz *= mat2(cos(p.y*.5+vec4(0,33,11,0)));
        //Distortion (turbulence) loop
        for(d=1.; d<9.; d/=.8)
            //Add distortion waves
            p += cos((p.yzx-t*vec3(3,1,0))*d)/d;
        //Compute distorted distance field of cylinder
        z += d = (.1+abs(length(p.xz)-.5))/2e1;
    }
    //Tanh tonemapping
    //https://www.shadertoy.com/view/ms3BD7
    O = tanh(O/4e3);
}
