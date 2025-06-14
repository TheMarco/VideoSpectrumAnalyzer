/*
[C]
By @XorDev
https://www.shadertoy.com/view/wcGSRW
[/C]
    quick mod of "Nova" by @XorDev - Modified for full visibility and centering.

    Original: https://www.shadertoy.com/view/WfGSRD

    
    Modifications:
    - Coordinate system 'p' is now centered and aspect-ratio corrected.
      The circle of radius 1 will now fit perfectly within the shorter dimension
      of the viewport, centered.
*/
void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    vec2 p = (fragCoord.xy * 2.0 - iResolution.xy) / min(iResolution.x, iResolution.y);
    float l = 0.5 - length(p);
    fragColor = tanh((1.2 + sin(atan(p.y,p.x)+iTime+vec4(0,2,4,0))) * .1 / max(l/.1,-l));
}
