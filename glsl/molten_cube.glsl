/*
[C]
by @XorDev
https://www.shadertoy.com/view/7dsBRB
[/C]
*/
// Molten Cube shader - Fixed version
// Original by @XorDev

void mainImage(out vec4 O, vec2 C)
{
    // Clear color
    O = vec4(0.0);
    
    // Initialize variables
    vec3 R = iResolution;
    vec3 p = 4.0 / R;
    vec3 A = vec3(0.0, 0.6, 0.8);
    vec3 q = vec3(0.0);
    float s = 0.0;
    
    // Main ray marching loop
    for(float i = 1.0; i <= 300.0; i += 1.0)
    {
        // Every 3rd iteration
        if (int(i) % 3 > 1)
        {
            // Decrement q.xz (equivalent to --q.xz in original)
            q.xz = q.xz - vec2(1.0);
            
            // Calculate step distance
            s = length(q.xz) * 0.5 - 0.04;
            
            // Add color based on distance
            O += 0.9 / exp(s * vec4(1.0, 2.0, 4.0, 1.0)) / i;
            
            // Step forward
            p -= normalize(vec3(C + C, R) - R) * s;
            
            // Rotate cube (using time as rotation parameter)
            s = iTime;
            q = abs(mix(A * dot(p, A), p, cos(s)) + sin(s) * cross(p, A));
        }
        else
        {
            // Axis sorting trick for cube rendering
            q = q.x < q.y ? q.zxy : q.zyx;
        }
    }
    
    // Final color adjustment (square for brightness)
    O *= O;
}
