/*
[C]
by diatribes
https://www.shadertoy.com/view/wfdGWM
[/C]
*/

void mainImage(out vec4 o, vec2 u) {
    float i = 0.0;
    float d = 0.0;
    float s = 0.0;
    float t = iTime;
    vec3 p = iResolution;    
    
    // Initialize output color to black
    o = vec4(0.0, 0.0, 0.0, 1.0);
    
    u = (u-p.xy/2.)/p.y;
    
    for(i = 0.0; i < 100.0; i++) {
        p = vec3(u * d, d+t);
        
        for (s = 0.15; s < 1.0; s *= 1.5) {
            p += cos(t+p.yzx*0.6)*sin(p.z*0.1)*0.2;
            p.y += sin(t+p.x)*0.03;
            p += abs(dot(sin(p * s * 24.0), p-p+0.01)) / s;
        }
        
        d += s = 0.03 + abs(2.0+p.y)*0.3;
        o += vec4(1.0, 2.0, 4.0, 0.0) / s;
    }
    
    // Apply final color transformation
    o = tanh(o / 7000.0 / dot(u-=0.35, u));
}
