/*
[C]
by Marco van Hylckama Vlieg
https://www.shadertoy.com/view/wX2SWc
[/C]

// Vibe Coded with AI by Marco van Hylckama Vlieg
// info@ai-created.com
//
// Cosmic Nexus
//
// Elements of "Portal" by misterPrada
// https://www.shadertoy.com/view/cdVyWG
//
// And
//
// Elements of "FBM Simplex3D" by Lallis
// https://www.shadertoy.com/view/4tSGDy

vec3 permute(vec3 x) { return mod(((x*34.0)+1.0)*x, 289.0); }

float snoise(vec2 v){
  const vec4 C = vec4(0.211324865405187, 0.366025403784439,
           -0.577350269189626, 0.024390243902439);
  vec2 i  = floor(v + dot(v, C.yy) );
  vec2 x0 = v -   i + dot(i, C.xx);
  vec2 i1;
  i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
  vec4 x12 = x0.xyxy + C.xxzz;
  x12.xy -= i1;
  i = mod(i, 289.0);
  vec3 p = permute( permute( i.y + vec3(0.0, i1.y, 1.0 ))
  + i.x + vec3(0.0, i1.x, 1.0 ));
  vec3 m = max(0.5 - vec3(dot(x0,x0), dot(x12.xy,x12.xy),
    dot(x12.zw,x12.zw)), 0.0);
  m = m*m ;
  m = m*m ;
  vec3 x = 2.0 * fract(p * C.www) - 1.0;
  vec3 h = abs(x) - 0.5;
  vec3 ox = floor(x + 0.5);
  vec3 a0 = x - ox;
  m *= 1.79284291400159 - 0.85373472095314 * ( a0*a0 + h*h );
  vec3 g;
  g.x  = a0.x  * x0.x  + h.x  * x0.y;
  g.yz = a0.yz * x12.xz + h.yz * x12.yw;
  return 130.0 * dot(m, g);
}

// Improved 3D noise function - smoother than the original
float smoothNoise3D(vec3 p) {
    vec3 i = floor(p);
    vec3 f = fract(p);
    
    // Smooth interpolation
    vec3 u = f * f * (3.0 - 2.0 * f);
    
    // Sample 8 corners of the cube
    float a = dot(sin(i + vec3(0.0, 0.0, 0.0)), vec3(12.9898, 78.233, 37.719)) * 43758.5453;
    float b = dot(sin(i + vec3(1.0, 0.0, 0.0)), vec3(12.9898, 78.233, 37.719)) * 43758.5453;
    float c = dot(sin(i + vec3(0.0, 1.0, 0.0)), vec3(12.9898, 78.233, 37.719)) * 43758.5453;
    float d = dot(sin(i + vec3(1.0, 1.0, 0.0)), vec3(12.9898, 78.233, 37.719)) * 43758.5453;
    float e = dot(sin(i + vec3(0.0, 0.0, 1.0)), vec3(12.9898, 78.233, 37.719)) * 43758.5453;
    float f1 = dot(sin(i + vec3(1.0, 0.0, 1.0)), vec3(12.9898, 78.233, 37.719)) * 43758.5453;
    float g = dot(sin(i + vec3(0.0, 1.0, 1.0)), vec3(12.9898, 78.233, 37.719)) * 43758.5453;
    float h = dot(sin(i + vec3(1.0, 1.0, 1.0)), vec3(12.9898, 78.233, 37.719)) * 43758.5453;
    
    // Trilinear interpolation
    float v1 = mix(mix(fract(a), fract(b), u.x), mix(fract(c), fract(d), u.x), u.y);
    float v2 = mix(mix(fract(e), fract(f1), u.x), mix(fract(g), fract(h), u.x), u.y);
    return mix(v1, v2, u.z) * 2.0 - 1.0;
}

// Rotation matrix
mat3 rotationMatrix(vec3 axis, float angle) {
    axis = normalize(axis);
    float s = sin(angle);
    float c = cos(angle);
    float oc = 1.0 - c;
    
    return mat3(
        oc * axis.x * axis.x + c,           oc * axis.x * axis.y - axis.z * s,  oc * axis.z * axis.x + axis.y * s,
        oc * axis.x * axis.y + axis.z * s,  oc * axis.y * axis.y + c,           oc * axis.y * axis.z - axis.x * s,
        oc * axis.z * axis.x - axis.y * s,  oc * axis.y * axis.z + axis.x * s,  oc * axis.z * axis.z + c
    );
}

// Improved fire palette with smoother gradients
vec3 firePalette(float i) {
    // Smoother transition between colors
    i = pow(i, 1.5); // Add more contrast
    float T = 1400.0 + 1300.0 * i;
    vec3 L = vec3(7.4, 5.6, 4.4);
    L = pow(L, vec3(5.0)) * (exp(1.43876719683e5/(T*L)) - 1.0);
    return 1.0 - exp(-5e8/L);
}

// Smooth step function with wider transition
float wideStep(float edge0, float edge1, float x) {
    float t = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0);
    return t * t * (3.0 - 2.0 * t);
}

// Main image function
void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    vec2 uv = fragCoord/iResolution.xy;
    vec2 p = (uv * 2.0 - 1.0) * vec2(iResolution.x/iResolution.y, 1.0);
    
    // Audio reactivity
    float audioBoost = 1.0;
    if (textureSize(iChannel0, 0).x > 0) {
        audioBoost = 1.0 + texture(iChannel0, vec2(0.1, 0.0)).x * 2.0;
    }
    
    // Time variables
    float time = iTime * 0.2; // Slower time for smoother animation
    
    // Portal effect (modified from portal.glsl)
    // Use lower frequency for smoother noise
    float noice = snoise(vec2(uv.x * 2.4 - 2.0, uv.y - time) * 1.8);
    vec2 circleParams = vec2(cos(noice) + 4.0, abs(sin(noice) + 2.5));
    float circleRatio = circleParams.y/circleParams.x;
    
    // Create the main portal effect with much smoother falloff
    float distFromCenter = length((fragCoord+fragCoord-iResolution.xy)/iResolution.y)-circleRatio*audioBoost;
    float circle = pow(circleParams.y, -abs(distFromCenter)*8.0) * 
                  (sin(time) * 0.5 + 0.5) * 1.3;
    
    // Add inner portal ring with audio reactivity and smoother transition
    float innerDist = length((fragCoord+fragCoord-iResolution.xy)/iResolution.y - 
                circleRatio*vec2(cos(time*audioBoost),sin(time*audioBoost)));
    circle += 1.5 * pow(circleParams.y, -abs(innerDist)*(circleParams.x * 0.7)); 
    
    // Smoke cloud effect (inspired by smokecloud.glsl)
    vec3 ro = vec3(0.0, 0.0, -2.0);
    vec3 rd = normalize(vec3(p, 0.0) - ro);
    
    // Rotate based on time and audio
    mat3 rot = rotationMatrix(vec3(0.0, 1.0, 0.0), time);
    mat3 rot2 = rotationMatrix(vec3(1.0, 0.0, 0.0), time * 0.5);
    ro = ro * rot * rot2;
    rd = rd * rot * rot2;
    
    // Raymarching for volumetric effect
    vec3 col = vec3(0.0);
    float z = 1.0;
    
    // More steps for smoother gradients
    for (int i = 0; i < 16; i++) {
        // Position in 3D space
        vec3 pos = ro + rd * z;
        
        // Create smoother turbulence with fewer iterations
        for (float d = 5.0; d < 30.0; d += d) {
            pos += 0.4 * sin(pos.yzx * d - 0.1 * time) / d;
        }
        
        // Calculate density with smoother noise
        float density = abs(smoothNoise3D(pos * 0.3 + time * 0.1));
        
        // Use a much wider transition for portal proximity
        float portalDist = length(pos.xy) - 1.0;
        float portalProximity = wideStep(-1.2, 1.2, abs(portalDist));
        
        // Mix fire palette with portal colors using smooth transitions
        vec3 fireColor = firePalette(density * audioBoost);
        vec3 portalColor = circle * vec3(circleParams * 0.1, 0.5);
        
        // Add color contribution with smoother falloff
        col += mix(fireColor, portalColor, portalProximity) * 0.12 * (1.0 - portalProximity * 0.5);
        
        // Larger steps for smoother result
        z += 0.15;
    }
    
    // Final color mixing with smoother transitions
    vec3 finalColor = col + circle * vec3(
        circleParams.x * 0.05 + sin(time) * 0.05, 
        circleParams.y * 0.05, 
        0.5 + cos(time) * 0.1
    ) * audioBoost;
    
    // Add subtle glow with wider radius
    float glow = length(p);
    finalColor += vec3(0.1, 0.2, 0.4) * smoothstep(1.0, 0.0, glow) * 0.2;
    
    // Softer contrast adjustment
    finalColor = pow(finalColor, vec3(1.1));
    
    // Create smoother transition to dark areas
    float luminance = dot(finalColor, vec3(0.299, 0.587, 0.114));
    float darkTransition = smoothstep(0.0, 0.3, luminance);
    finalColor *= darkTransition;
    
    // Output
    fragColor = vec4(finalColor, 1.0);
}
