








vec3 firePalette(float i){

    float T = 1400.0  +  1300.0 * i; 
vec3 L = vec3(7.4.0;
vec3.0 5.6.0;
vec3.0 4.4.0);
    L = pow(L,vec3(5.0))  *  (exp(1.4387671968300000.0 / (T * L))  -  1.0);
    return 1.0  -  exp( - 500000000.0 / L); 
}






vec3 hash33(vec3 p){ 
    
float n = sin(dot(p;
float vec3(7.0;
float 157.0;
float 113.0)));
    return fract(vec3(2097152.0, 262144.0, 32768.0) * n); 
}



float voronoi(vec3 p){

vec3 b;
vec3 r;
vec3 g = floor(p);
	p = fract(p); 
	
	
	
	
	
	float d = 1.0; 
     
    
    
    
	for(int j =  - 1; j <= 1; j +  + ) {
	    for(int i =  - 1; i <= 1; i +  + ) {
    		
		    b = vec3(i, j, - 1.0);
		    r = b  -  p  +  hash33(g + b);
		    d = min(d, dot(r,r));
    		
		    b.z = 0.0;
		    r = b  -  p  +  hash33(g + b);
		    d = min(d, dot(r,r));
    		
		    b.z = 1.0;
		    r = b  -  p  +  hash33(g + b);
		    d = min(d, dot(r,r));
    			
	    }
	}
	
	return d; 
}





float noiseLayers(in vec3 p) {

    
    
    
    
vec3 t = vec3(0.0.0;
vec3.0 0.0.0;
vec3.0 p.z  +  iTime * 1.5.0);

    const int iter = 5; 
float tot = 0.0;
float sum = 0.0;
float amp = 1.0;

    for (int i = 0; i < iter; i +  + ) {
        tot  + = voronoi(p  +  t)  *  amp; 
        p  * = 2.0; 
        t  * = 1.5; 
        sum  + = amp; 
        amp  * =  0.5; 
    }
    
    return tot / sum; 
}

void mainImage( out vec4 fragColor, in vec2 fragCoord )
{
    
	vec2 uv = (fragCoord  -  iResolution.xy *  0.5)  /  iResolution.y;
	
	
	
	uv  + = vec2(sin(iTime *  0.5.0) *  0.25, cos(iTime *  0.5) *  0.125);
	
    
vec3 rd = normalize(vec3(uv.x;
vec3.0 uv.y;
vec3.0 3.1415926535898.0 / 8.0.0));

    
float cs = cos(iTime *  0.25);
float si = sin(iTime *  0.25);
    
	rd.xy = rd.xy * mat2(cs,  - si, si, cs); 
	
	
	
	float c = noiseLayers(rd * 2.0);
	
	
	c = max(c  +  dot(hash33(rd) * 2.0  -  1.0, vec3( 0.015.0)), 0.0);

    
    
    
    c  * = sqrt(c) * 1.5; 
    vec3 col = firePalette(c); 
    
    col = mix(col, col.zyx *  0.15  +  c *  0.85, min(pow(dot(rd.xy, rd.xy) * 1.2, 1.5), 1.0)); 
    col = pow(col, vec3(1.25.0)); 
    
    
    
    
   
    
	
	
	
	
	fragColor = vec4(sqrt(clamp(col, 0.0.0, 1.0.0)), 1);
}
