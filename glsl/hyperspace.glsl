/*
[C]
by blue_max
https://www.shadertoy.com/view/wtd3zM
[/C]

// Based on theGiallo's https://www.shadertoy.com/view/MttSz2
// MIT License. Use freely; but attribution is expected.
#define TAU 6.28318
#define PI 3.141592
const float period = 1.0;
const float speed  = 2.0;
const float rotation_speed = 0.3;
const float t2 = 4.0; // Length in seconds of the effect

// This effect fades in and out of white every t2 seconds
// Remove the next def to get an infinite tunnel instead.
//#define WHITEOUT 1

// From https://www.shadertoy.com/view/4sc3z2
// and https://www.shadertoy.com/view/XsX3zB
#define MOD3 vec3(.1031,.11369,.13787)
vec3 hash33(vec3 p3)
{
	p3 = fract(p3 * MOD3);
    p3 += dot(p3, p3.yxz+19.19);
    return -1.0 + 2.0 * fract(vec3((p3.x + p3.y)*p3.z, (p3.x+p3.z)*p3.y, (p3.y+p3.z)*p3.x));
}

float simplexNoise(vec3 p)
{
    const float K1 = 0.333333333;
    const float K2 = 0.166666667;
    
    vec3 i = floor(p + (p.x + p.y + p.z) * K1);
    vec3 d0 = p - (i - (i.x + i.y + i.z) * K2);
    
    vec3 e = step(vec3(0.0), d0 - d0.yzx);
	vec3 i1 = e * (1.0 - e.zxy);
	vec3 i2 = 1.0 - e.zxy * (1.0 - e);
    
    vec3 d1 = d0 - (i1 - 1.0 * K2);
    vec3 d2 = d0 - (i2 - 2.0 * K2);
    vec3 d3 = d0 - (1.0 - 3.0 * K2);
    
    vec4 h = max(0.6 - vec4(dot(d0, d0), dot(d1, d1), dot(d2, d2), dot(d3, d3)), 0.0);
    vec4 n = h * h * h * h * vec4(dot(d0, hash33(i)), dot(d1, hash33(i + i1)), dot(d2, hash33(i + i2)), dot(d3, hash33(i + 1.0)));
    
    return dot(vec4(31.316), n);
}

float fBm3(in vec3 p)
{
    //p += vec2(sin(iTime * .7), cos(iTime * .45))*(.1) + iMouse.xy*.1/iResolution.xy;
	float f = 0.0;
	// Change starting scale to any integer value...
	float scale = 5.0;
    p = mod(p, scale);
	float amp   = 0.75;
	
	for (int i = 0; i < 5; i++)
	{
		f += simplexNoise(p * scale) * amp;
		amp *= 0.5;
		// Scale must be multiplied by an integer value...
		scale *= 2.0;
	}
	// Clamp it just in case....
	return min(f, 1.0);
}

// From: https://www.shadertoy.com/view/4dBcWy

vec3 mod289(vec3 x) {
  return x - floor(x * (1.0 / 289.0)) * 289.0;
}

vec4 mod289(vec4 x) {
  return x - floor(x * (1.0 / 289.0)) * 289.0;
}

vec4 permute(vec4 x) {
     return mod289(((x*34.0)+1.0)*x);
}

vec4 taylorInvSqrt(vec4 r)
{
  return 1.79284291400159 - 0.85373472095314 * r;
}

float snoise(vec3 v)
  { 
  const vec2  C = vec2(0.1666666666666667, 0.3333333333333333) ; // 1.0/6.0, 1.0/3.0
  const vec4  D = vec4(0.0, 0.5, 1.0, 2.0);

// First corner
  vec3 i  = floor(v + dot(v, C.yyy) );
  vec3 x0 =   v - i + dot(i, C.xxx) ;

// Other corners
  vec3 g = step(x0.yzx, x0.xyz);
  vec3 l = 1.0 - g;
  vec3 i1 = min( g.xyz, l.zxy );
  vec3 i2 = max( g.xyz, l.zxy );

  vec3 x1 = x0 - i1 + C.xxx;
  vec3 x2 = x0 - i2 + C.yyy; // 2.0*C.x = 1/3 = C.y
  vec3 x3 = x0 - D.yyy;      // -1.0+3.0*C.x = -0.5 = -D.y

// Permutations
  i = mod289(i); 
  vec4 p = permute( permute( permute( 
             i.z + vec4(0.0, i1.z, i2.z, 1.0 ))
           + i.y + vec4(0.0, i1.y, i2.y, 1.0 )) 
           + i.x + vec4(0.0, i1.x, i2.x, 1.0 ));

// Gradients: 7x7 points over a square, mapped onto an octahedron.
// The ring size 17*17 = 289 is close to a multiple of 49 (49*6 = 294)
  float n_ = 0.142857142857; // 1.0/7.0
  vec3  ns = n_ * D.wyz - D.xzx;

  vec4 j = p - 49.0 * floor(p * ns.z * ns.z);  //  mod(p,7*7)

  vec4 x_ = floor(j * ns.z);
  vec4 y_ = floor(j - 7.0 * x_ );    // mod(j,N)

  vec4 x = x_ *ns.x + ns.yyyy;
  vec4 y = y_ *ns.x + ns.yyyy;
  vec4 h = 1.0 - abs(x) - abs(y);

  vec4 b0 = vec4( x.xy, y.xy );
  vec4 b1 = vec4( x.zw, y.zw );

  //vec4 s0 = vec4(lessThan(b0,0.0))*2.0 - 1.0;
  //vec4 s1 = vec4(lessThan(b1,0.0))*2.0 - 1.0;
  vec4 s0 = floor(b0)*2.0 + 1.0;
  vec4 s1 = floor(b1)*2.0 + 1.0;
  vec4 sh = -step(h, vec4(0.0));

  vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy ;
  vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww ;

  vec3 p0 = vec3(a0.xy,h.x);
  vec3 p1 = vec3(a0.zw,h.y);
  vec3 p2 = vec3(a1.xy,h.z);
  vec3 p3 = vec3(a1.zw,h.w);

//Normalise gradients
  vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2, p2), dot(p3,p3)));
  p0 *= norm.x;
  p1 *= norm.y;
  p2 *= norm.z;
  p3 *= norm.w;

// Mix final noise value
  vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
  m = m * m;
  return 42.0 * dot( m*m, vec4( dot(p0,x0), dot(p1,x1), 
                                dot(p2,x2), dot(p3,x3) ) );
  }

// Original code ends here.


float getnoise(int octaves, float persistence, float freq, vec3 coords) {

    float amp= 1.; 
    float maxamp = 0.;
    float sum = 0.;

    for (int i=0; i < octaves; ++i) {

        sum += amp * snoise(coords*freq); 
        freq *= 2.;
        maxamp += amp;
        amp *= persistence;
    }
    
    return (sum / maxamp) * .5 + .5;
}

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    float t = mod(iTime, t2);
    t = t / t2; // Normalized time
    
    vec4 col = vec4(0.0);
	vec2 q = fragCoord.xy / iResolution.xy;
	vec2 p = ( 2.0 * fragCoord.xy - iResolution.xy ) / min( iResolution.y, iResolution.x );
    vec2 mo = (2.0 * iMouse.xy - iResolution.xy) / min(iResolution.x, iResolution.y);
    p += vec2(0.0, -0.1);
    
    //float ay = TAU * mod(iTime, 8.0) / 8.0;
    //ay = 45.0 * 0.01745;
    float ay = 0.0, ax = 0.0, az = 0.0;
    if (iMouse.z > 0.0) {
        ay = 3.0 * mo.x;
        ax = 3.0 * mo.y;
    }
    mat3 mY = mat3(
         cos(ay), 0.0,  sin(ay),
         0.0,     1.0,      0.0,
        -sin(ay), 0.0,  cos(ay)
    );
    
    mat3 mX = mat3(
        1.0,      0.0,     0.0,
        0.0,  cos(ax), sin(ax),
        0.0, -sin(ax), cos(ax)
    );
    mat3 m = mX * mY;
    
    vec3 v = vec3(p, 1.0);
    v = m * v;
    float v_xy = length(v.xy);
    float z = v.z / v_xy;
    
    // The focal_depth controls how "deep" the tunnel looks. Lower values
	// provide more depth.
	float focal_depth = 0.15;
    #ifdef WHITEOUT
    focal_depth = mix(0.15, 0.015, smoothstep(0.65, 0.9, t));
    #endif
    
    vec2 polar;
    //float p_len = length(p);
    float p_len = length(v.xy);
    //polar.y = focal_depth / p_len + iTime * speed;
    polar.y = z * focal_depth + iTime * speed;
    //polar.y = z;
    float a = atan(v.y, v.x);
    //float a = atan(q.y, q.x);
    // atan returns a value in the range -PI to PI, let's normalize
    // that into the range [0..1]
    a = 0.5 + 0.5 * a / (1.0 * PI);
    a -= iTime * rotation_speed;
    float x = fract(a);
    // Remove the seam by reflecting the u coordinate around 0.5:
    if (x >= 0.5) x = 1.0 - x;
    polar.x = x;
    
    // Colorize blue
    float val = 0.45 + 0.55 * fBm3(
        vec3(vec2(2.0, 0.5) * polar, 0.15 * iTime));
    //float val = getnoise(8, 0.65, 1.0, vec3(polar, 0));
    val = clamp(val, 0.0, 1.0);
    col.rgb = vec3(0.15, 0.4, 0.9) * vec3(val);
    
    // Add white spots
    vec3 white = 0.35 * vec3(smoothstep(0.55, 1.0, val));
    col.rgb += white;
    col.rgb = clamp(col.rgb, 0.0, 1.0);
    
    float w_total = 0.0, w_out = 0.0;
    #ifdef WHITEOUT
    // Fade in and out from white every t2 seconds
    float w_in = 0.0;
    w_in = abs(1.0 - 1.0 * smoothstep(0.0, 0.25, t));
    w_out = abs(1.0 * smoothstep(0.8, 1.0, t));
    w_total = max(w_in, w_out);
    #endif
    
    
    // Add the white disk at the center
    float disk_size = max(0.025, 1.5 * w_out);
    //disk_size = 0.001;
    float disk_col = exp(-(p_len - disk_size) * 4.0);
    //col.rgb += mix(col.xyz, vec3(1,1,1), disk_col);
    col.rgb += clamp(vec3(disk_col), 0.0, 1.0);
    
    
    #ifdef WHITEOUT
    col.rgb = mix(col.rgb, vec3(1.0), w_total);
    #endif
    
    fragColor = vec4(col.rgb,1);
}

