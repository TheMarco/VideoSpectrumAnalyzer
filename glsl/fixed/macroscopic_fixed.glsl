// Original shader by Yohei Nishitsuji (https://x.com/YoheiNishitsuji/status/1892846729302581296)
// Adapted for Shadertoy

// HSV to RGB color conversion
vec3 hsv(float h, float s, float v) {
    vec4 t = vec4(1.0, 2.0/3.0, 1.0/3.0, 3.0);
    vec3 p = abs(fract(vec3(h) + t.xyz) * 6.0 - vec3(t.w));
    return v * mix(vec3(t.x), clamp(p - vec3(t.x), 0.0, 1.0), s);
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // Normalized pixel coordinates
    vec2 uv = fragCoord.xy / iResolution.xy - 0.5;
    uv.x *= iResolution.x / iResolution.y;  // Aspect ratio correction
    
    // Time variable
    float t = iTime * 0.1;
    
    // Initialize color
    vec4 finalColor = vec4(0.0, 0.0, 0.0, 1.0);
    
    // Ray marching setup
    vec3 rayOrigin = vec3(0.0, 0.0, -3.0);
    vec3 rayDir = normalize(vec3(uv, 1.0));
    
    // Ray marching parameters
    float totalDensity = 0.0;
    float colorIntensity = 0.0;
    float verticalDisplacement = 0.0;
    
    // Main ray-marching loop
    for(float i = 0.0; i < 100.0; i++) {
        // Accumulate density along the ray
        float stepSize = 0.1 + i * 0.01;
        totalDensity += i * 0.001;
        
        // Current position along the ray
        vec3 pos = rayOrigin + rayDir * stepSize * i;
        
        // Add some movement
        pos.x += sin(t) * 0.5;
        pos.y += cos(t) * 0.3;
        
        // Calculate radius
        float radius = length(pos);
        
        // Transform space
        vec3 transformedPos = vec3(
            log(radius + 0.1) - t,
            exp2(mod(-pos.z, 5.0) / (radius + 0.1)) - 0.15,
            pos.z
        );
        
        // Accumulate vertical displacement
        verticalDisplacement += transformedPos.y * 0.2;
        
        // Generate noise pattern
        float noise = 0.0;
        for(float scale = 5.0; scale < 100.0; scale *= 2.0) {
            noise += -abs(dot(
                sin(transformedPos.xzx * scale),
                cos(transformedPos.yzz * scale)
            )) / (scale * 0.8);
        }
        
        // Color based on position and noise
        vec3 color = hsv(
            verticalDisplacement * 0.1 + 0.59,  // Hue
            radius * 0.2 + verticalDisplacement * 0.3,  // Saturation
            totalDensity * i * 0.01  // Value
        );
        
        // Amplify colors
        color *= 0.05;
        
        // Add to final color
        finalColor.rgb += color;
    }
    
    // Tone mapping and gamma correction
    finalColor.rgb = pow(finalColor.rgb / (1.0 + finalColor.rgb), vec3(0.4545));
    
    // Output final color
    fragColor = finalColor;
}
