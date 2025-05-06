// By @XorDev
//<300 chars playlist: https://www.shadertoy.com/playlist/fXlGDN

// Based on gaz's hypercube:
// https://www.shadertoy.com/view/NlcSDS

// Twigl: https://t.co/MCkEtXRfYM
// Tweet: https://twitter.com/XorDev/status/1493984559498768384

//FabriceNeyret2 saved 3 chars
//coyote save 9 chars


void mainImage(out vec4 O, vec2 C)
{
    O-=O; //Clear color
    vec3 R = iResolution, //Temporary resolution
         p = 4./R, //Camera position
         A = vec3(0,.6,.8), //Rotation axis
         q = R-R; //Rotated position

    for( float i=0.,s; i++<3e2; ) 
        q = int(i)% 3 > 1 ? //Step forward every 3 iterations
                s = length(--q.xz)*.5 - .04, //Step distance
                O += .9/exp(s*vec4(1,2,4,1))/i, //Color based on SDF
                abs( mix(A*dot(p -= normalize(vec3(C+C,R)-R) * s,A), //Step forward
                         p, cos(s=iTime))+sin(s)*cross(p,A) ) //Rotate cube
            :    
                q.x<q.y ? q.zxy : q.zyx; //gaz's clever axis sorting trick
        
    O *= O;
}
