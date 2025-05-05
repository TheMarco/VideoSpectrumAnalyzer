/*
    "Shield" by @XorDev
    
    Inspired by @cmzw's work: witter.com/cmzw_/status/1729148918225916406
    
    X: X.com/XorDev/status/1730436700000649470
    Twigl: twigl.app/?ol=true&ss=-NkYXGfK5wEl4VaUQ9zS
*/
void mainImage( out vec4 O,vec2 I)
{
    //Iterator, z and time
    float i,z,t=iTime;
    //Clear frag and loop 100 times
    for(O*=i; i<1.; i+=.01)
    {
        //Resolution for scaling
        vec2 v=iResolution.xy,
        //Center and scale outward
        p=(I+I-v)/v.y*i;
        //Sphere distortion and compute z
        p/=.2+sqrt(z=max(1.-dot(p,p),0.))*.3;
        //Offset for hex pattern
        p.y+=fract(ceil(p.x=p.x/.9+t)*.5)+t*.2;
        //Mirror quadrants
        v=abs(fract(p)-.5);
        //Add color and fade outward
        O+=vec4(2,3,5,1)/2e3*z/
        //Compute hex distance
        (abs(max(v.x*1.5+v,v+v).y-1.)+.1-i*.09);
    }
    //Tanh tonemap
    O=tanh(O*O);
}
