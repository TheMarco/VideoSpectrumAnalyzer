/*
[C]
by diatribes
https://www.shadertoy.com/view/w32XDc
[/C]
*/

#define P(z) vec3(cos(vec2(.15,.2)*(z))*5.,z)          
void mainImage(out vec4 o, vec2 u) {
    float i,d,s,n,t=iTime*3.;
    vec3  q = iResolution,
          p = P(t),
          Z = normalize( P(t+1.)- p),
          X = normalize(vec3(Z.z,0,-Z)),
          D = vec3((u-q.xy/2.)/q.y, 1)  * mat3(-X, cross(X, Z), Z);
    for(o*=i; i++<1e2;) {
        p += D * s;
        q = P(p.z)+cos(t+p.yzx)*.3;
        s  = 2.  - min(length((p-q).xy),
                   min(length(p.xy - q.y) ,
                       length(p.xy - q.x)));
        for (n = .1; n < 1.;
            s -= abs(dot(sin(p * n * 16.), q-q+.03)) / n,
            n += n);
        d += s = .04 + abs(s)*.2;
        o += (1.+cos(d+vec4(4,2,1,0))) / s / d;
    }
    o = tanh(o / 2e2);
}
