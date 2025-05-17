/*
    [C]
    by Shane
    https://www.shadertoy.com/view/4scXz2
    [/C]
    Biomine
    -------

    A biocooling system for a futuristic, off-world mine... or a feeding mechanisn for an alien
        hatchery? I wasn't really sure what I was creating when I started, and I'm still not. :) I at
        least wanted to create the sense that the tubes were pumping some form of biomatter around
        without having to resort to full reflective and refractive passes... I kind of got there. :)

        All things considered, there's not a lot to this. Combine a couple of gyroid surfaces, ID them,
        then add their respective material properties. The scene is simple to create, and explained in
        the distance function. There's also some function based, 2nd order cellular bump mapping, for
        anyone interested.

        The fluid pumped through the tubes was created by indexing the reflected and refracted rays
        into a basic environment mapping function. Not accurate, but simple, effective and way cheaper
        than the real thing.

        I'd just finished watching some of the Assembly 2016 entries on YouTube, so for better or
        worse, wanted to produce the scene without the help of any in-house textures.

    Related examples:

    Cellular Tiling - Shane
    https://www.shadertoy.com/view/4scXz2

        Cellular Tiled Tunnel - Shane
        https://www.shadertoy.com/view/MscSDB

*/


#define FAR 50.0 



float objID = 0.0; 
float saveID = 0.0;



float hash( float n ){ return fract(cos(n) * 45758.5453); }




mat2 rot2( float a ){ 
    vec2 v = sin(vec2(1.570796, 0.0) + a);
    return mat2(v, -v.y, v.x); 
}




float noise3D(in vec3 p){
    
    const vec3 s = vec3(7.0, 157.0, 113.0);
    vec3 ip = floor(p); 
    p -= ip; 
    vec4 h = vec4(0.0, s.yz, s.y + s.z) + dot(ip, s);
    p = p * p * (3.0 - 2.0 * p); 
    h = mix(fract(sin(h) * 43758.5453), fract(sin(h + s.x) * 43758.5453), p.x);
    h.xy = mix(h.xz, h.yw, p.y);
    return mix(h.x, h.y, p.z); 
}











float drawSphere(in vec3 p){
  
    p = fract(p) - 0.5;    
    return dot(p, p);
    
    
    
}


float cellTile(in vec3 p){
    
    
    vec4 v, d;
    d.x = drawSphere(p - vec3(0.81, 0.62, 0.53));
    p.xy = vec2(p.y - p.x, p.y + p.x) * 0.7071;
    d.y = drawSphere(p - vec3(0.39, 0.2, 0.11));
    p.yz = vec2(p.z - p.y, p.z + p.y) * 0.7071;
    d.z = drawSphere(p - vec3(0.62, 0.24, 0.06));
    p.xz = vec2(p.z - p.x, p.z + p.x) * 0.7071;
    d.w = drawSphere(p - vec3(0.2, 0.82, 0.64));

    v.xy = min(d.xz, d.yw);
    v.z = min(max(d.x, d.y), max(d.z, d.w));
    v.w = max(v.x, v.y); 
   
    d.x = min(v.z, v.w) - min(v.x, v.y); 
    
        
    return d.x * 2.66; 
    
}


vec2 path(in float z){ 
    
    float a = sin(z * 0.11);
    float b = cos(z * 0.14);
    return vec2(a * 4.0 - b * 1.5, b * 1.7 + a * 1.5); 
}



float smaxP(float a, float b, float s){
    
    float h = clamp(0.5 + 0.5 * (a - b) / s, 0.0, 1.0);
    return mix(b, a, h) + h * (1.0 - h) * s;
}







float map(vec3 p){
  
    p.xy -= path(p.z); 

    p += cos(p.zxy * 1.5707963) * 0.2; 

    
    
    float d = dot(cos(p * 1.5707963), sin(p.yzx * 1.5707963)) + 1.0;

    
    float bio = d + 0.25 + dot(sin(p * 1.0 + iTime * 6.283 + sin(p.yzx * 0.5)), vec3(0.033));

    
    
    float tun = smaxP(3.25 - length(p.xy - vec2(0.0, 1.0)) + 0.5 * cos(p.z * 3.14159 / 32.0), 0.75 - d, 1.0) - abs(1.5 - d) * 0.375;


    objID = step(tun, bio); 

    return min(tun, bio); 

 
}



float bumpSurf3D(in vec3 p){
    
    float bmp;
    float noi = noise3D(p * 96.0);
    
    if(saveID > 0.5){
        float sf = cellTile(p * 0.75); 
        float vor = cellTile(p * 1.5);
    
        bmp = sf * 0.66 + (vor * 0.94 + noi * 0.06) * 0.34;
    }
    else {
        p /= 3.0;
        float ct = cellTile(p * 2.0 + sin(p * 12.0) * 0.5) * 0.66 + cellTile(p * 6.0 + sin(p * 36.0) * 0.5) * 0.34;
        bmp = (1.0 - smoothstep(-0.2, 0.25, ct)) * 0.9 + noi * 0.1;

        
    }
    
    return bmp;

}


vec3 doBumpMap(in vec3 p, in vec3 nor, float bumpfactor){
    
    const vec2 e = vec2(0.001, 0.0);
    float ref = bumpSurf3D(p);                 
    vec3 grad = (vec3(bumpSurf3D(p - e.xyy),
                      bumpSurf3D(p - e.yxy),
                      bumpSurf3D(p - e.yyx)) - ref) / e.x;                     
          
    grad -= nor * dot(nor, grad);          
                      
    return normalize(nor + grad * bumpfactor);
    
}


float trace(in vec3 ro, in vec3 rd){

    float t = 0.0;
    float h;
    for(int i = 0; i < 72; i++){
    
        h = map(ro + rd * t);
        
        
        if(abs(h) < 0.002 * (t * 0.125 + 1.0) || t > FAR) break; 
        t += step(h, 1.0) * h * 0.2 + h * 0.5;
        
    }

    return min(t, FAR);
}


vec3 getNormal(in vec3 p) {
    const vec2 e = vec2(0.002, 0.0);
    return normalize(vec3(map(p + e.xyy) - map(p - e.xyy), 
                          map(p + e.yxy) - map(p - e.yxy),
                          map(p + e.yyx) - map(p - e.yyx)));
}






float thickness(in vec3 p, in vec3 n, float maxDist, float falloff)
{
    const float nbIte = 6.0;
    float ao = 0.0;
    
    for(float i = 1.0; i < nbIte + 0.5; i++){
        
        float l = (i * 0.75 + fract(cos(i) * 45758.5453) * 0.25) / nbIte * maxDist;
        
        ao += (l + map(p - n * l)) / pow(1.0 + l, falloff);
    }
    
    return clamp(1.0 - ao / nbIte, 0.0, 1.0);
}








float calculateAO(in vec3 p, in vec3 n)
{
    float ao = 0.0;
    float l;
    const float maxDist = 4.0;
    const float nbIte = 6.0;
    
    for(float i = 1.0; i < nbIte + 0.5; i++){
    
        l = (i + hash(i)) * 0.5 / nbIte * maxDist;
        
        ao += (l - map(p + n * l)) / (1.0 + l);
    }
    
    return clamp(1.0 - ao / nbIte, 0.0, 1.0);
}











vec3 eMap(vec3 rd, vec3 sn){
    
    
    
    rd.y += iTime;
    rd /= 3.0;

    
    float ct = cellTile(rd * 2.0 + sin(rd * 12.0) * 0.5) * 0.66 + cellTile(rd * 6.0 + sin(rd * 36.0) * 0.5) * 0.34;
    vec3 texCol = (vec3(0.25, 0.2, 0.15) * (1.0 - smoothstep(-0.1, 0.3, ct)) + vec3(0.02, 0.02, 0.53) / 6.0);
    return smoothstep(0.0, 1.0, texCol);
    
}

void mainImage(out vec4 fragColor, in vec2 fragCoord){
    
    
    vec2 uv = (fragCoord - iResolution.xy * 0.5) / iResolution.y;
    
    
    vec3 camPos = vec3(0.0, 1.0, iTime * 2.0);
    vec3 lookAt = camPos + vec3(0.0, 0.0, 0.1);

 
    
    vec3 lightPos = camPos + vec3(0.0, 0.5, 5.0);

    
    
    
    lookAt.xy += path(lookAt.z);
    camPos.xy += path(camPos.z);
    lightPos.xy += path(lightPos.z);

    
    float FOV = 3.14159265 / 2.0; 
    vec3 forward = normalize(lookAt - camPos);
    vec3 right = normalize(vec3(forward.z, 0.0, -forward.x));
    vec3 up = cross(forward, right);

    
    vec3 rd = normalize(forward + FOV * uv.x * right + FOV * uv.y * up);
    
    
    
    
    
    
    
    rd.xy = rot2(path(lookAt.z).x / 16.0) * rd.xy;
        
    
    
    float t = trace(camPos, rd);
    
    
    
    saveID = objID; 
    
    
    vec3 sceneCol = vec3(0.0);
    
    
    if(t < FAR){
    
       
        
        vec3 sp = t * rd + camPos;
        vec3 sn = getNormal(sp);       

        
        
        
        if(saveID > 0.5) sn = doBumpMap(sp, sn, 0.2);
        else sn = doBumpMap(sp, sn, 0.008);
        
        
        float ao = calculateAO(sp, sn);
        
        
        vec3 ld = lightPos - sp;

        
        float distlpsp = max(length(ld), 0.001);
        
        
        ld /= distlpsp;
        
        
        float atten = 1.0 / (1.0 + distlpsp * 0.25); 
        
        
        float ambience = 0.5;
        
        
        float diff = max(dot(sn, ld), 0.0);
       
        
        float spec = pow(max(dot(reflect(-ld, sn), -rd), 0.0), 32.0);

        
        
        float fre = pow(clamp(dot(sn, rd) + 1.0, 0.0, 1.0), 1.0);
        
     

        
        vec3 texCol;        
        
        if(saveID > 0.5){ 
            
            texCol = vec3(0.3) * (noise3D(sp * 32.0) * 0.66 + noise3D(sp * 64.0) * 0.34) * (1.0 - cellTile(sp * 16.0) * 0.75);
            
            texCol *= smoothstep(-0.1, 0.5, cellTile(sp * 0.75) * 0.66 + cellTile(sp * 1.5) * 0.34) * 0.85 + 0.15; 
        }
        else { 
            
            vec3 sps = sp / 3.0;
            float ct = cellTile(sps * 2.0 + sin(sps * 12.0) * 0.5) * 0.66 + cellTile(sps * 6.0 + sin(sps * 36.0) * 0.5) * 0.34;
            texCol = vec3(0.35, 0.25, 0.2) * (1.0 - smoothstep(-0.1, 0.25, ct)) + vec3(0.1, 0.01, 0.004);
        }
        
        
        
        
        vec3 hf = normalize(ld + sn);
        float th = thickness(sp, sn, 1.0, 1.0);
        float tdiff = pow(clamp(dot(rd, -hf), 0.0, 1.0), 1.0);
        float trans = (tdiff + 0.0) * th;  
        trans = pow(trans, 4.0);        
        

        
        
        float shading = 1.0;
        
        
        
        
        
        
        
        sceneCol = texCol * (diff + ambience) + vec3(0.7, 0.9, 1.0) * spec;
        if(saveID < 0.5) sceneCol += vec3(0.7, 0.9, 1.0) * spec * spec;
        sceneCol += texCol * vec3(0.8, 0.95, 1.0) * pow(fre, 4.0) * 2.0;
        sceneCol += vec3(1.0, 0.07, 0.15) * trans * 1.5;
        
        
        
        
        vec3 ref;
        vec3 em;
        
        if(saveID < 0.5){ 
            
            
            
            ref = reflect(rd, sn);
            em = eMap(ref, sn);
            sceneCol += em * 0.5;
            ref = refract(rd, sn, 1.0 / 1.3);
            em = eMap(ref, sn);
            sceneCol += em * vec3(2.0, 0.2, 0.3) * 1.5;
        }

        
        sceneCol *= atten * shading * ao;
       
    
    }
       
    
    
    
    vec3 sky = vec3(2.0, 0.9, 0.8);
    sceneCol = mix(sky, sceneCol, 1.0 / (t * t / FAR / FAR * 8.0 + 1.0));

    
    fragColor = vec4(sqrt(clamp(sceneCol, 0.0, 1.0)), 1.0);
    
}
