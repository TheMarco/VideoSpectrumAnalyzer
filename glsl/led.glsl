/*
    "LED" by @XorDev
    
    A little shader inspired by LED cubes.
    
    Original: https://www.shadertoy.com/view/msB3Wm
    Tweet: twitter.com/XorDev/status/1588987185763880961
    Twigl: t.co/wJxCI4wLwa
    
    <300 chars playlist: shadertoy.com/playlist/fXlGDN
*/

void mainImage(out vec4 O, vec2 I)
{
    // Clear fragColor
    O = vec4(0.0, 0.0, 0.0, 0.0);
    
    // Initialize LED position and rotated position vectors
    vec3 p, q;
    // Save resolution for scaling/centering
    vec3 r = iResolution;
    // Time (yz are approximate ratios of pi/2)
    vec3 t = iTime+vec3(0.0, 11.0, 33.0);
    
    // Loop through 64 LEDs, adding LED color
    for(int i=0; i<64; i++)
    {
        // Compute LED 3D position from i
        p = vec3(i&3, i/4&3, i/16) - 1.5;
        // Rotate about y-axis
        q = p;
        q.zx *= mat2(cos(t.x), -sin(t.x), sin(t.x), cos(t.x));
        
        // Add LED color contribution
        O.rgb += (sin(p.x+t*vec3(3.0, 4.0, 5.0))+1.0) *
            // Brightness with flickering from 2D texture (fixed from 3D)
            texture(iChannel0, vec2((p+t).x, (p+t).y)*0.2).r/500.0 * (2.3-q.z) /
            // Diminish with linear distance (and project 3D LED to 2D)
            length((I+I-r.xy)/r.y+q.xy/(4.0+q.z));
    }
    
    // Set alpha to 1.0
    O.a = 1.0;
}
