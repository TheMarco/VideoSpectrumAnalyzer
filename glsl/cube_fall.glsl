/*
[C]
by SHAU
https://www.shadertoy.com/view/ttSyR3
[/C]
*/

// Created by SHAU - 2020
// License Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License.
//-----------------------------------------------------

/**
 * Loosley inspired by GIF animation on Pouet
 * and Sparse grid marching by Nimitz
 **/

#define R iResolution.xy
#define ZERO (min(iFrame,0))
#define EPS .005
#define FAR 140.
#define T iTime
#define TORUS vec2(40.0,18.0)

//Fabrice - compact rotation
mat2 rot(float x) {return mat2(cos(x), sin(x), -sin(x), cos(x));}

//Nimitz
//https://www.shadertoy.com/view/XlfGDs
const float c = 1.0;
const float ch = c * 0.5;
const float ch2 = ch + 0.01;
float dBox(vec3 ro, vec3 rd)  
{
    vec3 m = 1. / rd;
    vec3 t = -m * ro + abs(m) * ch2;
	return min(min(t.x, t.y), t.z);
}

//Shane - Perspex Web Lattice - one of my favourite shaders
//https://www.shadertoy.com/view/Mld3Rn
//Standard hue rotation formula... compacted down a bit.
vec3 rotHue(vec3 p, float a)
{
    vec2 cs = sin(vec2(1.570796,0) + a);

    mat3 hr = mat3(0.299,  0.587,  0.114,  0.299,  0.587,  0.114,  0.299,  0.587,  0.114) +
        	  mat3(0.701, -0.587, -0.114, -0.299,  0.413, -0.114, -0.300, -0.588,  0.886) * cs.x +
        	  mat3(0.168,  0.330, -0.497, -0.328,  0.035,  0.292,  1.250, -1.050, -0.203) * cs.y;
							 
    return clamp(p*hr,0.,1.);
}

//Dave Hoskins - Hash without sin
vec2 hash23(vec3 p3)
{
	p3 = fract(p3 * vec3(.1031, .1030, .0973));
    p3 += dot(p3, p3.yzx+33.33);
    return fract((p3.xx+p3.yz)*p3.zy);
}

//SDF functions IQ
float sdTorus(vec3 p, vec2 t) 
{
    vec2 q = vec2(length(p.yz) - t.x, p.x);
    return length(q) - t.y;
}

float sdBox(vec3 p, vec3 b) 
{
    vec3 d = abs(p) - b;
    return min(max(d.x, max(d.y, d.z)), 0.0) + length(max(d, 0.0));
}

float boxedTorus(vec3 p, vec3 rd)
{
    float AT = T*0.4;
    vec3 q = p;
    q.yz *= rot(AT);
    rd.yz *= rot(AT);
    vec3 qd = fract(q/c)*c -ch;
    vec3 qid = floor(q/c) + 0.5;
    vec2 h2 = hash23(qid);
    float t = dBox(qd, rd); //Base distance is cell exit distance
    if (sdTorus(floor(q/c)+.5,TORUS) < 0. && p.y < 0.)
    {
        qd.yz *= rot(h2.y + h2.x*T);
        qd.zx *= rot(h2.x + h2.y*T);
        t = min(t, sdBox(qd, vec3(0.3)));    
    }
    return t;
}

float boxedWall(vec3 p, vec3 rd)
{
    float AT = T*0.4;
    p.y += AT * 25.;
    vec3 qd = fract(p/c)*c -ch;
    vec3 qid = floor(p/c);
    vec2 h2 = hash23(qid);
    float t = dBox(qd, rd); //Base distance is cell exit distance
    if (p.z > (TORUS.x - TORUS.y))
    {
        qd.yz *= rot(h2.y + h2.x*T);
        qd.zx *= rot(h2.x + h2.y*T);
        t = min(t, sdBox(qd, vec3(0.3)));    
    }
    return t;
}

float map(vec3 p, vec3 rd) 
{    
    return min(boxedTorus(p, rd), boxedWall(p, rd));
}

vec3 normal(vec3 p, vec3 rd) 
{  
    vec4 n = vec4(0.0);
    for (int i=ZERO; i<4; i++) 
    {
        vec4 s = vec4(p, 0.0);
        s[i] += EPS;
        n[i] = map(s.xyz, rd);
    }
    return normalize(n.xyz-n.w);
}

vec4 render(vec3 ro, vec3 rd)
{
    vec3 pc = vec3(0),
         lp = vec3(-10,8,-8),
        sc = rotHue(vec3(1,0.5,0.1), T*0.3);

    float t = 0.0, mint = FAR;   
    for (int i=0; i<360; i++)
    {
        float ns = map(ro + rd*t, rd);
        if (ns<EPS)
        {
            break;
        }
        t += ns;
        if (t>FAR) 
        {
            t = -1.0;
            break;
        }
    }
    
    if (t>0.0)
    {
        mint = t;
        vec3 p = ro + rd*t;
        vec3 n = normal(p,rd);
        vec3 ld = normalize(lp - p);
        float lt = length(lp - p); 
        float spec = pow(max(dot(reflect(-ld, n), -rd), 0.0), 32.0);
        
        pc += sc*0.4*max(0.05,dot(ld,n)) / (1. + lt*lt*0.02);
        pc += sc*spec*2.;
        pc += vec3(0.6,0.1,0.8)*0.01*max(0.,n.y);
    }

    pc *= exp(-0.06 * mint); 
    pc = pow(pc,vec3(.43545));
    
    return vec4(pc,mint);
}

//IQ
mat3 camera(vec3 la, vec3 ro, float cr)
{
	vec3 cw = normalize(la - ro),
	     cp = vec3(sin(cr),cos(cr),0.0),
	     cu = normalize(cross(cw,cp)),
	     cv =          (cross(cu,cw));
    return mat3(cu,cv,cw); 
}

void mainImage(out vec4 C, vec2 U)
{
    float AT = T - 4.1;
    vec3 pc = vec3(0),
         la = vec3(0,-10,TORUS.x),
         ro = vec3(sin(AT*0.2)*20.,
                   -20.0,
                   -5. + cos(AT*0.31)*3.);
    ro.y -= ro.x*ro.x*0.02*sin(AT*0.3);
    
    float fl = 1.4;
    mat3 cam = camera(la,ro,0.);  

    vec2 uv = (2.0*(U) - R.xy)/R.y;
    vec3 rd = cam*normalize(vec3(uv,fl));        
    vec4 scene = render(ro,rd);
    pc = scene.xyz;

    pc = 1.15*pow(pc,vec3(0.9,0.95,1.0)) + vec3(-0.04,-0.04,0.0); //IQ
    pc = pow(pc,vec3(0.80,0.85,0.9));
    pc *= 1. / (1. + length(uv)*length(uv)*0.2);

    C = vec4(pc*2.4,1.0);
}
