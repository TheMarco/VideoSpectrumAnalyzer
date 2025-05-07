/*

[C]
by Marco van Hylckama Vlieg
https://www.shadertoy.com/view/w32SDc
[/C]

Based on the work by patu:
https://www.shadertoy.com/view/4t2cR1


*/

// Constants
#define FAR 1000.0
#define PI 3.14159265
#define FOV 70.0
#define FOG 0.8  // Further reduced fog for smoother look
#define MAX_ITERATIONS 150  // Increased iterations for smoother results

// Improved hash function for smoother noise
float hash12(vec2 p) {
    p = fract(p * vec2(123.4, 456.7));
    p += dot(p, p + 89.1);
    return fract(p.x * p.y);
}

// Improved 3D noise function with better interpolation
float noise3D(in vec3 p) {
    vec3 i = floor(p);
    vec3 f = fract(p);    
    vec3 u = f * f * (3.0 - 2.0 * f); // Improved smoothing
    
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
        
    return mix(v1, v2, u.z);
}

// Enhanced Fractal Brownian Motion for smoother detail
float fbm(vec3 x) {
    float r = 0.0;
    float w = 1.0;
    float s = 1.0;
    
    for (int i = 0; i < 5; i++) {
        w *= 0.5;
        s *= 2.0;
        r += w * noise3D(s * x);
    }
    
    return r;
}

// Color palette function for earthy, natural tones
vec3 palette(float t) {
    // Earthy color palette with browns, ambers, and deep greens
    vec3 a = vec3(0.5, 0.3, 0.2);    // Warm brown base
    vec3 b = vec3(0.4, 0.3, 0.2);    // Moderate color variation for natural shifts
    vec3 c = vec3(1.0, 1.0, 1.0);
    vec3 d = vec3(0.3, 0.2, 0.1);    // Phase shift for earth tone cycling
    
    return a + b * cos(6.28318 * (c * t + d));
}

// Ultra-smooth Y-coordinate function with minimal oscillation
float yCoord(float x) {
    // Drastically reduced amplitude and frequency for minimal movement
    return cos(x * -0.05) * sin(x * 0.04) * 0.1; // Reduced from 6.0 to 0.1
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

// Infinite cylinder SDF with smoothing
float cylinderSDF(vec3 p, float r) {
    return length(p.xz) - r;
}

// Smoother map function for SDF
Geometry map(vec3 p) {
    // Ultra-smooth path movement with minimal displacement
    float timeScale = 0.06; // Increased from 0.04 for faster movement
    
    // Drastically reduced displacement amounts
    p.x -= yCoord(p.y * 0.04) * 1.5;
    p.z += yCoord(p.y * 0.004) * 2.0;
    
    // Smoother noise variation with reduced intensity
    float n = pow(abs(fbm(p * 0.02)) * 8.0, 1.2);
    float s = fbm(p * 0.004 + vec3(0.0, iTime * 0.05, 0.0)) * 100.0;
    
    Geometry obj;
    obj.dist = max(0.0, -cylinderSDF(p, s + 20.0 - n));
    
    // Smoother secondary displacement with reduced amplitude
    p.x -= sin(p.y * 0.008) * 15.0 + cos(p.z * 0.004) * 25.0;
    obj.dist = max(obj.dist, -cylinderSDF(p, s + 30.0 + n * 2.0));
    
    return obj;
}

// Enhanced ray marching function with better convergence
Geometry trace(vec3 ro, vec3 rd) {
    float t = 10.0;
    float omega = 1.1; // Further reduced for more stability
    float previousRadius = 0.0;
    float stepLength = 0.0;
    float pixelRadius = 1.0 / 1500.0; // Further increased precision
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
    // Screen coordinates with smoother anti-aliasing
    vec2 uv = (fragCoord.xy / iResolution.xy) - 0.5;
    uv *= tan(radians(FOV) / 2.0) * 4.0;
    
    // Ultra-smooth camera movement with increased speed
    float timeScale = 0.9; // Increased from 0.4 for faster movement
    float cameraTime = iTime * timeScale;
    
    // Camera setup with ultra-smooth motion - minimal oscillation
    // Drastically reduced oscillation amplitudes and frequencies
    vec3 vuv = normalize(vec3(0.0, 1.0, 0.0)); // Fixed up vector
    vec3 ro = vec3(0.0, 30.0 + cameraTime * 90.0, -0.1); // Increased from 60.0 for faster forward movement
    
    // Ultra-smooth path following with minimal displacement
    ro.x += yCoord(ro.y * 0.04) * 0.1; // Reduced from 1.5 to 0.1
    ro.z -= yCoord(ro.y * 0.004) * 0.1; // Reduced from 2.0 to 0.1
    
    // Target point with ultra-smooth motion
    vec3 vrp = vec3(0.0, 50.0 + cameraTime * 90.0, 2.0); // Increased from 60.0 for faster forward movement
    
    // Apply same minimal displacement to target for consistent movement
    vrp.x += yCoord(vrp.y * 0.04) * 0.1; // Reduced from 1.5 to 0.1
    vrp.z -= yCoord(vrp.y * 0.004) * 0.1; // Reduced from 2.0 to 0.1
    
    // Camera orientation with ultra-smooth transitions
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
    
    // Color variation based on position and time
    float colorPos = tr.hit.y * 0.01 + cameraTime * 0.2;
    vec3 baseColor = palette(colorPos);
    
    // Earthy coloring with natural tones
    vec3 col = baseColor * fbm(tr.hit.xzy * 0.004) * 5.0;
    
    // Enhance red/brown channel
    col.r *= fbm(tr.hit * 0.004) * 4.0;
    
    // Enhance yellow/amber tones
    col.g *= fbm(tr.hit * 0.003) * 3.5;
    
    // Reduce blue for more earthy dominance
    col.b *= fbm(tr.hit * 0.005) * 2.0;
    
    // Add color variation based on depth
    float depthFactor = min(0.6, float(tr.iterations) / 120.0);
    vec3 depthColor = palette(colorPos * 0.5 + 0.3);
    
    // Scene color transition with earthy tones
    vec3 sceneColor = depthFactor * col + col * 0.03;
    sceneColor *= 1.0 + 0.25 * (abs(fbm(tr.hit * 0.0008 + 3.0) * 5.0) *
                 (fbm(vec3(0.0, 0.0, cameraTime * 0.02) * 2.0)) * 1.0);
    
    // Add amber highlights
    float amberAccent = smoothstep(0.75, 0.92, fbm(tr.hit * 0.003));
    sceneColor = mix(sceneColor, vec3(0.9, 0.7, 0.3), amberAccent * 0.25);
    
    // Add deep brown/black accents
    float brownAccent = smoothstep(0.4, 0.2, fbm(tr.hit * 0.002));
    sceneColor = mix(sceneColor, vec3(0.1, 0.05, 0.02), brownAccent * 0.4);
    
    // Apply contrast adjustment for natural look
    sceneColor = pow(sceneColor, vec3(0.85));
    
    // Steam effect with earthy tones
    vec3 steamColor = palette(colorPos * 0.5 + 0.7) * vec3(0.6, 0.4, 0.2);
    vec3 rro = originalRo;
    ro = tr.hit;
    float distC = tr.dist;
    float f = 0.0;
    
    // Steam iterations
    for (float i = 0.0; i < 40.0; i++) {       
        rro = ro - rd * distC;
        f += fbm(rro * vec3(0.04, 0.04, 0.04) * 0.3) * 0.05;
        distC -= 2.0;
        if (distC < 2.0) break;
    }
 
    // Add colored steam effect with earthy tones
    sceneColor += steamColor * pow(abs(f * 1.1), 2.5) * 1.2;
    
    // Add subtle earthy highlights
    sceneColor += palette(colorPos * 0.2 + 1.5) * pow(abs(dot(rd, normalize(vec3(1.0, 0.5, 0.0)))), 8.0) * 0.07;
    
    // Smoother vignette
    float vignette = 1.0 - smoothstep(0.0, 2.0, length(uv));
    sceneColor *= mix(0.85, 1.0, vignette);
    
    // Final color with smoother tone mapping
    fragColor = vec4(clamp(sceneColor * (1.0 - length(uv) / 2.5), 0.0, 1.0), 1.0);
    
    // Apply distance-based intensity and ultra-smooth tone mapping
    if (tr.dist < 1.0e30) {
        // Soften bright areas and avoid pure whites
        fragColor = pow(abs(fragColor / tr.dist * 100.0), vec4(0.75));  // Reduced from 120.0 and increased from 0.7
        fragColor = min(fragColor, vec4(0.9, 0.9, 0.9, 1.0));  // Cap brightness to avoid pure whites
    } else {
        fragColor = vec4(0.0, 0.0, 0.0, 1.0);
    }
}
