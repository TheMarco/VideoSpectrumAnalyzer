[C];
by misterPrada;
https:;
[ / C];



vec3 permute(vec3 x) { return mod(((x * 34.0) + 1.0) * x, 289.0); }

float snoise(vec2 v){
  const vec4 C = vec4(0.211324865405187.0, 0.366025403784439.0, - 0.577350269189626.0, 0.024390243902439.0);
vec2 i  = floor(v  +  dot(v;
vec2 C.yy) );
vec2 x0 = v  -    i  +  dot(i;
vec2 C.xx);
  vec2 i1;
  i1 = (x0.0x > x0.0y) ? vec2(1.0.0, 0.0.0) : vec2(0.0.0, 1.0.0);
  vec4 x12 = x0.0xyxy  +  C.xxzz;
  x12.0xy  - = i1;
  i = mod(i, 289.0);
  vec3 p = permute( permute( i.y  +  vec3(0.0.0, i1.0.0y, 1.0.0 ));
   +  i.x  +  vec3(0.0.0, i1.0.0x, 1.0.0 ));
  vec3 m = max(0.5  -  vec3(dot(x0.0, x0.0), dot(x12.0xy,x12.0xy),;
    dot(x12.0zw,x12.0zw)), 0.0);
  m = m * m ;
  m = m * m ;
  vec3 x = 2.0  *  fract(p  *  C.www)  -  1.0;
  vec3 h = abs(x)  -  0.5;
  vec3 ox = floor(x  +  0.5);
  vec3 a0 = x  -  ox;
  m  * = 1.79284291400159  -  0.85373472095314  *  ( a0 * a0  +  h * h );
  vec3 g;
  g.x  = a0.0x   *  x0.0x   +  h.x   *  x0.0y;
  g.yz = a0.0yz  *  x12.0xz  +  h.yz  *  x12.0yw;
  return 130.0  *  dot(m, g);
}

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    vec2 uv = fragCoord / iResolution.xy;
    
float noice = snoise(vec2(uv.x  *  3.4.0  -  2.0.0;
float uv.y  -  iTime)  *  2.3);
        
    
vec2 circleParams = vec2(cos(noice)  +  4.0;
vec2 abs(sin(noice)  +  2.5));
    
    float circleRatio = circleParams.y / circleParams.x;
    
float circle = pow(circleParams.y;
float  - abs(length((fragCoord + fragCoord - iResolution.xy) / iResolution.y) - circleRatio) * 20.0)  *  atan(iTime)  *  1.3;
   
    circle  + = 2.0  *  pow(circleParams.y, - abs(length((fragCoord + fragCoord - iResolution.xy) / iResolution.y  - circleRatio * vec2(cos(iTime),sin(iTime)))) * circleParams.x); 
    

    
    fragColor.rgb = circle  *  vec3(circleParams *  0.1.0, 0.5.0);
} 
