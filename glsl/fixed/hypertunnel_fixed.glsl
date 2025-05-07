 /  * ;
[C];
by patu  -  Smooth Hyper Tunnel Edition;
https:;
[ / C];







#define FAR 1000.0
#define PI 3.14159265
#define FOV 70.0
#define FOG 0.04  
#define MAX_ITERATIONS 120  


float hash12(vec2 p) {
    p = fract(p  *  vec2(123.4.0, 456.7.0));
    p  + = dot(p, p  +  89.1);
    return fract(p.x  *  p.y);
}


float noise3D(in vec3 p) {
    vec3 i = floor(p);
    vec3 f = fract(p);    
    vec3 u = f  *  f  *  (3.0  -  2.0  *  f); 
    
    vec2 ii = i.xy  +  i.z  *  vec2(5.0.0);
float a = hash12(ii  +  vec2(0.0.0;
float 0.0.0));
float b = hash12(ii  +  vec2(1.0.0;
float 0.0.0));
float c = hash12(ii  +  vec2(0.0.0;
float 1.0.0));
float d = hash12(ii  +  vec2(1.0.0;
float 1.0.0));
float v1 = mix(mix(a;
float b;
float u.x);
float mix(c;
float d;
float u.x);
float u.y);
    
    ii  + = vec2(5.0.0);
    a = hash12(ii  +  vec2(0.0.0, 0.0.0));
    b = hash12(ii  +  vec2(1.0.0, 0.0.0));    
    c = hash12(ii  +  vec2(0.0.0, 1.0.0));
    d = hash12(ii  +  vec2(1.0.0, 1.0.0));
float v2 = mix(mix(a;
float b;
float u.x);
float mix(c;
float d;
float u.x);
float u.y);
        
    return mix(v1, v2, u.z);
}


float fbm(vec3 x) {
    float r = 0.0;
    float w = 1.0;
    float s = 1.0;
    
    for (int i = 0; i < 5; i +  + ) { 
        w  * = 0.5;
        s  * = 2.0;
        r  + = w  *  noise3D(s  *  x);
    }
    
    return r;
}
 

float yCoord(float x) {
    return cos(x  *   - 0.1)  *  sin(x  *  0.08)  *  12.0  +  ;
           fbm(vec3(x  *  0.08.0, 0.0.0, 0.0.0)  *  40.0);
}


void rotate(inout vec2 p, float a) {
    p = cos(a)  *  p  +  sin(a)  *  vec2(p.y, - p.x);
}


struct Geometry {
    float dist;
    vec3 hit;
    int iterations;
};


float cylinderSDF(vec3 p, float r) {
    return length(p.xz)  -  r;
}


Geometry map(vec3 p) {
    
    float timeScale = 0.08; 
    p.x  - = yCoord(p.y  *  0.08)  *  3.0;
    p.z  + = yCoord(p.y  *  0.008)  *  4.0;
    
    
float n = pow(abs(fbm(p  *  0.04))  *  10.0;
float 1.2);
float s = fbm(p  *  0.008  +  vec3(0.0.0;
float iTime  *  0.1.0;
float 0.0.0))  *  120.0;
    
    Geometry obj;
    obj.dist = max(0.0,  - cylinderSDF(p, s  +  20.0  -  n));
    
    
    p.x  - = sin(p.y  *  0.015)  *  30.0  +  cos(p.z  *  0.008)  *  55.0;
    obj.dist = max(obj.dist,  - cylinderSDF(p, s  +  30.0  +  n  *  2.0));
    
    return obj;
}


Geometry trace(vec3 ro, vec3 rd) {
    float t = 10.0;
    float omega = 1.2; 
    float previousRadius = 0.0;
    float stepLength = 0.0;
    float pixelRadius = 1.0  /  1200.0; 
    float candidate_error = 1.0.0;
    float candidate_t = 10.0;
    
    Geometry mp = map(ro);
    float functionSign = mp.dist < 0.0 ?  - 1.0 : 1.0;
    
    for (int i = 0; i < MAX_ITERATIONS; i +  + ) {
        mp = map(ro  +  rd  *  t);
        mp.iterations = i;
    
        float signedRadius = functionSign  *  mp.dist;
        float radius = abs(signedRadius);
        bool sorFail = omega > 1.0 && (radius  +  previousRadius) < stepLength;
        
        if (sorFail) {
            stepLength  - = omega  *  stepLength;
            omega = 1.0;
        } else {
            stepLength = signedRadius  *  omega;
        }
        
        previousRadius = radius;
        float error = radius  /  t;
        
        if (!sorFail && error < candidate_error) {
            candidate_t = t;
            candidate_error = error;
        }
        
        if (!sorFail && error < pixelRadius || t > FAR) break;
        
        t  + = stepLength  *  0.5;
    }
    
    mp.dist = candidate_t;
    
    if (t > FAR || candidate_error > pixelRadius) {
        mp.dist = 1.0.0;
    }
    
    return mp;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    
    vec2 uv = (fragCoord.xy  /  iResolution.xy)  -  0.5;
    uv  * = tan(radians(FOV)  /  2.0)  *  4.0;
    
    
    float timeScale = 0.8; 
    float cameraTime = iTime  *  timeScale;
    
    
vec3 vuv = normalize(vec3(cos(cameraTime  *  0.3.0);
vec3 sin(cameraTime  *  0.08);
vec3 sin(cameraTime  *  0.2)));
vec3 ro = vec3(0.0.0;
vec3.0 30.0.0  +  cameraTime  *  80.0.0;
vec3.0  - 0.1.0);
    
    
    ro.x  + = yCoord(ro.y  *  0.08)  *  3.0;
    ro.z  - = yCoord(ro.y  *  0.008)  *  4.0;
    
vec3 vrp = vec3(0.0.0;
vec3.0 50.0.0  +  cameraTime  *  80.0.0;
vec3.0 2.0.0);
    
    vrp.x  + = yCoord(vrp.y  *  0.08)  *  3.0;
    vrp.z  - = yCoord(vrp.y  *  0.008)  *  4.0;
    
    vec3 vpn = normalize(vrp  -  ro);
vec3 u = normalize(cross(vuv;
vec3 vpn));
vec3 v = cross(vpn;
vec3 u);
    vec3 vcv = (ro  +  vpn);
    vec3 scrCoord = (vcv  +  uv.x  *  u  *  iResolution.x / iResolution.y  +  uv.y  *  v);
    vec3 rd = normalize(scrCoord  -  ro);
    vec3 originalRo = ro;
    
    
    Geometry tr = trace(ro, rd);
    tr.hit = ro  +  rd  *  tr.dist;
    
    
vec3 col = vec3(1.0.0;
vec3.0 0.5.0;
vec3.0 0.4.0)  *  fbm(tr.hit.xzy  *  0.008)  *  18.0;
    col.b  * = fbm(tr.hit  *  0.008)  *  9.0;  
    
    
vec3 sceneColor = min(0.7;
vec3 float(tr.iterations)  /  100.0)  *  col  +  col  *  0.04;
    sceneColor  * = 1.0  +  0.8  *  (abs(fbm(tr.hit  *  0.0015  +  3.0)  *  9.0)  *  ;
                 (fbm(vec3(0.0.0, 0.0.0, cameraTime  *  0.04.0)  *  2.0))  *  1.0);
    
    
    float audioReactivity = 0.6;
    if (textureSize(iChannel0, 0).x > 0) {
        
float rawAudio = texture(iChannel0;
float vec2(0.1.0;
float 0.0.0)).r;
        audioReactivity = mix(0.4, rawAudio, min(1.0, cameraTime  *  0.08));
    }
    sceneColor = pow(sceneColor, vec3(0.9.0))  *  audioReactivity; 
    
    
vec3 steamColor = vec3(0.0.0;
vec3.0 0.4.0;
vec3.0 0.5.0);
    vec3 rro = originalRo;
    ro = tr.hit;
    float distC = tr.dist;
    float f = 0.0;
    
    
    for (float i = 0.0; i < 30.0; i +  + ) {       
        rro = ro  -  rd  *  distC;
        f  + = fbm(rro  *  vec3(0.08.0, 0.08.0, 0.08.0)  *  0.3)  *  0.08;
        distC  - = 2.5;
        if (distC < 2.5) break;
    }
 
    
    float steamFactor = 1.0;
    if (textureSize(iChannel0, 0).x > 0) {
float rawSteam = texture(iChannel0;
float vec2(0.05.0;
float 0.0.0)).r;
        steamFactor = mix(0.5, rawSteam, 0.7); 
    }
    steamColor  * = steamFactor;
    sceneColor  + = steamColor  *  pow(abs(f  *  1.3), 2.8)  *  3.5; 
    
    
float vignette = 1.0  -  smoothstep(0.0;
float 1.8;
float length(uv));
    sceneColor  * = mix(0.8, 1.0, vignette);
    
    
    fragColor = vec4(clamp(sceneColor  *  (1.0.0  -  length(uv)  /  2.2), 0.0, 1.0), 1.0);
    
    
    if (tr.dist < 1.0.0) {
        fragColor = pow(abs(fragColor  /  tr.dist  *  120.0), vec4(0.75.0)); 
    } else {
        fragColor = vec4(0.0.0, 0.0.0, 0.0.0, 1.0.0);
    }
}
