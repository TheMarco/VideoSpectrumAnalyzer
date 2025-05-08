// Audio Reactive Visualizer Shader
// This shader visualizes audio data from iChannel0

// Utility function to get audio data from the texture
float getAudio(float index) {
    // Audio data is stored in the red channel of iChannel0
    // The texture is 512x1 pixels
    vec2 uv = vec2(index / 512.0, 0.5);
    return texture(iChannel0, uv).r;
}

// Function to get a smooth audio value
float getSmoothAudio(float index, float width) {
    float sum = 0.0;
    float count = 0.0;
    
    for (float i = -width; i <= width; i++) {
        float idx = index + i;
        if (idx >= 0.0 && idx < 512.0) {
            sum += getAudio(idx);
            count += 1.0;
        }
    }
    
    return sum / max(count, 1.0);
}

// Function to get audio spectrum data
float getSpectrum(float index) {
    // Map index from 0-1 to 0-512
    float idx = index * 512.0;
    
    // Get smoothed audio value
    return getSmoothAudio(idx, 2.0);
}

// Function to get bass, mid, and treble values
vec3 getAudioLevels() {
    float bass = 0.0;
    float mid = 0.0;
    float treble = 0.0;
    
    // Bass: 0-50 Hz (roughly 0-10% of spectrum)
    for (float i = 0.0; i < 51.2; i++) {
        bass += getAudio(i);
    }
    bass /= 51.2;
    
    // Mid: 50-2000 Hz (roughly 10-40% of spectrum)
    for (float i = 51.2; i < 204.8; i++) {
        mid += getAudio(i);
    }
    mid /= (204.8 - 51.2);
    
    // Treble: 2000-20000 Hz (roughly 40-100% of spectrum)
    for (float i = 204.8; i < 512.0; i++) {
        treble += getAudio(i);
    }
    treble /= (512.0 - 204.8);
    
    return vec3(bass, mid, treble);
}

// Function to draw a circular spectrum
vec3 drawCircularSpectrum(vec2 uv, float radius, float thickness, vec3 color) {
    float angle = atan(uv.y, uv.x);
    float normalizedAngle = (angle + 3.14159) / (2.0 * 3.14159); // 0 to 1
    
    // Get spectrum value at this angle
    float spectrum = getSpectrum(normalizedAngle);
    
    // Calculate distance from center
    float dist = length(uv);
    
    // Calculate inner and outer radius
    float innerRadius = radius - thickness / 2.0;
    float outerRadius = radius + thickness / 2.0 + spectrum * 0.3;
    
    // Draw the circular spectrum
    float circle = smoothstep(outerRadius + 0.01, outerRadius, dist) * 
                  smoothstep(innerRadius, innerRadius + 0.01, dist);
    
    // Add some color variation based on the spectrum
    vec3 finalColor = color * (0.5 + spectrum * 2.0);
    
    return finalColor * circle;
}

// Function to draw audio bars
vec3 drawAudioBars(vec2 uv, vec3 color) {
    // Number of bars
    const float numBars = 64.0;
    
    // Bar width and spacing
    float barWidth = 1.8 / numBars;
    float spacing = 0.2 / numBars;
    
    // Calculate which bar we're in
    float barIndex = floor((uv.x + 0.9) / (barWidth + spacing));
    
    // Check if we're within the valid range
    if (barIndex >= 0.0 && barIndex < numBars) {
        // Get the spectrum value for this bar
        float spectrum = getSpectrum(barIndex / numBars);
        
        // Calculate bar height
        float barHeight = spectrum * 1.5;
        
        // Check if we're inside the bar
        float x = mod(uv.x + 0.9, barWidth + spacing);
        if (x < barWidth && uv.y < barHeight && uv.y > 0.0) {
            // Color the bar based on height
            return color * (0.5 + spectrum);
        }
    }
    
    return vec3(0.0);
}

// Function to create a pulsing background
vec3 pulsingBackground(vec2 uv, vec3 color) {
    // Get audio levels
    vec3 levels = getAudioLevels();
    
    // Create a pulsing effect based on bass
    float pulse = levels.x * 0.5 + 0.5;
    
    // Create a gradient based on position
    float gradient = 1.0 - length(uv) * 0.5;
    
    // Combine pulse and gradient
    return color * pulse * gradient;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {
    // Normalize coordinates
    vec2 uv = (fragCoord - 0.5 * iResolution.xy) / min(iResolution.x, iResolution.y);
    
    // Initialize color
    vec3 color = vec3(0.0);
    
    // Add pulsing background
    color += pulsingBackground(uv, vec3(0.1, 0.05, 0.2));
    
    // Add circular spectrum
    color += drawCircularSpectrum(uv, 0.5, 0.02, vec3(0.8, 0.3, 1.0));
    color += drawCircularSpectrum(uv, 0.7, 0.01, vec3(0.3, 0.8, 1.0));
    
    // Add audio bars at the bottom
    if (uv.y < 0.0) {
        color += drawAudioBars(uv, vec3(0.2, 0.8, 0.5));
    }
    
    // Add some time-based animation
    color += vec3(0.05) * sin(iTime + uv.x * 10.0) * sin(iTime + uv.y * 10.0);
    
    // Output final color
    fragColor = vec4(color, 1.0);
}
