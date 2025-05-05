// Warp Tunnel shader - Ultra Smooth Version
// Original by Shadertoy user

const float pi = acos(-1.0);
const float innerR = 1.0;
const float outerR = 12.0;

float globalTime = 0.0;

float dot2(in vec3 v) { return dot(v, v); }

// Improved hash function for smoother noise
vec3 hash3(vec2 p) {
    vec3 q = vec3(dot(p, vec2(127.1, 311.7)), 
                  dot(p, vec2(269.5, 183.3)), 
                  dot(p, vec2(419.2, 371.9)));
    return fract(sin(q) * 43758.5453);
}

// Smooth noise function with cubic interpolation
float smoothNoise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    
    // Cubic interpolation
    vec2 u = f * f * (3.0 - 2.0 * f);
    
    // Sample 4 corners
    float a = dot(hash3(i).xy, vec2(0.5));
    float b = dot(hash3(i + vec2(1.0, 0.0)).xy, vec2(0.5));
    float c = dot(hash3(i + vec2(0.0, 1.0)).xy, vec2(0.5));
    float d = dot(hash3(i + vec2(1.0, 1.0)).xy, vec2(0.5));
    
    // Bilinear interpolation with cubic smoothing
    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

// Fractal Brownian Motion for ultra-smooth noise
float fbm(vec2 p) {
    float sum = 0.0;
    float amp = 0.5;
    float freq = 1.0;
    
    // Add multiple octaves of noise
    for(int i = 0; i < 4; i++) {
        sum += smoothNoise(p * freq) * amp;
        amp *= 0.5;
        freq *= 2.0;
    }
    
    return sum;
}

// Adapted from IQ's iCappedCone: https://www.shadertoy.com/view/llcfRf
// Simplified with the assumption that the cone's axis is always the Z axis, and
// that the caps are not needed.
// Also, it automatically returns either the near or far intersection depending on
// the Z order of the endpoints.
float intersectCone(in vec3 ro, in vec3 rd, 
                   in float ra, in float rb,
                   in float paz, in float pbz)
{
    float ba = pbz - paz;
    vec3 oa = ro - vec3(0.0, 0.0, paz);
    vec3 ob = ro - vec3(0.0, 0.0, pbz);

    float m0 = ba * ba;
    float m1 = oa.z * ba;
    float m2 = ob.z * ba; 
    float m3 = rd.z * ba;

    // body
    float m4 = dot(rd, oa);
    float m5 = dot(oa, oa);
    float rr = ra - rb;
    float hy = m0 + rr * rr;

    float k2 = m0 * m0 - m3 * m3 * hy;
    float k1 = m0 * m0 * m4 - m1 * m3 * hy + m0 * ra * (rr * m3 * 1.0);
    float k0 = m0 * m0 * m5 - m1 * m1 * hy + m0 * ra * (rr * m1 * 2.0 - m0 * ra);

    float h = k1 * k1 - k2 * k0;
    if (h < 0.0) return -1.0;

    float t0 = (-k1 - sqrt(h)) / k2;
    float t1 = (-k1 + sqrt(h)) / k2;

    float y0 = m1 + t0 * m3;
    float y1 = m1 + t1 * m3;

    if (paz > pbz)
        return (y0 > 0.0 && y0 < m0) ? (-k1 - sqrt(h)) / k2 : -1.0;
    else
        return (y1 > 0.0 && y1 < m0) ? (-k1 + sqrt(h)) / k2 : -1.0;
}

float trace(vec3 ro, vec3 rd, out vec3 nearN, out vec2 nearUV)
{
    const int N = 6;

    float minT = 1e4;
    float outTh0 = 0.0;
    float outTh1 = 0.0;

    float twist = globalTime / 2.5;

    // Make a torus from cones
    for (int i = 0; i < N; ++i)
    {
        float th0 = pi * 2.0 / float(N) * float(i + 0) + twist;
        float th1 = pi * 2.0 / float(N) * float(i + 1) + twist;

        float z0 = sin(th0) * innerR;
        float z1 = sin(th1) * innerR;

        float r0 = outerR + cos(th0) * innerR;
        float r1 = outerR + cos(th1) * innerR;

        float t = intersectCone(ro, rd, r0, r1, z0, z1);

        if (t > 0.0 && t < minT)
        {
            // Save only the pertinent data for later construction
            // of shading inputs.
            outTh0 = th0;
            outTh1 = th1;
            minT = t;
        }
    }

    if (minT > 1e3)
        return -1.0;

    float th0 = outTh0;
    float th1 = outTh1;
    float th2 = (th0 + th1) / 2.0;

    vec3 rp = ro + rd * minT;

    float phi = atan(rp.y, rp.x);

    // Get the surface differentials and a reference point for texturing
    vec3 tangent = normalize(vec3(cos(phi) * cos(th1), sin(phi) * cos(th1), sin(th1)) -
                           vec3(cos(phi) * cos(th0), sin(phi) * cos(th0), sin(th0)));

    float incircleRadius = innerR * cos(pi / float(N));

    vec3 midPoint = vec3(cos(phi) * (outerR + cos(th2) * incircleRadius),
                      sin(phi) * (outerR + cos(th2) * incircleRadius), sin(th2) * incircleRadius);

    nearUV.x = (phi + pi) / pi * 16.0;
    nearUV.y = dot(rp - midPoint, tangent);

    nearN = vec3(cos(phi) * cos(th2), sin(phi) * cos(th2), sin(th2));

    return minT;
}

mat3 rotX(float a)
{
    return mat3(1.0, 0.0, 0.0,
                0.0, cos(a), sin(a),
                0.0, -sin(a), cos(a));
}

mat3 rotY(float a)
{
    return mat3(cos(a), 0.0, sin(a),
                0.0, 1.0, 0.0,
                -sin(a), 0.0, cos(a));
}

mat3 rotZ(float a)
{
    return mat3(cos(a), sin(a), 0.0,
                -sin(a), cos(a), 0.0,
                0.0, 0.0, 1.0);
}

// Smooth circle function with anti-aliasing
float smoothCircle(vec2 uv, float radius, float smoothness) {
    float dist = length(uv);
    return 1.0 - smoothstep(radius - smoothness, radius + smoothness, dist);
}

// Smooth line function with anti-aliasing
float smoothLine(float value, float position, float thickness) {
    float halfThick = thickness * 0.5;
    return smoothstep(position - halfThick - 0.01, position - halfThick, value) - 
           smoothstep(position + halfThick, position + halfThick + 0.01, value);
}

vec4 render(vec2 fragCoord)
{    
    // Create deterministic jitter for motion blur
    vec3 jitter = hash3(fragCoord * 0.01 + vec2(iTime * 0.1, 0.0));

    // Motion blur jitter
    globalTime = iTime + jitter.x * 1.0 / 60.0;
    
    // Set up primary ray, including ray differentials
    vec2 p = fragCoord / iResolution.xy * 2.0 - 1.0;
    p.x *= iResolution.x / iResolution.y;

    vec3 ro = vec3(outerR, sin(globalTime / 7.0) * 0.3, cos(globalTime / 5.0) * 0.3);
    vec3 rd = normalize(vec3(p, -1.5));
    
    // Rotation transformation. There is no translation here, because the tunnel
    // motion is faked with texture scrolling.
    mat3 m = rotZ(globalTime / 2.0) * rotX(cos(globalTime / 4.0) * 0.2) * rotY(sin(globalTime / 3.0) * 0.2);
    m = rotX(pi/2.0) * m;
    rd = m * rd;

    vec3 nearN = vec3(0.0);
    vec2 nearUV = vec2(0.0);

    vec3 transfer = vec3(1.0);    
    vec4 fragColor = vec4(0.0);

    // Trace ray bounces
    for (int j = 0; j < 3; ++j)
    {
        float t0 = trace(ro, rd, nearN, nearUV);

        if (t0 < 0.0)
            break;

        vec3 rp = ro + rd * t0;
        vec3 c = vec3(0.0);

        // Fake motion-blurred camera motion by blurring the
        // surface shading. Note that the non-jittered time value
        // is used here as a base time for the blur offset.
        const int motionBlurSamples = 8; // Increased samples for smoother motion blur

        for (int i = 0; i < motionBlurSamples; ++i)
        {
            // Tunnel surface shading
            float time = iTime + (float(i) + jitter.x) / float(motionBlurSamples) * (1.0 / 60.0);
            vec2 uv = nearUV;
            uv.x += time * 5.0;
            
            // Ultra-smooth pattern with anti-aliasing
            vec2 circleUV = fract(uv + vec2(0.25, 0.5)) - 0.5;
            
            // Smooth circles with proper anti-aliasing
            float circle1 = smoothCircle(circleUV, 0.4, 0.05);
            float circle2 = smoothCircle(circleUV, 0.1, 0.01);
            
            c += vec3(pow(circle1, 8.0)) * vec3(0.3, 0.5, 1.0) * 2.0;
            c += vec3(circle2) * vec3(0.3, 0.5, 1.0) * 4.0;
            
            // Smooth horizontal lines
            float line1 = smoothLine(fract(uv.x - 0.3), 0.9, 0.05);
            float line2 = smoothLine(fract(uv.x - 0.3), 0.95, 0.02);
            
            c += vec3(line1) / 2.0 * vec3(0.4, 0.4, 1.0) * 3.0;
            c += vec3(line2) / 2.0 * vec3(0.4, 0.4, 1.0) * 6.0;
            
            // Smooth noise pattern using FBM
            float noiseVal = fbm(uv / 15.0 + time / 10.0 * vec2(1.0, 0.0));
            float noiseLine1 = smoothstep(0.58, 0.62, noiseVal) * smoothstep(0.62, 0.58, noiseVal);
            float noiseLine2 = smoothstep(0.595, 0.605, noiseVal) * smoothstep(0.605, 0.595, noiseVal);
            
            c += noiseLine1 / 4.0 * vec3(0.4, 0.4, 1.0);
            c += noiseLine2 * 2.0 * vec3(0.4, 0.4, 1.0);
            
            // Smooth horizontal grid lines
            float gridLine1 = smoothLine(uv.y, 0.0, 0.01);
            float gridLine2 = smoothLine(uv.y, 0.5, 0.01);
            
            c += vec3(gridLine1) * 1.5;
            c += vec3(gridLine2) * 1.5;
        }

        c /= float(motionBlurSamples);

        // Smooth fog transition
        c = mix(vec3(1.0) * vec3(0.5, 0.5, 1.0), c, exp2(-t0 / 13.0));

        // Tint
        c *= vec3(0.6, 0.6, 1.0) / 1.3;

        // Accumulate
        fragColor.rgb += c * transfer;
        
        // Reflection amount with smoother falloff
        transfer *= 0.8 * pow(clamp(1.0 - dot(-nearN, -rd), 0.0, 1.0), 4.0);

        if (max(max(transfer.x, transfer.y), transfer.z) < 1e-3)
            break;
        
        // Reflect
        ro = rp + nearN * 1e-4;
        rd = reflect(rd, nearN);

        jitter = jitter.yzx;
    }

    fragColor.a = 1.0;
    return fragColor;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord)
{
    fragColor = vec4(0.0);
    vec3 backg = vec3(0.07);

    // Enhanced anti-aliasing with 4x4 supersampling
    const int AA = 4;
    for (int y = 0; y < AA; ++y)
        for (int x = 0; x < AA; ++x)
        {
            vec2 offset = vec2(float(x), float(y)) / float(AA) - 0.5;
            vec4 r = render(fragCoord + offset);
            r.rgb = mix(backg, r.rgb, r.a);
            fragColor.rgb += clamp(r.rgb, 0.0, 1.0);
        }

    fragColor /= float(AA * AA);

    // Enhanced tonemapping for smoother highlights
    fragColor.rgb = fragColor.rgb / (fragColor.rgb + 0.4);
    
    // Subtle color grading
    fragColor.rgb = pow(fragColor.rgb, vec3(1.0, 1.4, 1.8));
    
    // Subtle vignette effect
    vec2 uv = fragCoord / iResolution.xy;
    float vignette = smoothstep(1.0, 0.3, length((uv - 0.5) * 1.5));
    fragColor.rgb *= mix(1.0, vignette, 0.3);

    // Gamma correction
    fragColor.rgb = pow(clamp(fragColor.rgb, 0.0, 1.0), vec3(1.0 / 2.2));
    fragColor.a = 1.0;
}
