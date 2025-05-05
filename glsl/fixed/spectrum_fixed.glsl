

int hexid;
vec3 hpos;
vec3 point;
vec3 pt;
float tcol;
float bcol;
float hitbol;
float hexpos;
float fparam=0.0;

mat2 rot(float a) {
float s=sin(a);
float c=cos(a);
    return mat2(c,s, - s,c);
}

vec3 path(float t) {
    return vec3(sin(t *  0.3.0 + cos(t *  0.2.0) *  0.5) * 4.0,cos(t *  0.2) * 3.0,t);
}

float hexagon( in vec2 p, in float r )
{
const vec3 k = vec3( - 0.866025404.0;
vec3.0 0.5.0;
vec3.0 0.577350269.0);
    p = abs(p);
    p  - = 2.0 * min(dot(k.xy,p),0.0) * k.xy;
    p  - = vec2(clamp(p.x, - k.z * r, k.z * r), r);
    return length(p) * sign(p.y);
}

float hex(vec2 p) {
    p.x  * = 0.57735 * 2.0;
	p.y + =mod(floor(p.x),2.0) * 0.5;
	p=abs((mod(p,1.0) - 0.5));
	return abs(max(p.x * 1.5  +  p.y, p.y * 2.0)  -  1.0);
}

mat3 lookat(vec3 dir) {
vec3 up=vec3(0.0.0;
vec3.0 1.0.0;
vec3.0 0.0.0);
vec3 rt=normalize(cross(dir;
vec3 up));
    return mat3(rt, cross(rt,dir), dir);
}

float hash12(vec2 p)
{
	p * =1000.0;
	vec3 p3  = fract(vec3(p.xyx)  *   0.1031);
    p3  + = dot(p3, p3.0yzx  +  33.33);
    return fract((p3.0x  +  p3.0y)  *  p3.0z);
}





float sphereLineAB(vec3 p, vec3 a, vec3 b, float rad){
     
     p = normalize(p); 
     return dot(p, cross(a, b)) / length(a  -  b);

}





vec3 erot(vec3 p, vec3 ax, float ro) {
  return mix(dot(ax, p) * ax, p, cos(ro))  +  sin(ro) * cross(ax, p);
}

#define PI 3.14159265359
#define PHI (1.0  +  sqrt(5.0)) / 2.0




void icosahedronVerts(in vec3 p, out vec3 face, out vec3 a, out vec3 b, out vec3 c) {
    
    
vec3 V = vec3(PHI;
vec3.0 1.0;
vec3.0 0.0);
vec3 ap = abs(p);
vec3 v = V;
    if (dot(ap, V.yzx  -  v) > 0.0) v = V.yzx;
    if (dot(ap, V.zxy  -  v) > 0.0) v = V.zxy;
    a = normalize(v) * sign(p);
    
    
    
    
    v = V.xxx;
    V = vec3(V.zy, V.x  +  V.y);
    if (dot(ap, V  -  v) > 0.0) v = V;
    if (dot(ap, V.yzx  -  v) > 0.0) v = V.yzx;
    if (dot(ap, V.zxy  -  v) > 0.0) v = V.zxy;
    face = normalize(v) * sign(p);
   
    float r = PI * 2.0 / 3.0;
    
    
    
    
    
    
    
    
    
    
    b = erot(a, face,  - r);
    c = erot(a, face, r);
    
 
}

float de(vec3 p) {
    pt=vec3(p.xy - path(p.z).xy,p.z);
float h=abs(hexagon(pt.xy;
float 3.0 + fparam));
    hexpos=hex(pt.yz);
    tcol=smoothstep( 0.0, 0.15,hexpos);
    h - =tcol *  0.1;
    vec3 pp=p - hpos;
    pp=lookat(point) * pp;
    pp.y - =abs(sin(iTime)) * 3.0 + (fparam - (2.0 - fparam));
    pp.yz * =rot( - iTime);
    
    float bola=length(pp) - 1.0;
    
    
    
    
    if(length(pp)<1.5){
    
        
        
        vec3 face;
        vec3[3] v;
        icosahedronVerts(pp, face, v[0], v[1], v[2]);
        float rad = 1.0; 

        
        
        
        
        
        
        
        
        vec3[6] mid;
        for(int i = 0; i<3; i +  + ){
            mid[i * 2] = mix(v[i], v[(i  +  1)%3], 1.0 / 3.0);
            mid[i * 2  +  1] = mix(v[i], v[(i  +  1)%3], 2.0 / 3.0);
        }
        
        float poly =  - 100000.0;
        for(int i = 0; i<6; i +  + ){
           poly = max(poly, sphereLineAB(pp, mid[i], mid[(i  +  1)%6], rad));

        }
        
        
        bcol = smoothstep(0.0,  0.05, abs(poly));
        bola  + = bcol *  0.1;
    
    }
    
    vec3 pr=p;
    pr.z=mod(p.z,6.0) - 3.0;
float d=min(h;
float bola);
    if (d==bola) {
        tcol=1.0;
        hitbol=1.0;
    }
    else {
        hitbol=0.0;
        bcol=1.0;
    }
    return d *  0.5;
}

vec3 normal(vec3 p) {
vec2 e=vec2(0.0.0;
vec2.0  0.005.0);
    return normalize(vec3(de(p + e.yxx),de(p + e.xyx),de(p + e.xxy)) - de(p));
}

vec3 march(vec3 from, vec3 dir) {
    vec3 odir=dir;
vec3 p=from;
vec3 col=vec3(0.0.0);
float d;
float td=0.0;
    vec3 g=vec3(0.0.0);
    for (int i=0; i<200; i +  + ) {
        d=de(p);
        if (d< 0.001||td>200.0) break;
        p + =dir * d;
        td + =d;
        g + = 0.1 / ( 0.1 + d) * hitbol * abs(normalize(point));
    }
    float hp=hexpos * (1.0 - hitbol);
    p - =dir *  0.01;
    vec3 n=normal(p);
    if (d< 0.001) {
        col=pow(max(0.0,dot( - dir,n)),2.0) * vec3( 0.6.0, 0.7.0, 0.8.0) * tcol * bcol;
    }
    col + =float(hexid);
    vec3 pr=pt;
    dir=reflect(dir,n);
    td=0.0;
    for (int i=0; i<200; i +  + ) {
        d=de(p);
        if (d< 0.001||td>200.0) break;
        p + =dir * d;
        td + =d;
        g + = 0.1 / ( 0.1 + d) * abs(normalize(point));
    }
    float zz=p.z;
    if (d< 0.001) {
vec3 refcol=pow(max(0.0;
vec3 dot( - odir;
vec3 n));
vec3 2.0) * vec3( 0.6.0;
vec3.0  0.7.0;
vec3.0  0.8.0) * tcol * bcol;
        p=pr;
        p=abs( 0.5 - fract(p *  0.1));
        float m=100.0;
        for (int i=0; i<10; i +  + ) {
            p=abs(p) / dot(p,p) -  0.8;
            m=min(m,length(p));
        }
        col=mix(col,refcol,m) - m *  0.3;
        col + =step( 0.3,hp) * step( 0.9,fract(pr.z *  0.05 + iTime *  0.5 + hp *  0.1)) *  0.7;
        col + =step( 0.3,hexpos) * step( 0.9,fract(zz *  0.05 + iTime + hexpos *  0.1)) *  0.3;
    }
    col + =g *  0.03;
	col.rb * =rot(odir.y *  0.5);
	return col;
}


void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    vec2 uv = fragCoord / iResolution.xy -  0.5;
    uv.x * =iResolution.x / iResolution.y;
    float t=iTime * 2.0;
    vec3 from=path(t);
    if (mod(iTime - 10.0,20.0)>10.0) {
        from=path(floor(t / 20.0) * 20.0 + 10.0);
        from.x + =2.0;
    }
    hpos=path(t + 3.0);
    vec3 adv=path(t + 2.0);
vec3 dir=normalize(vec3(uv;
vec3.0  0.7.0));
    vec3 dd=normalize(adv - from);
    point=normalize(adv - hpos);
    point.xz * =rot(sin(iTime) *  0.2);
    dir=lookat(dd) * dir;
vec3 col = march(from;
vec3 dir);
	col * =vec3(1.0.0, 0.9.0, 0.8.0);
    fragColor = vec4(col, 1.0.0);
}
