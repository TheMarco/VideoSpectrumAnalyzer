


#define FAR 1000.0
#define PI 3.14159265
#define FOV 70.0
#define FOG 0.8
#define MAX_ITERATIONS 150


float hash12(vec2 p) {
    p = fract(p * vec2(123.4, 456.7));
    p += dot(p, p + 89.1);
    return fract(p.x * p.y);
}


float noise3D(in vec3 p) {
    vec3 i = floor(p);
    vec3 f = fract(p);
    vec3 u = f * f * (3.0 - 2.0 * f);

    vec2 ii = i.xy + i.z * vec2(5.0);
    float a = hash12(ii + vec2(0.0, 0.0));
    float b = hash12(ii + vec2(1.0, 0.0));
    float c = hash12(ii + vec2(0.0, 1.0));
    float d = hash12(ii + vec2(1.0, 1.0));
    float v1 = mix(mix(a, b, u.x), mix(c, d, u.x), u.y);

    ii += vec2(5.0);
    a = hash12(ii + vec2(0.0, 0.0));
    b = hash12(ii + vec2(1.0, 0.0));
    c = hash12(ii + vec2(0.0, 1.0));
    d = hash12(ii + vec2(1.0, 1.0));
    float v2 = mix(mix(a, b, u.x), mix(c, d, u.x), u.y);

    return mix(v1, v2, u.z);
}


float fbm(vec3 x) {
    float r = 0.0;
    float w = 1.0;
    float s = 1.0;

    for (int i = 0; i < 5; i++) {
        w *= 0.5;
        s *= 2.0;
        r += w * noise3D(s * x);
    }

    return r;
}


vec3 palette(float t) {

    vec3 a = vec3(0.5, 0.3, 0.2);
    vec3 b = vec3(0.4, 0.3, 0.2);
    vec3 c = vec3(1.0, 1.0, 1.0);
    vec3 d = vec3(0.3, 0.2, 0.1);

    return a + b * cos(6.28318 * (c * t + d));
}


float yCoord(float x) {

    return cos(x * -0.05) * sin(x * 0.04) * 0.1;
}


void rotate(inout vec2 p, float a) {
    p = cos(a) * p + sin(a) * vec2(p.y, -p.x);
}


struct Geometry {
    float dist;
    vec3 hit;
    int iterations;
};


float cylinderSDF(vec3 p, float r) {
    return length(p.xz) - r;
}


Geometry map(vec3 p) {

    float timeScale = 0.06;


    p.x -= yCoord(p.y * 0.04) * 1.5;
    p.z += yCoord(p.y * 0.004) * 2.0;


    float n = pow(abs(fbm(p * 0.02)) * 8.0, 1.2);
    float s = fbm(p * 0.004 + vec3(0.0, iTime * 0.5, 0.0)) * 100.0;

    Geometry obj;
    obj.dist = max(0.0, -cylinderSDF(p, s + 20.0 - n));


    p.x -= sin(p.y * 0.008) * 15.0 + cos(p.z * 0.004) * 25.0;
    obj.dist = max(obj.dist, -cylinderSDF(p, s + 30.0 + n * 2.0));

    return obj;
}


Geometry trace(vec3 ro, vec3 rd) {
    float t = 10.0;
    float omega = 1.1;
    float previousRadius = 0.0;
    float stepLength = 0.0;
    float pixelRadius = 1.0 / 1500.0;
    float candidate_error = 1.0;
    float candidate_t = 10.0;

    Geometry mp = map(ro);
    float functionSign = mp.dist < 0.0 ? -1.0 : 1.0;

    for (int i = 0; i < MAX_ITERATIONS; i++) {
        mp = map(ro + rd * t);
        mp.iterations = i;

        float signedRadius = functionSign * mp.dist;
        float radius = abs(signedRadius);
        bool sorFail = omega > 1.0 && (radius + previousRadius) < stepLength;

        if (sorFail) {
            stepLength -= omega * stepLength;
            omega = 1.0;
        } else {
            stepLength = signedRadius * omega;
        }

        previousRadius = radius;
        float error = radius / t;

        if (!sorFail && error < candidate_error) {
            candidate_t = t;
            candidate_error = error;
        }

        if (!sorFail && error < pixelRadius || t > FAR) break;

        t += stepLength * 0.5;
    }

    mp.dist = candidate_t;

    if (t > FAR || candidate_error > pixelRadius) {
        mp.dist = 1.0;
    }

    return mp;
}

void mainImage(out vec4 fragColor, in vec2 fragCoord) {

    vec2 uv = (fragCoord.xy / iResolution.xy) - 0.5;
    uv *= tan(radians(FOV) / 2.0) * 4.0;


    float timeScale = 0.9;
    float cameraTime = iTime * timeScale;



    vec3 vuv = normalize(vec3(0.0, 1.0, 0.0));
    vec3 ro = vec3(0.0, 30.0 + cameraTime * 90.0, -0.1);


    ro.x += yCoord(ro.y * 0.04) * 0.1;
    ro.z -= yCoord(ro.y * 0.004) * 0.1;


    vec3 vrp = vec3(0.0, 50.0 + cameraTime * 90.0, 2.0);


    vrp.x += yCoord(vrp.y * 0.04) * 0.1;
    vrp.z -= yCoord(vrp.y * 0.004) * 0.1;


    vec3 vpn = normalize(vrp - ro);
    vec3 u = normalize(cross(vuv, vpn));
    vec3 v = cross(vpn, u);
    vec3 vcv = (ro + vpn);
    vec3 scrCoord = (vcv + uv.x * u * iResolution.x / iResolution.y + uv.y * v);
    vec3 rd = normalize(scrCoord - ro);
    vec3 originalRo = ro;


    Geometry tr = trace(ro, rd);
    tr.hit = ro + rd * tr.dist;


    float colorPos = tr.hit.y * 0.01 + cameraTime * 0.2;
    vec3 baseColor = palette(colorPos);


    vec3 col = baseColor * fbm(tr.hit.xzy * 0.004) * 5.0;


    col.r *= fbm(tr.hit * 0.004) * 4.0;


    col.g *= fbm(tr.hit * 0.003) * 3.5;


    col.b *= fbm(tr.hit * 0.005) * 2.0;


    float depthFactor = min(0.6, float(tr.iterations) / 120.0);
    vec3 depthColor = palette(colorPos * 0.5 + 0.3);


    vec3 sceneColor = depthFactor * col + col * 0.03;
    sceneColor *= 1.0 + 0.25 * (abs(fbm(tr.hit * 0.0008 + 3.0) * 5.0) *
                 (fbm(vec3(0.0, 0.0, cameraTime * 0.02) * 2.0)) * 1.0);


    float amberAccent = smoothstep(0.75, 0.92, fbm(tr.hit * 0.003));
    sceneColor = mix(sceneColor, vec3(0.9, 0.7, 0.3), amberAccent * 0.25);


    float brownAccent = smoothstep(0.4, 0.2, fbm(tr.hit * 0.002));
    sceneColor = mix(sceneColor, vec3(0.1, 0.05, 0.02), brownAccent * 0.4);


    sceneColor = pow(sceneColor, vec3(0.85));


    vec3 steamColor = palette(colorPos * 0.5 + 0.7) * vec3(0.6, 0.4, 0.2);
    vec3 rro = originalRo;
    ro = tr.hit;
    float distC = tr.dist;
    float f = 0.0;


    for (float i = 0.0; i < 40.0; i++) {
        rro = ro - rd * distC;
        f += fbm(rro * vec3(0.04, 0.04, 0.04) * 0.3) * 0.05;
        distC -= 2.0;
        if (distC < 2.0) break;
    }


    sceneColor += steamColor * pow(abs(f * 1.1), 2.5) * 1.2;


    sceneColor += palette(colorPos * 0.2 + 1.5) * pow(abs(dot(rd, normalize(vec3(1.0, 0.5, 0.0)))), 8.0) * 0.07;


    float vignette = 1.0 - smoothstep(0.0, 2.0, length(uv));
    sceneColor *= mix(0.85, 1.0, vignette);


    fragColor = vec4(clamp(sceneColor * (1.0 - length(uv) / 2.5), 0.0, 1.0), 1.0);


    if (tr.dist < FAR) {

        fragColor = pow(abs(fragColor / tr.dist * 100.0), vec4(0.75));
        fragColor = min(fragColor, vec4(0.9, 0.9, 0.9, 1.0));
    } else {
        fragColor = vec4(0.0, 0.0, 0.0, 1.0);
    }
}
