// Hyper Tunnel - Completely rewritten version
// Based on the original "Sailing Beyond" demoscene production
// https://www.youtube.com/watch?v=oITx9xMrAcM
// https://www.pouet.net/prod.php?which=77899

// Constants
#define FAR 1000.0
#define PI 3.14159265
#define FOV 70.0
#define FOG 0.06
#define MAX_ITERATIONS 100

// Hash function for noise
float hash12(vec2 p) {
    float h = dot(p, vec2(127.1, 311.7));    
    return fract(sin(h) * 43758.5453123);
}

// 3D noise function
float noise3D(in vec3 p) {
    vec3 i = floor(p);
    vec3 f = fract(p);    
    vec3 u = f * f * (3.0 - 2.0 * f);
    
    vec2 ii = i.xy + i.z * vec2(5.0);
    float a = hash12(ii + vec2(0.0, 0.0));
    float b = hash12(ii + vec2(1.0, 0.0));    
    float c = hash12(ii + vec2(0.0, 1.0));
    float d = hash12(ii + vec2(1.0, 1.0)); 
    float v1 = mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
    
    ii += vec2(5.0);
    a = hash12(ii + vec2(0.0, 0.0));
    b = hash12(ii + vec2(1.0, 0.0));    
    c = hash12(ii + vec2(0.0, 1.0));
    d = hash12(ii + vec2(1.0, 1.0));
    float v2 = mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
        
    return max(mix(v1, v2, u.z), 0.0);
}

// Fractal Brownian Motion
float fbm(vec3 x) {
    float r = 0.0;
    float w = 1.0;
    float s = 1.0;
    
    for (int i = 0; i < 4; i++) {
        w *= 0.25;
        s *= 3.0;
        r += w * noise3D(s * x);
    }
    
    return r;
}
 
// Y-coordinate function
float yCoord(float x) {
    return cos(x * -0.134) * sin(x * 0.13) * 15.0 + 
           fbm(vec3(x * 0.1, 0.0, 0.0) * 55.4);
}

// Rotation function
void rotate(inout vec2 p, float a) {
    p = cos(a) * p + sin(a) * vec2(p.y, -p.x);
}

// Geometry structure
struct Geometry {
    float dist;
    vec3 hit;
    int iterations;
};

// Infinite cylinder SDF
float cylinderSDF(vec3 p, float r) {
    return length(p.xz) - r;
}

// Map function for SDF
Geometry map(vec3 p) {
    p.x -= yCoord(p.y * 0.1) * 3.0;
    p.z += yCoord(p.y * 0.01) * 4.0;
    
    float n = pow(abs(fbm(p * 0.06)) * 12.0, 1.3);
    float s = fbm(p * 0.01 + vec3(0.0, iTime * 0.14, 0.0)) * 128.0;
    
    Geometry obj;
    obj.dist = max(0.0, -cylinderSDF(p, s + 18.0 - n));
    
    p.x -= sin(p.y * 0.02) * 34.0 + cos(p.z * 0.01) * 62.0;
    obj.dist = max(obj.dist, -cylinderSDF(p, s + 28.0 + n * 2.0));
    
    return obj;
}

// Ray marching function
Geometry trace(vec3 ro, vec3 rd) {
    float t = 10.0;
    float omega = 1.3;
    float previousRadius = 0.0;
    float stepLength = 0.0;
    float pixelRadius = 1.0 / 1000.0;
    float candidate_error = 1.0e32;
    float candidate_t = 10.0;
    
    Geometry mp = map(ro);
    float functionSign = mp.dist < 0.0 ? -1.0 : 1.0;
    
    for (int i = 0; i < MAX_ITERATIONS; i++) {
        mp = map(ro + rd * t);
        mp.iterations = i;
    
        float signedRadius = functionSign * mp.dist;
        float radius = abs(signedRadius);
        bool sorFail = omega > 1.0 && (radius + previousRadius) < stepLength;
        
        if (sorFail) {
            stepLength -= omega * stepLength;
            omega = 1.0;
        } else {
            stepLength = signedRadius * omega;
        }
        
        previousRadius = radius;
        float error = radius / t;
        
        if (!sorFail && error < candidate_error) {
            candidate_t = t;
            candidate_error = error;
        }
        
        if (!sorFail && error < pixelRadius || t > FAR) break;
        
        t += stepLength * 0.5;
    }
    
    mp.dist = candidate_t;
    
    if (t > FAR || candidate_error > pixelRadius) {
        mp.dist = 1.0e32;
    }
    
    return mp;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // Screen coordinates
    vec2 uv = (fragCoord.xy / iResolution.xy) - 0.5;
    uv *= tan(radians(FOV) / 2.0) * 4.0;
    
    // Camera setup
    vec3 vuv = normalize(vec3(cos(iTime), sin(iTime * 0.11), sin(iTime * 0.41)));
    vec3 ro = vec3(0.0, 30.0 + iTime * 100.0, -0.1);
    
    ro.x += yCoord(ro.y * 0.1) * 3.0;
    ro.z -= yCoord(ro.y * 0.01) * 4.0;
    
    vec3 vrp = vec3(0.0, 50.0 + iTime * 100.0, 2.0);
    
    vrp.x += yCoord(vrp.y * 0.1) * 3.0;
    vrp.z -= yCoord(vrp.y * 0.01) * 4.0;
    
    vec3 vpn = normalize(vrp - ro);
    vec3 u = normalize(cross(vuv, vpn));
    vec3 v = cross(vpn, u);
    vec3 vcv = (ro + vpn);
    vec3 scrCoord = (vcv + uv.x * u * iResolution.x/iResolution.y + uv.y * v);
    vec3 rd = normalize(scrCoord - ro);
    vec3 originalRo = ro;
    
    // Ray marching
    Geometry tr = trace(ro, rd);
    tr.hit = ro + rd * tr.dist;
    
    // Coloring
    vec3 col = vec3(1.0, 0.5, 0.4) * fbm(tr.hit.xzy * 0.01) * 20.0;
    col.b *= fbm(tr.hit * 0.01) * 10.0;  
    
    vec3 sceneColor = min(0.8, float(tr.iterations) / 90.0) * col + col * 0.03;
    sceneColor *= 1.0 + 0.9 * (abs(fbm(tr.hit * 0.002 + 3.0) * 10.0) * 
                 (fbm(vec3(0.0, 0.0, iTime * 0.05) * 2.0)) * 1.0);
    
    // Audio reactivity (simulated)
    float audioReactivity = 0.6;
    if (textureSize(iChannel0, 0).x > 0) {
        audioReactivity = texture(iChannel0, vec2(0.1, 0.0)).r * min(1.0, iTime * 0.1);
    }
    sceneColor = pow(sceneColor, vec3(1.0)) * audioReactivity;
    
    // Steam effect
    vec3 steamColor = vec3(0.0, 0.4, 0.5);
    vec3 rro = originalRo;
    ro = tr.hit;
    float distC = tr.dist;
    float f = 0.0;
    
    for (float i = 0.0; i < 24.0; i++) {       
        rro = ro - rd * distC;
        f += fbm(rro * vec3(0.1, 0.1, 0.1) * 0.3) * 0.1;
        distC -= 3.0;
        if (distC < 3.0) break;
    }
 
    // Steam color modulation
    float steamFactor = 1.0;
    if (textureSize(iChannel0, 0).x > 0) {
        steamFactor = texture(iChannel0, vec2(0.05, 0.0)).r;
    }
    steamColor *= steamFactor;
    sceneColor += steamColor * pow(abs(f * 1.5), 3.0) * 4.0;
    
    // Final color
    fragColor = vec4(clamp(sceneColor * (1.0 - length(uv) / 2.0), 0.0, 1.0), 1.0);
    
    // Apply distance-based intensity and tone mapping
    if (tr.dist < 1.0e30) {
        fragColor = pow(abs(fragColor / tr.dist * 130.0), vec4(0.8));
    } else {
        fragColor = vec4(0.0, 0.0, 0.0, 1.0);
    }
}
