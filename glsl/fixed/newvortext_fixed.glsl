// New Vortex shader - Fixed version
// Original by @XorDev

void mainImage(out vec4 O, vec2 I)
{
    // Clear fragcolor
    O = vec4(0.0, 0.0, 0.0, 0.0);
    
    // Resolution for scaling
    vec2 v = iResolution.xy;
    
    // Center and scale
    vec2 p = (I + I - v) / v.y;
    
    // Loop through arcs (i=radius, l=length)
    for(float i = 0.2, l = 0.0; i < 1.0; i += 0.05)
    {
        // Compute polar coordinate position
        v = vec2(mod(atan(p.y, p.x) + i + i * iTime, 6.28) - 3.14, 1.0) * length(p) - i;
        
        // Clamp to light length
        float temp = v.x + i;
        v.x -= clamp(temp, -i, i);
        
        // Calculate length
        l = length(v) + 0.003;
        
        // Pick color for each arc and shade/attenuate light
        O += (cos(i * 5.0 + vec4(0.0, 1.0, 2.0, 3.0)) + 1.0) * (1.0 + v.y / l) / l;
    }
    
    // Tanh tonemap
    O = tanh(O / 100.0);
}
