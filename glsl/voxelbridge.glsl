/*
[C]
by SHAU
https://www.shadertoy.com/view/MddfRl
[/C]
*/

// Created by SHAU - 2018
// License Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License.
//-----------------------------------------------------

#define PI 3.141592
#define T iTime
#define FAR 50.0

//Dave Hoskins
float hash13(vec3 p3) {
	p3 = fract(p3 * .1031);
    p3 += dot(p3, p3.yzx + 19.19);
    return fract((p3.x + p3.y) * p3.z);
}

//Shane
vec3 path(float t) {
    float a = sin(t * PI / 24.0 + 1.7);
    float b = cos(t * PI / 24.0);
    return vec3(a * 2.0, b * a, t);    
}   

//wireframe edges
float tex(vec3 rp) {
    float bs = 0.95;
    if (abs(rp.x) < bs && abs(rp.y) < bs) return 0.0;
    return 1.0;   
}        

// Cube mapping routine from Fizzer
float fizz(vec3 rp) {
    vec3 f = abs(rp);
    f = step(f.zxy, f) * step(f.yzx, f); 
    f.xy = f.x > .5 ? rp.yz / rp.x : f.y > .5 ? rp.xz / rp.y : rp.xy / rp.z; 
    return tex(f);
}

mat2 rot(float x) {return mat2(cos(x), sin(x), -sin(x), cos(x));}

//sphere and box functions from IQ
//https://iquilezles.org/www/index.htm
vec2 boxIntersection(vec3 ro, vec3 rd, vec3 b, inout vec3 on, float r1, float r2) {
    
    float la = 0.0;
    
    ro.zy *= rot(r1);
    rd.zy *= rot(r1);
    ro.xz *= rot(r2);
    rd.xz *= rot(r2);

    vec3 m = 1.0 / rd;
    vec3 n = m * ro;
    vec3 k = abs(m) * b;
    vec3 t1 = -n - k;
    vec3 t2 = -n + k;
    float tN = max(max(t1.x, t1.y), t1.z);
    float tF = min(min(t2.x, t2.y), t2.z);
    on = -sign(rd) * step(t1.yzx, t1.xyz) * step(t1.zxy, t1.xyz);
    
    la = fizz(ro + rd * tN);
    
    on.zy *= rot(-r1); 
    on.zy *= rot(-r1); 
    on.xz *= rot(-r2); 
    on.xz *= rot(-r2); 
    
    return (tN > tF || tF < 0.0) ? vec2(0.0) : vec2(tN, la);
}

vec2 sphIntersect(vec3 ro, vec3 rd, vec4 sph) {
    vec3 oc = ro - sph.xyz;
    float b = dot(oc, rd);
    float c = dot(oc, oc) - sph.w * sph.w;
    float h = b * b - c;
    if (h < 0.0) return vec2(0.0);
    h = sqrt(h);
    float tN = -b - h;
    float tF = -b + h;
    return vec2(tN, tF);
}

float sphDensity(vec3 ro, vec3 rd, vec4 sph, float dbuffer) {

    float ndbuffer = dbuffer / sph.w;
    vec3  rc = (ro - sph.xyz) / sph.w;

    float b = dot(rd, rc);
    float c = dot(rc, rc) - 1.0;
    float h = b * b - c;
    if (h < 0.0) return 0.0;
    h = sqrt(h);
    float t1 = -b - h;
    float t2 = -b + h;

    if (t2 < 0.0 || t1 > ndbuffer) return 0.0;
    t1 = max(t1, 0.0);
    t2 = min(t2, ndbuffer);

    float i1 = -(c * t1 + b * t1 * t1 + t1 * t1 * t1 / 3.0);
    float i2 = -(c * t2 + b * t2 * t2 + t2 * t2 * t2 / 3.0);
    return (i2 - i1) * (3.0 / 4.0);
}

//modified logic from IQ
//https://www.shadertoy.com/view/4dfGzs
struct Scene {
    float t;
    vec3 n;
    float l;
};
Scene voxelMarch(vec3 ro, vec3 rd) {
 
    float t = 0.0;
    vec3 n = vec3(0.0), mm = n, p = floor(ro), ri = 1.0 / rd, rs = sign(rd);
    float l = 0.0;
    
    vec3 d = (p - ro + 0.5 + rs * 0.5) * ri;

    for (int i = 0; i < 128; i++) {
        
        if (length(p.xy - path(p.z).xy) > 3.0) {
        
            float r = hash13(p);
        	float r1 = r + T + p.z;
        	float r2 = r1 * 2.0 + p.y;

            vec2 bi = boxIntersection(ro - (p + vec3(0.5)), 
                                       rd, 
                                       vec3(clamp(r * 0.5, 0.1, 0.3)), 
                                       n,
                                       r1,
                                       r2);
            
            if (bi.x > 0.0) {
                t = bi.x;
                l = bi.y;
                break;
            }
        }
        
        mm = step(d.xyz, d.yxy) * step(d.xyz, d.zzx);
        d += mm * rs * ri;
        p += mm * rs;
    }
    
    return Scene(t, n, l);
}

void setupCamera(vec2 fragCoord, inout vec3 ro, inout vec3 rd, inout vec3 lp) {

    vec2 uv = (fragCoord.xy - iResolution.xy * 0.5) / iResolution.y;

    vec3 lookAt = vec3(0.0, 0.0, T * 6.0);
    ro = lookAt + vec3(0.0, 0.0, -1.0);
    lp = lookAt + vec3(0.0, 0.0, 16.0 + sin(T * 0.2) * 6.0);

    lookAt = path(lookAt.z);
    ro = path(ro.z);
	lp = path(lp.z);
      
    float FOV = PI / 3.0;
    vec3 forward = normalize(lookAt - ro);
    vec3 right = normalize(vec3(forward.z, 0.0, -forward.x)); 
    vec3 up = cross(forward, right);

    rd = normalize(forward + FOV * uv.x * right + FOV * uv.y * up);
    rd.xy *= rot(sin(-ro.x  * 0.5) * 0.4);//isdive
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    
    float mint = FAR;
    vec3 pc = vec3(0.0), ro, rd, lp;
    setupCamera(fragCoord, ro, rd, lp);
    
    Scene scene = voxelMarch(ro, rd);
    
    if (scene.t > 0.0) {
        
        mint = scene.t;
        vec3 rp = ro + rd * scene.t;
        
        //camera light
        vec3 ld = normalize(vec3(4.0, 5.0, -4.0));
        float atten = 1.0 / (1.0 + scene.t * scene.t * 0.05);
        float spec = pow(max(dot(reflect(-ld, scene.n), -rd), 0.0), 64.0);
        vec3 ac = vec3(1.0) * max(dot(ld, scene.n), 0.05) * 0.2;
        ac += vec3(0.1, 0.0, 0.9) * max(0.0, scene.n.y) * 0.1;
        ac += vec3(1.0) * spec * atten;
        
        //glowball light
        ld = normalize(lp - rp);
        float lt = length(lp - rp);
        atten = 1.0 / (1.0 + lt * lt * 0.03);
        spec = pow(max(dot(reflect(-ld, scene.n), -rd), 0.0), 64.0);
        //shadow
        Scene shadowScene = voxelMarch(rp - rd * 0.01, ld);
        float sh = shadowScene.t > 0.0 && shadowScene.t < lt ? 0.0 : 1.0;
        vec3 gc = vec3(1.0, 0.5, 0.0) * max(dot(ld, scene.n), 0.05) * atten * sh;
        atten = 1.0 / (1.0 + lt * lt * 0.08);
        gc += vec3(1.0, 0.8, 0.0) * max(dot(ld, scene.n), 0.05) * atten * sh;
        gc += vec3(1.0, 1.0, 0.3) * spec * atten * sh;
        
        pc = ac + gc;
        
        float la = mod(rp.z + T * 8.0, 30.0);
        pc += vec3(1.0, 0.5, 0.0) * scene.l * step(la, 5.0) / (1.0 + mint * 0.001);
    }
    
    pc = mix(pc, vec3(0.4, 0.2, 0.0), mint / FAR);
    
    vec2 si = sphIntersect(ro, rd, vec4(lp, 1.0));
    if (si.x > 0.0 && si.x < mint) {
        float w = sphDensity(ro, rd, vec4(lp, 1.0), FAR);
        if (w > 0.0) {
        	pc += vec3(1.0, 0.2, 0.0) * w * w;    
        	pc += vec3(1.0, 0.5, 0.0) * w * w * w;    
        	pc += vec3(1.0, 1.0, 0.0) * w * w * w * w * w;    
        }
    }
    
    fragColor = vec4(pc, 1.0);
}
