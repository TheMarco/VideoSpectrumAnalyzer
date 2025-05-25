// starDust - shadertoy intro
// Created by Dmitry Andreev - and'2014
// License Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License.

#define SPEED           (1.7)
#define WARMUP_TIME     (2.0)

// Audio reactivity functions
float getAudio(float index) {
    // Audio data is stored in the red channel of iChannel0
    vec2 uv = vec2(index / 512.0, 0.5);
    return texture(iChannel0, uv).r;
}

float getBassLevel() {
    float bass = 0.0;
    for(float i = 0.0; i < 10.0; i++) {
        bass += getAudio(i) * (10.0 - i) / 10.0;
    }
    return bass / 10.0;
}

float getMidLevel() {
    float mid = 0.0;
    for(float i = 10.0; i < 100.0; i++) {
        mid += getAudio(i);
    }
    return mid / 90.0;
}

float getHighLevel() {
    float high = 0.0;
    for(float i = 100.0; i < 200.0; i++) {
        high += getAudio(i);
    }
    return high / 100.0;
}

float saturate(float x)
{
    return clamp(x, 0.0, 1.0);
}

float isectPlane(vec3 n, float d, vec3 org, vec3 dir)
{
    float t = -(dot(org, n) + d) / dot(dir, n);

    return t;
}

float drawLogo(in vec2 fragCoord)
{
    float res = max(iResolution.x, iResolution.y);
    vec2  pos = vec2(floor((fragCoord.xy / res) * 128.0));

    float val = 0.0;

    // AND'14 bitmap
    if (pos.y == 2.0) val = 4873761.5;
    if (pos.y == 3.0) val = 8049199.5;
    if (pos.y == 4.0) val = 2839721.5;
    if (pos.y == 5.0) val = 1726633.5;
    if (pos.x >125.0) val = 0.0;

    float bit = floor(val * exp2(pos.x - 125.0));

    return bit != floor(bit / 2.0) * 2.0 ? 1.0 : 0.0;
}

vec3 drawEffect(vec2 coord, float time)
{
    vec3 clr = vec3(0.0);
    const float far_dist = 10000.0;

    // Get audio levels
    float bass = getBassLevel() * 5.0;
    float mid = getMidLevel() * 3.0;
    float high = getHighLevel() * 2.0;

    // Use bass for time scaling
    float timeScale = 1.0 + bass * 0.5;

    float mtime = time * 2.0 / SPEED * timeScale;
    vec2 uv = coord.xy / iResolution.xy;

    vec3 org = vec3(0.0);
    vec3 dir = vec3(uv.xy * 2.0 - 1.0, 1.0);

    // Animate tilt - use mid frequencies to control tilt
    float ang = sin(time * 0.2) * 0.2 + mid * 0.3;
    vec3 odir = dir;
    dir.x = cos(ang) * odir.x + sin(ang) * odir.y;
    dir.y = sin(ang) * odir.x - cos(ang) * odir.y;

    // Animate FOV and aspect ratio - use bass for FOV
    dir.x *= 1.5 + 0.5 * sin(time * 0.125) + bass * 0.5;
    dir.y *= 1.5 + 0.5 * cos(time * 0.25 + 0.5) + bass * 0.5;

    // Animate view direction - use high frequencies for view direction
    dir.x += 0.25 * sin(time * 0.3) + high * 0.2;
    dir.y += 0.25 * sin(time * 0.7) + high * 0.2;

    // Bend it like this - use mid frequencies for bending
    dir.xy = mix(vec2(dir.x + 0.2 * cos(dir.y) - 0.1 + mid * 0.3, dir.y), dir.xy,
        smoothstep(0.0, 1.0, saturate(0.5 * abs(mtime - 50.0))));

    // Bend it like that - use bass for additional bending
    dir.xy = mix(vec2(dir.x + 0.1 * sin(4.0 * (dir.x + time)) + bass * 0.2, dir.y), dir.xy,
        smoothstep(0.0, 1.0, saturate(0.5 * abs(mtime - 58.0))));

    // Cycle between long blurry and short sharp particles - use audio levels
    vec2 param = mix(vec2(60.0, 0.8), vec2(800.0, 3.0),
        pow(0.5 + 0.5 * sin(time * 0.2) + bass * 0.5, 2.0));

    float lt = fract(mtime / 4.0) * 4.0;
    vec2 mutes = vec2(0.0);

    if (mtime >= 32.0 && mtime < 48.0)
    {
        mutes = max(vec2(0.0), 1.0 - 4.0 * abs(lt - vec2(3.25, 3.50)));
    }

    for (int k = 0; k < 2; k++)
    for (int i = 0; i < 64; i++)
    {
        // Draw only few layers during prologue
        if (mtime < 16.0 && i >= 16) break;

        vec3 pn = vec3(k > 0 ? -1.0 : 1.0, 0.0, 0.0);
        float t = isectPlane(pn, 100.0 + float(i) * 20.0, org, dir);

        if (t <= 0.0 || t >= far_dist) continue;

        vec3 p = org + dir * t;
        vec3 vdir = normalize(-p);

        // Create particle lanes by quantizing position
        vec3 pp = ceil(p / 100.0) * 100.0;

        // Pseudo-random variables
        float n = pp.y + float(i) + float(k) * 123.0;
        float q = fract(sin(n * 123.456) * 234.345);
        float q2= fract(sin(n * 234.123) * 345.234);

        q = sin(p.z * 0.0003 + 1.0 * time * (0.25 + 0.75 * q2) + q * 12.0);

        // Smooth particle edges out
        q = saturate(q * param.x - param.x + 1.0) * param.y;
        q *= saturate(4.0 - 8.0 * abs(-50.0 + pp.y - p.y) / 100.0);

        // Fade out based on distance
        q *= 1.0 - saturate(pow(t / far_dist, 5.0));

        // Fade out based on view angle
        float fn = 1.0 - pow(1.0 - dot(vdir, pn), 2.0);
        q *= 2.0 * smoothstep(0.0, 1.0, fn);

        // Flash fade left or right plane
        q *= 1.0 - 0.9 * (k == 0 ? mutes.x : mutes.y);

        // Cycle palettes - use mid frequencies for color mixing
        const vec3 orange = vec3(1.0, 0.7, 0.4);
        const vec3 blue   = vec3(0.4, 0.7, 1.0);
        const vec3 purple = vec3(0.8, 0.4, 1.0);

        // Use mid frequencies to blend between three colors
        float colorMix = 0.5 + 0.5 * sin(time * 0.5 + q2) + mid * 0.5;
        vec3 color1 = mix(orange, blue, fract(colorMix));
        vec3 color2 = mix(blue, purple, fract(colorMix));
        clr += q * mix(color1, color2, fract(colorMix * 2.0));

        // Flash some particles in sync with bass level
        float population = 0.97 - bass * 0.2; // More bass = more particles flash

        if (q2 > population)
        {
            // Use bass level to control flash intensity
            float flashIntensity = 8.0 * (1.0 + bass * 2.0);

            clr += q * flashIntensity * max(0.0, bass);
        }
    }

    clr *= 0.2;

    // Cycle gammas
    clr.r = pow(clr.r, 0.75 + 0.35 * sin(time * 0.5));
    clr.b = pow(clr.b, 0.75 - 0.35 * sin(time * 0.5));

    // Initial fade-in
    clr *= pow(min(mtime / 4.0, 1.0), 2.0);

    // Fade-out shortly after initial fade-in right before drums kick in
    if (mtime < 8.0) clr *= 1.0 - saturate((mtime - 5.0) / 3.0);

    // Flash horizon in sync with snare drum
    if (mtime >= 15.0)
    {
        float h = normalize(dir).x;
        clr *= 1.0 + 2.0 * pow(saturate(1.0 - abs(h)), 8.0)
            * max(0.0, fract(-mtime + 0.5) * 4.0 - 3.0);
    }

    // The end
    if (mtime >= 64.0) clr = vec3(0.0);

    // Initial flash
    if (mtime >= 16.0) clr += max(0.0, 1.0 - (mtime-16.0) * 1.0);

    // Final flash
    if (mtime >= 64.0) clr += max(0.0, 1.0 - (mtime-64.0) * 0.5) * vec3(0.8,0.9,1.0);

    // Desaturate prologue
    if (mtime < 16.0) clr = mix( vec3(dot(clr, vec3(0.33))), clr, min(1.0, mtime / 32.0));

    // Vignette in linear space (looks better)
    clr *= clr;
    clr *= 1.4;
    clr *= 1.0 - 1.5 * dot(uv - 0.5, uv - 0.5);
    clr = sqrt(max(vec3(0.0), clr));

    return clr;
}

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    float time = max(0.0, iTime - WARMUP_TIME);
    vec3  clr = vec3(0.0);

    clr = drawEffect(fragCoord.xy, time);
    clr = mix(clr, vec3(0.8, 0.9, 1.0), 0.3 * drawLogo(fragCoord));

    fragColor = vec4(clr, 0.0);
}
