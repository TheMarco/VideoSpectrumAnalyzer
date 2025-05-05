vec2	march(vec3 pos, vec3 dir);
vec3	camera(vec2 uv);
void	rotate(inout vec2 v, float angle);
float	sdTorus( vec3 p, vec2 t, float phase );
float	mylength(vec2 p);

#define LIGHT
//#define HOLES
//#define FUNKY

float 	t;			// time
vec3	ret_col;	// color
#ifdef LIGHT
vec3	h; 			// light amount
#endif

#define I_MAX		200.
#define E			0.0001
#define FAR			50.
#define	PI			3.14159
#define	TAU			PI*2.

void mainImage(out vec4 c_out, in vec2 f)
{
    t  = iTime*.125;
    vec3	col = vec3(0., 0., 0.);
	vec2 R = iResolution.xy,
          uv  = vec2(f-R/2.) / R.y;
	vec3	dir = camera(uv);
    vec3	pos = vec3(.0, .0, 0.0);

    pos.z = 4.5-iTime*2.;
    #ifdef LIGHT
    h = vec3(0.);
    #endif
    vec2	inter = (march(pos, dir));
    if (inter.y <= FAR)
        col.xyz = ret_col*(1.-inter.x*.0025);
    else
        col *= 0.;
    #ifdef LIGHT
    col += h*.005125;
    #endif
    c_out =  vec4(col,1.0);
}

/*
** Leon's mod polar from : https://www.shadertoy.com/view/XsByWd
*/

vec2 modA (vec2 p, float count) {
    float an = TAU/count;
    float a = atan(p.y,p.x)+an*.5;
    a = mod(a, an)-an*.5;
    return vec2(cos(a),sin(a))*length(p);
}

/*
** end mod polar
*/

float	scene(vec3 p)
{  
    float	var;
    float	mind = 1e5;
    vec3	op = p;
    #ifdef	FUNKY
    var =
        step(-1.+cos( floor( p.z*6.)/6.+iTime*1.)*3.14, mod(atan(p.x, p.y ), 6.28)-3.14 )
        *
        step(mod(atan(p.x, p.y ), 6.28)-3.14-1.5, -1.+cos( floor( p.z*3.)/1.+iTime*1.)*3.14)
        
        *
        step(
            .0
            ,
        (length(fract(vec2(op.z, min(abs(op.x), abs(op.y)))*10.)-.5)-.2)
	        )
        
        ;
    #else
    var = 
        atan(p.x, p.y)*1.+0.;
    #endif
    var = cos(var*1.+floor(p.z) +iTime*(mod(floor(p.z), 2.)-1. == 0. ? -1. : 1.) );
    float	dist_cylinder = 1e5;
    ret_col = 1.-vec3(.5-var*.5, .5, .3+var*.5);
    mind = length(p.xy)-1.+.1*var;
    #ifdef HOLES
    mind = max(mind, var*-(length(fract(vec2(op.z, min(abs(op.x), abs(op.y)))*10.)-.5)-.1) );
    #endif
    mind = max(mind, -(length(p.xy)-.9+.1*var));
    p.xy = modA(p.yx, 50.+50.*sin(p.z*.25) );
	p.z = fract(p.z*3.)-.5;
    if (var != 0.)
    {
	    dist_cylinder = length(p.zy)-.0251-.25*sin(op.z*5.5);
	    dist_cylinder = max(dist_cylinder, -p.x+.4 +clamp(var, .0, 1.) );
    }
    mind = 
        min
        (
            mind
            ,
			dist_cylinder
        );

    #ifdef LIGHT
    h += vec3(.5,.8,.5)*(var!=0.?1.:0.)*.0125/(.01+max(mind-var*.1, .0001)*max(mind-var*.1, .0001) );
    #endif
    
    return (mind);
}

vec2	march(vec3 pos, vec3 dir)
{
    vec2	dist = vec2(0.0, 0.0);
    vec3	p = vec3(0.0, 0.0, 0.0);
    vec2	s = vec2(0.0, 0.0);

	    for (float i = -1.; i < I_MAX; ++i)
	    {
	    	p = pos + dir * dist.y;
	        dist.x = scene(p);
	        dist.y += dist.x*.2; // makes artefacts disappear
	        if (dist.x < E || dist.y > FAR)
            {
                break;
            }
	        s.x++;
    }
    s.y = dist.y;
    return (s);
}

float	mylength(vec2 p)
{
	float	ret;
    
    p = p*p*p*p;
    p = p*p;
    ret = (p.x+p.y);
    ret = pow(ret, 1./8.);
    
    return ret;
}

// Utilities

void rotate(inout vec2 v, float angle)
{
	v = vec2(cos(angle)*v.x+sin(angle)*v.y,-sin(angle)*v.x+cos(angle)*v.y);
}

vec2	rot(vec2 p, vec2 ang)
{
	float	c = cos(ang.x);
    float	s = sin(ang.y);
    mat2	m = mat2(c, -s, s, c);
    
    return (p * m);
}

vec3	camera(vec2 uv)
{
    float		fov = 1.;
	vec3		forw  = vec3(0.0, 0.0, -1.0);
	vec3    	right = vec3(1.0, 0.0, 0.0);
	vec3    	up    = vec3(0.0, 1.0, 0.0);

    return (normalize((uv.x) * right + (uv.y) * up + fov * forw));
}
