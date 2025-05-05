// Cloud Ten - Optimized Fixed version
// Original by nimitz 2015 (twitter: @stormoid)
// License Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License

#define time iTime

// Optimized hash function - simpler but still high quality
float hash12(vec2 p) {
    vec3 p3 = fract(vec3(p.xyx) * vec3(443.8975, 397.2973, 491.1871));
    p3 += dot(p3.zxy, p3.yxz + 19.19);
    return fract(p3.x * p3.y * p3.z);
}

// Optimized 3D noise function with smooth interpolation
float noise(in vec3 p) {
    vec3 i = floor(p);
    vec3 f = fract(p);
    
    // Smoother interpolation (cheaper than cubic)
    vec3 u = f * f * (3.0 - 2.0 * f);
    
    // Sample 8 corners with fewer operations
    float n000 = hash12(i.xy + vec2(0.0, 0.0) + i.z * 11.0);
    float n100 = hash12(i.xy + vec2(1.0, 0.0) + i.z * 11.0);
    float n010 = hash12(i.xy + vec2(0.0, 1.0) + i.z * 11.0);
    float n110 = hash12(i.xy + vec2(1.0, 1.0) + i.z * 11.0);
    float n001 = hash12(i.xy + vec2(0.0, 0.0) + (i.z + 1.0) * 11.0);
    float n101 = hash12(i.xy + vec2(1.0, 0.0) + (i.z + 1.0) * 11.0);
    float n011 = hash12(i.xy + vec2(0.0, 1.0) + (i.z + 1.0) * 11.0);
    float n111 = hash12(i.xy + vec2(1.0, 1.0) + (i.z + 1.0) * 11.0);
    
    // Optimized trilinear interpolation
    return mix(
        mix(mix(n000, n100, u.x), mix(n010, n110, u.x), u.y),
        mix(mix(n001, n101, u.x), mix(n011, n111, u.x), u.y),
        u.z
    );
}

// Optimized FBM with fewer octaves but still good quality
float fbm(in vec3 x) {
    float rz = 0.0;
    float a = 0.5;
    float freq = 1.0;
    
    // Use 3 octaves instead of 4 for better performance
    for (int i = 0; i < 3; i++) {
        rz += noise(x * freq) * a;
        a *= 0.5;
        freq *= 2.0;
    }
    return rz;
}

mat2 mm2(in float a) {
    float c = cos(a), s = sin(a);
    return mat2(c, s, -s, c);
}

float path(in float x) { 
    return sin(x * 0.01 - 3.1415) * 28.0 + 6.5; 
}

// Optimized map function with good detail but fewer calculations
float map(vec3 p) {
    // Base cloud shape
    float base = p.y * 0.07 + (fbm(p * 0.3) - 0.1);
    float detail = sin(p.x * 0.24 + sin(p.z * 0.01) * 7.0) * 0.22 + 0.15 + sin(p.z * 0.08) * 0.05;
    
    // Add detail only where it matters most (near cloud surface)
    float microDetail = 0.0;
    if (base + detail > -0.1 && base + detail < 0.1) {
        microDetail = fbm(p * 1.5) * 0.03;
    }
    
    return base + detail + microDetail;
}

float march(in vec3 ro, in vec3 rd) {
    float precis = 0.3;
    float h = 1.0;
    float d = 0.0;
    for (int i = 0; i < 17; i++) {
        if (abs(h) < precis || d > 70.0) break;
        d += h;
        vec3 pos = ro + rd * d;
        pos.y += 0.5;
        float res = map(pos) * 7.0;
        h = res;
    }
    return d;
}

float mapV(vec3 p) { 
    return clamp(-map(p), 0.0, 1.0);
}

// Optimized volume marching with adaptive step sizes
vec4 marchV(in vec3 ro, in vec3 rd, in float t, in vec3 bgc, in vec3 lgt, in float mouseY) {
    vec4 rz = vec4(0.0);
    
    // Adaptive step count based on distance
    int maxSteps = 150;
    float stepMultiplier = 1.0;
    
    // If we're far away, use fewer steps
    if (t > 40.0) {
        maxSteps = 120;
        stepMultiplier = 1.2;
    }
    
    for (int i = 0; i < maxSteps; i++) {
        if (rz.a > 0.99 || t > 200.0) break;
        
        vec3 pos = ro + t * rd;
        float den = mapV(pos);
        
        // Skip very low density areas
        if (den < 0.01) {
            t += 0.5 * stepMultiplier;
            continue;
        }
        
        // Cloud coloring
        vec4 col = vec4(mix(vec3(0.8, 0.75, 0.85), vec3(0.0), den), den);
        col.xyz *= mix(bgc * bgc * 2.5, mix(vec3(0.1, 0.2, 0.55), vec3(0.8, 0.85, 0.9), mouseY * 0.4), 
                    clamp(-(den * 40.0 + 0.0) * pos.y * 0.03 - mouseY * 0.5, 0.0, 1.0));
        
        // Lighting and fringes
        col.rgb += clamp((1.0 - den * 6.0) + pos.y * 0.13 + 0.55, 0.0, 1.0) * 0.35 * mix(bgc, vec3(1.0), 0.7);
        col += clamp(den * pos.y * 0.15, -0.02, 0.0);
        
        // Simplified shadows
        float shadowSoftness = 0.2 + mouseY * 0.05;
        col *= smoothstep(shadowSoftness, 0.0, mapV(pos + 1.0 * lgt)) * 0.85 + 0.15;
        
        // Alpha blending
        col.a *= 0.95;
        col.rgb *= col.a;
        rz = rz + col * (1.0 - rz.a);

        // Adaptive step size - larger steps in low density areas
        float stepSize = max(0.3, (2.0 - den * 30.0) * t * 0.011) * stepMultiplier;
        
        // Take larger steps in areas of consistent density
        if (i > 0 && i % 10 == 0 && den < 0.1) {
            stepSize *= 1.5;
        }
        
        t += stepSize;
    }

    return clamp(rz, 0.0, 1.0);
}

float pent(in vec2 p) {    
    vec2 q = abs(p);
    return max(max(q.x * 1.176 - p.y * 0.385, q.x * 0.727 + p.y), -p.y * 1.237) * 1.0;
}

// Simplified lens flare
vec3 lensFlare(vec2 p, vec2 pos) {
    vec2 q = p - pos;
    float dq = dot(q, q);
    vec2 dist = p * (length(p)) * 0.75;
    float ang = atan(q.x, q.y);
    vec2 pp = mix(p, dist, 0.5);
    float sz = 0.01;
    
    // Simplified flare calculation
    float rz = pow(abs(fract(ang * 0.8 + 0.12) - 0.5), 3.0) * 0.5;
    rz *= smoothstep(1.0, 0.0, dq);
    rz *= smoothstep(0.0, 0.01, dq);
    
    // Fewer flare elements
    rz += max(1.0 / (1.0 + 30.0 * pent(dist + 0.8 * pos)), 0.0) * 0.17;
    rz += clamp(sz - pow(pent(pp + 0.15 * pos), 1.55), 0.0, 1.0) * 5.0;
    rz += clamp(sz - pow(pent(pp - 0.05 * pos), 1.2), 0.0, 1.0) * 4.0;
    rz += clamp(sz - pow(pent((pp + 0.5 * pos)), 1.7), 0.0, 1.0) * 4.0;
    
    return vec3(clamp(rz, 0.0, 1.0));
}

mat3 rot_x(float a) {
    float sa = sin(a); 
    float ca = cos(a); 
    return mat3(1.0, 0.0, 0.0, 0.0, ca, sa, 0.0, -sa, ca);
}

mat3 rot_y(float a) {
    float sa = sin(a); 
    float ca = cos(a); 
    return mat3(ca, 0.0, sa, 0.0, 1.0, 0.0, -sa, 0.0, ca);
}

mat3 rot_z(float a) {
    float sa = sin(a); 
    float ca = cos(a); 
    return mat3(ca, sa, 0.0, -sa, ca, 0.0, 0.0, 0.0, 1.0);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {    
    // Optimized anti-aliasing - 1.5x supersampling instead of 2x
    vec4 finalColor = vec4(0.0);
    
    // Use 3 samples in a triangle pattern instead of 4 in a square
    const vec2 offsets[3] = vec2[3](
        vec2(0.0, 0.0),
        vec2(0.66, 0.33),
        vec2(0.33, 0.66)
    );
    
    for (int i = 0; i < 3; i++) {
        vec2 offset = offsets[i];
        vec2 uv = (fragCoord + offset) / iResolution.xy;
        vec2 p = uv - 0.5;
        float asp = iResolution.x / iResolution.y;
        p.x *= asp;
        
        vec2 mo = iMouse.xy / iResolution.xy;
        float mouseY = mo.y;
        float st = sin(time * 0.3 - 1.3) * 0.2;
        vec3 ro = vec3(0.0, -2.0 + sin(time * 0.3 - 1.0) * 2.0, time * 30.0);
        ro.x = path(ro.z);
        vec3 ta = ro + vec3(0.0, 0.0, 1.0);
        vec3 fw = normalize(ta - ro);
        vec3 uu = normalize(cross(vec3(0.0, 1.0, 0.0), fw));
        vec3 vv = normalize(cross(fw, uu));
        const float zoom = 1.0;
        vec3 rd = normalize(p.x * uu + p.y * vv + -zoom * fw);
        
        float rox = sin(time * 0.2) * 0.6 + 2.9;
        rox += smoothstep(0.6, 1.2, sin(time * 0.25)) * 3.5;
        float roy = sin(time * 0.5) * 0.2;
        mat3 rotation = rot_x(-roy) * rot_y(-rox + st * 1.5) * rot_z(st);
        mat3 inv_rotation = rot_z(-st) * rot_y(rox - st * 1.5) * rot_x(roy);
        rd *= rotation;
        rd.y -= dot(p, p) * 0.06;
        rd = normalize(rd);
        
        vec3 col = vec3(0.0);
        vec3 lgt = normalize(vec3(-0.3, mouseY + 0.1, 1.0));  
        float rdl = clamp(dot(rd, lgt), 0.0, 1.0);
      
        // Sky gradient
        vec3 hor = mix(vec3(0.9, 0.6, 0.7) * 0.35, vec3(0.5, 0.05, 0.05), rdl);
        hor = mix(hor, vec3(0.5, 0.8, 1.0), mouseY);
        col += mix(vec3(0.2, 0.2, 0.6), hor, exp2(-(1.0 + 3.0 * (1.0 - rdl)) * max(abs(rd.y), 0.0))) * 0.6;
        
        // Sun glare
        col += 0.8 * vec3(1.0, 0.9, 0.9) * exp2(rdl * 650.0 - 650.0);
        col += 0.3 * vec3(1.0, 1.0, 0.1) * exp2(rdl * 100.0 - 100.0);
        col += 0.5 * vec3(1.0, 0.7, 0.0) * exp2(rdl * 50.0 - 50.0);
        col += 0.4 * vec3(1.0, 0.0, 0.05) * exp2(rdl * 10.0 - 10.0);  
        vec3 bgc = col;
        
        float rz = march(ro, rd);
        
        if (rz < 70.0) {   
            vec4 res = marchV(ro, rd, rz - 5.0, bgc, lgt, mouseY);
            col = col * (1.0 - res.w) + res.xyz;
        }
        
        vec3 proj = (-lgt * inv_rotation);
        col += 1.4 * vec3(0.7, 0.7, 0.4) * clamp(lensFlare(p, -proj.xy / proj.z * zoom) * proj.z, 0.0, 1.0);
        
        float g = smoothstep(0.03, 0.97, mo.x);
        col = mix(mix(col, col.brg * vec3(1.0, 0.75, 1.0), clamp(g * 2.0, 0.0, 1.0)), col.bgr, clamp((g - 0.5) * 2.0, 0.0, 1.0));
        
        // Color grading
        col = clamp(col, 0.0, 1.0);
        col = col * 0.5 + 0.5 * col * col * (3.0 - 2.0 * col); // saturation
        col = pow(col, vec3(0.416667)) * 1.055 - 0.055; // sRGB
        
        // Vignette
        float vignette = pow(16.0 * uv.x * uv.y * (1.0 - uv.x) * (1.0 - uv.y), 0.12);
        col *= vignette;
        
        // Accumulate for anti-aliasing
        finalColor += vec4(col, 1.0);
    }
    
    // Average the samples
    fragColor = finalColor / 3.0;
}
