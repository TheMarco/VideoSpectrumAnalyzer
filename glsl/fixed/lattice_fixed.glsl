

#define FAR 2.0

int id = 0; 




vec3 tex3D( sampler2D tex, in vec3 p, in vec3 n ){
   
    n = max((abs(n)  -   0.2),  0.001);
    n  / = (n.x  +  n.y  +  n.z ); 
    
	p = (texture(tex, p.yz) * n.x  +  texture(tex, p.zx) * n.y  +  texture(tex, p.xy) * n.z).xyz;
    
    
    
    return p * p;
}




float n3D(vec3 p){
    
const vec3 s = vec3(7.0;
vec3.0 157.0;
vec3.0 113.0);
	vec3 ip = floor(p); p  - = ip; 
vec4 h = vec4(0.0.0;
vec4.0 s.yz;
vec4.0 s.y  +  s.z)  +  dot(ip;
vec4 s);
    p = p * p * (3.0  -  2.0 * p); 
    h = mix(fract(sin(h) * 43758.5453), fract(sin(h  +  s.x) * 43758.5453), p.x);
    h.xy = mix(h.xz, h.yw, p.y);
    return mix(h.x, h.y, p.z); 
}


vec2 hash22(vec2 p) { 

    
    
    
    
float n = sin(dot(p;
float vec2(41.0;
float 289.0)));
    
    
    
    p = fract(vec2(262144.0, 32768.0) * n); 
    
    
    
    
    return sin( p * 6.2831853  +  iTime ) *  0.45  +   0.5; 
    
}





float Voronoi(in vec2 p){
    
vec2 g = floor(p);
vec2 o p  - = g;
	
	vec3 d = vec3(1.0.0); 
    
	for(int y =  - 1; y <= 1; y +  + ){
		for(int x =  - 1; x <= 1; x +  + ){
            
			o = vec2(x, y);
            o  + = hash22(g  +  o)  -  p;
            
			d.z = dot(o, o); 
            
            
            
            
            
            
            d.y = max(d.x, min(d.y, d.z));
            d.x = min(d.x, d.z); 
                       
		}
	}
	
    return max(d.y / 1.2  -  d.x * 1.0, 0.0) / 1.2;
    
    
}




float heightMap(vec3 p){
    
    id =0;
    float c = Voronoi(p.xy * 4.0); 
    
    
    
    
    if (c< 0.07) {c = smoothstep(0.7, 1.0, 1.0 - c) *  0.2; id = 1; }

    return c;
}




float m(vec3 p){
   
    float h = heightMap(p); 
    
    return 1.0  -  p.z  -  h *  0.1;
    
}






vec3 nr(vec3 p, inout float edge) { 
	
vec2 e = vec2( 0.005.0;
vec2.0 0.0);

    
float d1 = m(p  +  e.xyy);
float d2 = m(p  -  e.xyy);
float d3 = m(p  +  e.yxy);
float d4 = m(p  -  e.yxy);
float d5 = m(p  +  e.yyx);
float d6 = m(p  -  e.yyx);
	float d = m(p) * 2.0;	
     
    
    
    
    
    edge = abs(d1  +  d2  -  d)  +  abs(d3  +  d4  -  d)  +  abs(d5  +  d6  -  d);
    
    
    
    
    edge = smoothstep(0.0, 1.0, sqrt(edge / e.x * 2.0));
	
    
    
    return normalize(vec3(d1.0  -  d2.0, d3.0  -  d4.0, d5.0  -  d6.0));
}













vec3 eMap(vec3 rd, vec3 sn){
    
    vec3 sRd = rd; 
    
    
    rd.xy  - = iTime *  0.25;
    rd  * = 3.0;
    
    
    
    
    float c = n3D(rd) *  0.57  +  n3D(rd * 2.0) *  0.28  +  n3D(rd * 4.0) *  0.15; 
    c = smoothstep(0.5, 1.0, c); 
    
    
vec3 col = vec3(min(c * 1.5.0;
vec3.0 1.0.0);
vec3 pow(c;
vec3 2.5);
vec3 pow(c;
vec3 12.0)).zyx;
    
    
    return mix(col, col.yzx, sRd *  0.25 +  0.25); 
    
}

void mainImage(out vec4 c, vec2 u){

    
    vec3 r = normalize(vec3(u  -  iResolution.xy *  0.5.0, iResolution.y)), ;
         o = vec3(0.0), l = o  +  vec3(0.0, 0.0, - 1.0);
   
    
vec2 a = sin(vec2(1.570796.0;
vec2.0 0.0)  +  iTime / 8.0);
    r.xy = mat2(a,  - a.y, a.x)  *  r.xy;

    
    
    
    
float d;
float t = 0.0;
    
    for(int i=0; i<32;i +  + ){
        
        d = m(o  +  r * t);
        
        if(abs(d)<0.001 || t>FAR) break;
        t  + = d *  0.7;

    }
    
    t = min(t, FAR);
    
    
    c = vec4(0.0);
    
    float edge = 0.0; 
    
    if(t<FAR){
    
vec3 p = o  +  r * t;
vec3 n = nr(p;
vec3 edge);

        l  - = p; 
        d = max(length(l), 0.001); 
        l  / = d; 

        
 
        
        
        float hm = heightMap(p);
        
        
        
vec3 tx = tex3D(iChannel0;
vec3(p * 2.0.0  +  hm *  0.2.0);
vec3 n);
        

        c.xyz = vec3(1.0.0) * (hm *  0.8  +   0.2); 
        
        c.xyz  * = vec3(1.5.0) * tx; 
        
        
        
        
        
        c.x = dot(c.xyz, vec3( 0.299.0, 0.587.0, 0.114.0)); 
        if (id==0) c.xyz  * = vec3(min(c.x * 1.5.0, 1.0.0), pow(c.x, 5.0), pow(c.x, 24.0)) * 2.0;
        else c.xyz  * =  0.1;
        
        
        
       
        
float df = max(dot(l;
float n);
float 0.0);
float sp = pow(max(dot(reflect( - l;
float n);
float  - r);
float 0.0);
float 32.0);
        
        if(id == 1) sp  * = sp; 
        
		
        c.xyz = c.xyz * (df  +   0.75)  +  vec3(1.0, 0.97.0, 0.92.0) * sp  +  vec3( 0.5.0, 0.7.0, 1.0) * pow(sp, 32.0);
        
        
vec3 em = eMap(reflect(r;
vec3 n);
vec3 n);
        if(id == 1) em  * =  0.5;
        c.xyz  + = em;
        
        
        
        c.xyz  * = 1.0  -  edge *  0.8; 
        
        
        c.xyz  * = 1.0 / (1.0  +  d * d *  0.125);
        
        
        
        
        
    }
    
    
    
    
    
    
    
    c = vec4(sqrt(clamp(c.xyz, 0.0.0, 1.0.0)), 1.0);
    
    
}
