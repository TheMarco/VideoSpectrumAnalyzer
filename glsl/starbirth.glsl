/*
[C]
by Marco van Hylckama Vlieg
https://www.shadertoy.com/view/wfd3zr
[/C]
*/
// StarBirth: Fully AI vibe coded simulation of Hubble telescope images
// by Marco van Hylckama Vlieg (@AIandDesign on X / YouTube)
// Fixed version for VideoSpectrumAnalyzer

#define PI 3.14159265359
#define ITERATIONS_FBM   8
#define ITERATIONS_RAYMARCH 8
#define TIME_OFFSET 80

// Spatial-Density Starfield Settings
#define CELL_SIZE    40.0      // Size of grid cells for star placement
#define DENSITY      0.70      // Base probability a cell contains a star
#define DENSITY_VAR  0.45      // Variation in density across regions
#define REGION_CELLS 8.0       // Number of cells per density region
#define MAX_RADIUS   5.0       // Max radius for SMALL stars (in pixels)
#define BRIGHT_BOOST 1.0       // Brightness multiplier for SMALL stars

// Large Star Settings
#define BIG_STAR_THRESHOLD 0.93 // Probability threshold for a star to be large (0.0-1.0)
#define BIG_STAR_MIN_RADIUS 10.0 // Min radius for LARGE star bloom (in pixels)
#define BIG_STAR_MAX_RADIUS 40.0 // Max radius for LARGE star bloom (in pixels)
#define BIG_STAR_BRIGHT_MIN 0.7  // Min brightness multiplier for LARGE stars
#define BIG_STAR_BRIGHT_MAX 2.8  // Max brightness multiplier for LARGE stars
#define BIG_STAR_COLOR_WARM vec3(1.0, 0.8, 0.5) // Color option 1 for large stars
#define BIG_STAR_COLOR_COOL vec3(0.7, 0.8, 1.0) // Color option 2 for large stars

// Additional Fixed Large Stars Settings
#define EXTRA_STAR_1_POS vec2(-0.2, 0.15) // Position in uv space relative to center
#define EXTRA_STAR_1_RADIUS 0.13          // Radius in uv space
#define EXTRA_STAR_1_COLOR vec3(1.0, 0.9, 0.7) // Color (warm white)
#define EXTRA_STAR_1_BRIGHTNESS 1.2         // Brightness multiplier

#define EXTRA_STAR_2_POS vec2(0.25, -0.1) // Position in uv space relative to center
#define EXTRA_STAR_2_RADIUS 0.09          // Radius in uv space
#define EXTRA_STAR_2_COLOR vec3(0.8, 0.9, 1.0) // Color (cool blueish)
#define EXTRA_STAR_2_BRIGHTNESS 1.2         // Brightness multiplier

// Rotation Helper
mat2 rotate(float a) {
    float s = sin(a);
    float c = cos(a);
    return mat2(c, -s, s, c);
}

// Hash Helpers
float hash1(float n) {
    return fract(sin(n) * 43758.5453);
}

vec2 hash2(vec2 p) {
    return fract(
        sin(vec2(
            dot(p, vec2(127.1, 311.7)),
            dot(p, vec2(269.5, 183.3))
        )) * 43758.5453
    );
}

float hash(vec2 p) {
    p = fract(p * vec2(123.34, 345.45));
    p += dot(p, p + 34.345);
    return fract(p.x * p.y);
}

// 2D Value Noise & FBM
float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f*f*(3.0 - 2.0*f);
    float a = hash(i + vec2(0.0,0.0));
    float b = hash(i + vec2(1.0,0.0));
    float c = hash(i + vec2(0.0,1.0));
    float d = hash(i + vec2(1.0,1.0));
    return mix(mix(a,b,f.x), mix(c,d,f.x), f.y);
}

float fbm(vec2 p, float to) {
    float v = 0.0;
    float amp = 0.5;
    float freq = 1.0;
    p += to * 0.1;
    for (int i = 0; i < ITERATIONS_FBM; i++) {
        v += amp * noise(p * freq);
        freq *= 2.0;
        amp *= 0.5;
    }
    return v;
}

// Main Render Function
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // Normalize coordinates
    vec2 uv = (2.0*fragCoord - iResolution.xy)
              / min(iResolution.x, iResolution.y);
    float time = (iTime + float(TIME_OFFSET)) * 0.2;

    float distToCenter = length(uv);
    vec3 finalColor = vec3(0.005, 0.0, 0.015);

    // Central Glowing Core
    float core = pow(
        smoothstep(0.15, 0.0, distToCenter),
        3.0
    );
    core += pow(
        smoothstep(0.05, 0.0, distToCenter),
        5.0
    ) * 0.5;
    finalColor += vec3(1.0,0.8,0.5) * core * 2.0;
    float bCore = core; // Use bCore for masking nebula layers

    // Simplified God Rays / Volumetric Shafts
    float shafts = 0.0;
    if (distToCenter > 0.01) {
        vec2 dir = normalize(uv);
        for (int i = 0; i < ITERATIONS_RAYMARCH; i++) {
            float t = float(i)/float(ITERATIONS_RAYMARCH)*0.8;
            vec2 p = uv - dir*t*(0.5+0.5*sin(time));
            vec2 qr = vec2(
                fbm(p*2.0 + vec2(1.7,8.2), time*0.5),
                fbm(p*2.0 + vec2(5.4,3.1), time*0.5 + 0.1)
            );
            float d = fbm(p*3.0 + qr*0.5, time*0.3);
            d = smoothstep(0.4,0.6,d);
            shafts += d * (1.0 - t) * 0.15;
        }
    }
    shafts = pow(shafts,2.0) * (1.0 - smoothstep(0.0,1.5,distToCenter));
    finalColor += vec3(0.8,0.6,0.3) * shafts * (0.5 + bCore*0.5);

    // Nebula Cloud Layers
    // Layer 1 (Warm Orange)
    vec2 uv1 = uv; 
    uv1 *= rotate(time*0.1);
    vec2 q1 = vec2(
        fbm(uv1 + time*0.05, time*0.02),
        fbm(uv1 + vec2(2.3,7.8) + time*0.04, time*0.02+0.05)
    );
    float f1 = pow(smoothstep(0.3,0.7, fbm(uv1 + q1*0.8, time*0.1)), 1.5);
    finalColor += mix(vec3(0.8,0.2,0.1), vec3(1.0,0.6,0.1), f1)
                  * f1 * 0.6 * (1.0 - bCore*0.8);

    // Layer 2 (Cool Blue)
    vec2 uv2 = uv*2.5; 
    uv2 *= rotate(-time*0.25);
    vec2 q2 = vec2(
        fbm(uv2*1.2 + time*0.2, time*0.1),
        fbm(uv2*1.2 + vec2(6.1,4.5) + time*0.18, time*0.1+0.1)
    );
    float f2 = pow(smoothstep(0.4,0.65, fbm(uv2 + q2*1.2, time*0.3+0.2)), 2.0);
    finalColor += mix(vec3(0.2,0.4,0.9), vec3(0.5,0.8,1.0), f2)
                  * f2 * 0.4 * (1.0 - smoothstep(0.0,0.5,distToCenter));

    // Layer 3 (Deep Red)
    vec2 uv3 = uv*1.8; 
    uv3 *= rotate(time*0.05);
    vec2 q3 = vec2(
        fbm(uv3 + time*0.15, time*0.1),
        fbm(uv3 + vec2(3.3,4.4) + time*0.12, time*0.1+0.1)
    );
    float f3 = pow(smoothstep(0.35,0.75, fbm(uv3 + q3*0.9, time*0.4)), 1.8);
    finalColor += mix(vec3(1.0,0.2,0.1), vec3(1.0,0.4,0.4), f3)
                  * f3 * 0.35 * (1.0 - smoothstep(0.0,1.0,distToCenter));

    // Layer 4 (Soft Blue)
    vec2 uv4 = uv*3.2; 
    uv4 *= rotate(-time*0.15);
    vec2 q4 = vec2(
        fbm(uv4 + time*0.25, time*0.15),
        fbm(uv4 + vec2(7.7,2.2) + time*0.22, time*0.15+0.15)
    );
    float f4 = pow(smoothstep(0.45,0.6, fbm(uv4 + q4*1.1, time*0.5)), 2.2);
    finalColor += mix(vec3(0.1,0.1,1.0), vec3(0.5,0.5,1.0), f4)
                  * f4 * 0.25 * (1.0 - smoothstep(0.0,0.7,distToCenter));

    // Layer 5 (Black Smoke)
    vec2 uv5 = uv*3.5; 
    uv5 *= rotate(-time*0.2 + 0.7);
    vec2 q5 = vec2(
        fbm(uv5 + time*0.3, time*0.15),
        fbm(uv5 + vec2(4.2,5.9) + time*0.33, time*0.15+0.15)
    );
    float f5 = pow(smoothstep(0.25,0.65, fbm(uv5 + q5*1.0, time*0.7)), 1.4);
    finalColor += mix(vec3(0.0), vec3(0.1), f5)
                  * f5 * 0.6 * (1.0 - smoothstep(0.0,1.3,distToCenter));

    // Add the two additional large stars
    // Star 1
    float dist1 = length(uv - EXTRA_STAR_1_POS);
    float bloom1 = pow(smoothstep(EXTRA_STAR_1_RADIUS * 0.7, 0.0, dist1), 3.0);
    bloom1 += pow(smoothstep(EXTRA_STAR_1_RADIUS * 0.4, 0.0, dist1), 5.0) * 0.5;
    finalColor += EXTRA_STAR_1_COLOR * bloom1 * EXTRA_STAR_1_BRIGHTNESS;

    // Star 2
    float dist2 = length(uv - EXTRA_STAR_2_POS);
    float bloom2 = pow(smoothstep(EXTRA_STAR_2_RADIUS * 0.7, 0.0, dist2), 3.0);
    bloom2 += pow(smoothstep(EXTRA_STAR_2_RADIUS * 0.4, 0.0, dist2), 5.0) * 0.5;
    finalColor += EXTRA_STAR_2_COLOR * bloom2 * EXTRA_STAR_2_BRIGHTNESS;

    // Final Gamma & Clamping
    finalColor = pow(finalColor, vec3(0.9));
    finalColor = clamp(finalColor, 0.0, 1.0);

    fragColor = vec4(finalColor, 1.0);
}
