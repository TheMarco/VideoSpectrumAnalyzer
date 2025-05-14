/*
[C]
by diatribes
https://www.shadertoy.com/view/wfdGWM
[/C]
*/

void mainImage(out vec4 o, vec2 u) {
    float i,d,s,t=iTime;
    vec3  p = iResolution;    
    u = (u-p.xy/2.)/p.y;
    for(o*=i; i++<1e2; ) {
        p = vec3(u* d,d+t);
        for (s = .15; s < 1.;
            p += cos(t+p.yzx*.6)*sin(p.z*.1)*.2,
            p.y += sin(t+p.x)*.03,
            p += abs(dot(sin(p * s * 24.), p-p+.01)) / s,
            s *= 1.5);
        d += s = .03 + abs(2.+p.y)*.3;
        o += vec4(1,2,4,0) / s;
    }
    o = tanh(o / 7e3 / dot(u-=.35,u));
}
