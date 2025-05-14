/*
[C]
Disco Teq
by diatribes
https://www.shadertoy.com/view/w32XDc
[/C]
*/

// Include the common functions from discoteq-common.txt
//	Classic Perlin 3D Noise
//	by Stefan Gustavson
//
vec4 permute(vec4 x){return mod(((x*34.0)+1.0)*x, 289.0);}
vec4 taylorInvSqrt(vec4 r){return 1.79284291400159 - 0.85373472095314 * r;}
vec3 fade(vec3 t) {return t*t*t*(t*(t*6.0-15.0)+10.0);}

float cnoise(vec3 P){
  vec3 Pi0 = floor(P); // Integer part for indexing
  vec3 Pi1 = Pi0 + vec3(1.0); // Integer part + 1
  Pi0 = mod(Pi0, 289.0);
  Pi1 = mod(Pi1, 289.0);
  vec3 Pf0 = fract(P); // Fractional part for interpolation
  vec3 Pf1 = Pf0 - vec3(1.0); // Fractional part - 1.0
  vec4 ix = vec4(Pi0.x, Pi1.x, Pi0.x, Pi1.x);
  vec4 iy = vec4(Pi0.yy, Pi1.yy);
  vec4 iz0 = Pi0.zzzz;
  vec4 iz1 = Pi1.zzzz;

  vec4 ixy = permute(permute(ix) + iy);
  vec4 ixy0 = permute(ixy + iz0);
  vec4 ixy1 = permute(ixy + iz1);

  vec4 gx0 = ixy0 / 7.0;
  vec4 gy0 = fract(floor(gx0) / 7.0) - 0.5;
  gx0 = fract(gx0);
  vec4 gz0 = vec4(0.5) - abs(gx0) - abs(gy0);
  vec4 sz0 = step(gz0, vec4(0.0));
  gx0 -= sz0 * (step(0.0, gx0) - 0.5);
  gy0 -= sz0 * (step(0.0, gy0) - 0.5);

  vec4 gx1 = ixy1 / 7.0;
  vec4 gy1 = fract(floor(gx1) / 7.0) - 0.5;
  gx1 = fract(gx1);
  vec4 gz1 = vec4(0.5) - abs(gx1) - abs(gy1);
  vec4 sz1 = step(gz1, vec4(0.0));
  gx1 -= sz1 * (step(0.0, gx1) - 0.5);
  gy1 -= sz1 * (step(0.0, gy1) - 0.5);

  vec3 g000 = vec3(gx0.x,gy0.x,gz0.x);
  vec3 g100 = vec3(gx0.y,gy0.y,gz0.y);
  vec3 g010 = vec3(gx0.z,gy0.z,gz0.z);
  vec3 g110 = vec3(gx0.w,gy0.w,gz0.w);
  vec3 g001 = vec3(gx1.x,gy1.x,gz1.x);
  vec3 g101 = vec3(gx1.y,gy1.y,gz1.y);
  vec3 g011 = vec3(gx1.z,gy1.z,gz1.z);
  vec3 g111 = vec3(gx1.w,gy1.w,gz1.w);

  vec4 norm0 = taylorInvSqrt(vec4(dot(g000, g000), dot(g010, g010), dot(g100, g100), dot(g110, g110)));
  g000 *= norm0.x;
  g010 *= norm0.y;
  g100 *= norm0.z;
  g110 *= norm0.w;
  vec4 norm1 = taylorInvSqrt(vec4(dot(g001, g001), dot(g011, g011), dot(g101, g101), dot(g111, g111)));
  g001 *= norm1.x;
  g011 *= norm1.y;
  g101 *= norm1.z;
  g111 *= norm1.w;

  float n000 = dot(g000, Pf0);
  float n100 = dot(g100, vec3(Pf1.x, Pf0.yz));
  float n010 = dot(g010, vec3(Pf0.x, Pf1.y, Pf0.z));
  float n110 = dot(g110, vec3(Pf1.xy, Pf0.z));
  float n001 = dot(g001, vec3(Pf0.xy, Pf1.z));
  float n101 = dot(g101, vec3(Pf1.x, Pf0.y, Pf1.z));
  float n011 = dot(g011, vec3(Pf0.x, Pf1.yz));
  float n111 = dot(g111, Pf1);

  vec3 fade_xyz = fade(Pf0);
  vec4 n_z = mix(vec4(n000, n100, n010, n110), vec4(n001, n101, n011, n111), fade_xyz.z);
  vec2 n_yz = mix(n_z.xy, n_z.zw, fade_xyz.y);
  float n_xyz = mix(n_yz.x, n_yz.y, fade_xyz.x);
  return 2.2 * n_xyz;
}

// Constants for flim color transform
const float flim_extended_gamut_red_scale = 1.0;
const float flim_extended_gamut_green_scale = 1.0;
const float flim_extended_gamut_blue_scale = 1.0;
const float flim_extended_gamut_red_rot = 0.0;
const float flim_extended_gamut_green_rot = 0.0;
const float flim_extended_gamut_blue_rot = 0.0;
const float flim_extended_gamut_red_mul = 1.0;
const float flim_extended_gamut_green_mul = 1.0;
const float flim_extended_gamut_blue_mul = 1.0;

// More accurate flim_transform function
vec3 flim_transform(vec3 col, float exposure, sampler2D iChannel) {
    // Convert to linear space if not already
    col = pow(col, vec3(2.2));

    // Apply exposure
    col *= pow(2.0, exposure);

    // Apply color grading
    float luma = dot(col, vec3(0.2126, 0.7152, 0.0722));

    // Vibrance (more subtle than saturation)
    float saturation = 1.2;
    float vibrance = 0.5;
    float satMix = clamp(min(col.r, min(col.g, col.b)) / max(col.r, max(col.g, col.b)), 0.0, 1.0);
    float satFactor = mix(0.0, vibrance, satMix) + saturation;
    col = mix(vec3(luma), col, satFactor);

    // ACES-inspired tone mapping
    const float a = 2.51;
    const float b = 0.03;
    const float c = 2.43;
    const float d = 0.59;
    const float e = 0.14;
    col = (col * (a * col + b)) / (col * (c * col + d) + e);

    // Ensure we don't have negative values
    col = max(vec3(0.0), col);

    // Back to sRGB
    col = pow(col, vec3(1.0/2.2));

    return col;
}

// Main shader code
#define S smoothstep
#define R iResolution.xy
#define T iTime

float c(vec2 u) { return S(5.0/R.y, 0.0, abs(length(u) - 0.25)); }
float t(float s) { return 0.5 + sin(T * s) * 0.5; }
mat2 r(float a) { return mat2(cos(a), sin(-a), sin(a), cos(a)); }

vec3 render(vec2 I)
{
    vec2 u = (I - 0.5 * R) / R.y * r(T * 0.3);
    vec4 O = vec4(0.0);

    // Use more iterations for better quality
    for (float i = 0.0; i < 1.0; i += 1.0/64.0) {
        // Add more variation to the noise
        float n = cnoise(vec3(u * 2.5 + i * 0.3, 0.9 * T + i * 1.2));

        // Make the circles more pronounced
        float l = c(u + n * 0.14);

        // More vibrant color cycling
        vec3 c = mix(
            vec3(t(0.4), t(0.8), t(3.0)),
            vec3(t(0.8), t(1.2), t(0.5)),
            i
        );

        // Accumulate colors with higher intensity
        O += vec4(l * c * 0.4, i);
    }

    // Ensure we have some minimum brightness
    O.rgb = max(O.rgb, vec3(0.01));

    return O.rgb;
}

void mainImage(out vec4 O, in vec2 I)
{
    // Render the main effect
    vec3 col = render(I);

    // Apply color grading with a more accurate flim_transform
    col = flim_transform(col, -0.3, iChannel0);

    // Ensure we have some minimum brightness
    col = max(col, vec3(0.01));

    // Output with full alpha
    O = vec4(col, 1.0);
}
