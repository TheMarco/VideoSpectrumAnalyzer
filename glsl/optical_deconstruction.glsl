//scene1: https://www.shadertoy.com/view/MlfczH
//self 5: https://www.shadertoy.com/view/4tscR8
//Optical-Circuit optical circuit scene 5 deconstruction b

/*

not my code, just deconstructing it:

www.pouet.net/prod.php?which=65125
https://www.youtube.com/watch?v=ISkIB4w6v6I

The [optical circuit demo] video source code once appeared on glslsandbox.com
... with very nondesctiptic labels, 
... only using single letter names for functions and vars..

It is fractal code golf overkill in [0..6] scenes.
This is a deconstruction of scene 5. , not the whole demo.
Un-used functions (only used in other scenes) are removed;
scene-specific branches are set to 1, or removed 
... (multiplying by *0. or adding -0 iterations)
... all changes are annotated.

This may run slightly faster due to removing all schene-specific branching
Most of that modifies iteration count (between scenes, which are static per shader)
The [smart re-use of schene specific branches and modifiers] is what makes this a 4k demo.
... at a cost of running slightly slower, by summing up scene-modifiers.
*/


//#define scene 5
#define timeOffset 23.984083

//scene5 skips all the black fractal code.
//and it replaces it with +50% more iterations over the 2 main loops

const float pi=acos(-1.);//3.14
const float t1=sqrt(.5); //0.707

float A,D,E;vec3 B,C;

float mav(vec2 a){return max(a.y,a.x);}
float mav(vec3 a){return max(a.z,mav(a.xy));}
float mav(vec4 a){return max(mav(a.zw),mav(a.xy));}
#define miv(a) -mav(-a)
#define dd(a) dot(a,a)
float vsum(vec3 a){return dot(a,vec3(1));}//dot() is generally faster on a gpu than 2add()
 //return a.x+a.y+a.z;}

//spaceship distance field is the min() of many sub-distance fields
//sub of H and I
vec3 F(vec3 a, float b){float c=sin(b),d=cos(b);return mat3(d,-c,0,c,d,0,0,0,1)*a;}
//sub of T,used once
vec3 H(vec3 a){a=F(a,(floor(atan(a.y,a.x)*1.5/pi)*2.+1.)*pi/3.);
 return vec3(a.x,abs(a.y),a.z);}
//sub of T, used once, modifies a internally though
vec3 I(vec3 a){a.z-=A*1.5;float b=A*.5 + floor(a.z);
 return F(vec3(a.x,a.y+sin(b),fract(a.z)-.5),pi-cos(b));}
//
//sub of S and T
float R(vec3 a){vec3 b=abs(a);return max(b.y,dot(vec3(.87,.5, 0), b))- 1.;}
//sub of T, used twice
float S(vec3 a){return max(max(abs(length(a-vec3(0,0,5.))-5.)-.05,R(a)),a.z-2.);}
//sub of T, used twice
float Q(vec3 a){return max(abs(length(a*vec3(1,1,.3))-.325)-.025,-a.z);}
//sub of T,used twice
float P(vec3 a){vec3 b=abs(a);
 return max(mav(b),max(max(length(b.xy),length(b.yz)),length(b.zx))-.2)-1.;}
//t is most scene specific
//for scene5 it is the distance field of chasing spaceships
float T(vec3 a){
 vec3 b=I(a)*20.,c=H(b*2.+vec3(0,0,2))-vec3(1.4,0,0),d=b;
 d.y=abs(d.y);
 return min(min(min(
           min(max(R(d*4.-vec3(2,5,0))*.25,abs(d.z)-1.),S(d.yzx*vec3(1,.5,.5)*1.5 + vec3(.3,0,0))/1.5),
           max(min(.1-abs(d.x),-d.z),S(vec3(0, 0, 1) - d.xzy * vec3(1, .5, .5)))),
          min(
           min(max(P(c),-P(c * 1.2 + vec3(0,0, 1.5)) / 1.2),Q(c + vec3(0, 0, 1.5))),
           Q(vec3(abs(c.xy), c.z) - vec3(.5,.5,-1.5)))*.5)*.05,
  .15-abs(a.x));}

//sub of W and Y
vec3 V(float a,vec3 b,float c){a*=c;return 1./((1.+2.*b/a+b*b/(a*a))*c+.0001);}
//used twice in Mainimage
vec3 W(vec3 a,float b,float c,float d){
 vec3 e=(V(.01,abs(a),d)*2.+V(.05, vec3(length(a.yz),length(a.zx),length(a.xy)),d)*5.)
       *(sin(A * vec3(2.1,1.3,1.7)+b*10.0)+1.);
 return(e*7.+e.yzx*1.5+e.zxy*1.5)*max(1.-c*200./d,0.)/d*12.;}

//glowing planes:
//sub of X
vec3 Z(float t){
 return vec3(0,-sin(t*.6),t*1.6+.5)+sin(t*.01*vec3(11,23,19))*vec3(.135,.25,.25);}
//sub of Y
float X(vec3 a,float t,float b){
 float c=fract(t+b),e=t-c;
 vec3 f=Z(e)* vec3(0, 1, 1) + sin(vec3(0,23,37)*e),
 g=normalize(sin(vec3(0, 17, 23) * e))*8.,
 h=f+g+vec3(sin(e*53.)*.15,0,9),
 j=f-g+vec3(sin(e*73.)*.15,0,9),
 k=mix(h,j,c-.15),
 l=mix(h,j,c+.15);
 t=dot(a-k,l-k)/dot(l-k,l-k);
 return length((t<.0?k:t>1.?l:k+t*(l-k))-a);}
//used in main
vec4 Y(vec3 a,float b,float t){
 vec3 c=I(a)*20.,
 d=vec3(length(c + vec3(-.35,.57,2)),length(c + vec3(-.35, -.57, 2)), length(c + vec3(.7, 0, 2))),
 e=V(.2,d,b),
 f=vec3(X(a, t, 0.0), X(a, t, .3), X(a, t, .6)), g = V(.001, f, b);
 return vec4(
  vsum(e)*vec3(30, 75, 150) * (E + 1.0) + vsum(g) * vec3(1.0, .1, .2) * 5000.0,
  min(min(min(d.y, d.z), d.x) * .05, min(min(f.y, f.z), f.x)));}

//used once in MainImage
vec3 G(vec3 a, float b){a=fract(a*.2)*2.-1.;a.z=b;float c=50.;
 for(int i=0;i<6+1;++i){//scene5 adds +1 iteration here
  float d = clamp(dd(a),.05,.65);c*=d;a=abs(a)/d-1.31;a.xy*=mat2(1,1,-1,1)*t1;
 }return a*c;}
//U is very scene specific, used 5* in mainImage
float U(vec3 a){return .15-abs(a.x);}

#define resolution iResolution
void mainImage(out vec4 O, in vec2 Uuu){
 {//this looks like it used to be an initiating function
  A=iTime + timeOffset;
  vec2 glVertex=Uuu.xy/resolution.xy*2.-1.;
  vec3 a=Z(A),//a b c d are very scene specific
  b=normalize((vec3(0,-sin((A+sin(A*.2)*4.)*.5+A*.1),(A+sin(A*.2)*4.)*1.6+.5)-a)),
  c=normalize(cross(b,sin(A*.001*vec3(31,17,29))));
  float d=A*5.;
  for(int i=0;i< 20;++i){
   float t=A-float(i)*.1;
   vec4 y=Y(Z(t),25.,t);
   d+=1.*sin((y.w+t)* 5.)*y.x*.05*exp(float(i)*-.25);//scene specific
  }/**/
  vec3 e=normalize(vec3(sin(vec2(.53,.47)*d)*4.+sin(vec2(.91,1.1)* d)*2.+sin(vec2(2.3,1.7)*d),200)),
  f=normalize(cross(e, vec3(sin(d), 50, 0)));
  B=a;
  C=mat3(c,cross(c,b),b)*(f*glVertex.x*1.78+cross(f,e)*glVertex.y+e*1.4);
  D=fract(sin(vsum(C)*99.317*pi)*85.081*pi);
  E=fract(sin(A      *99.317*pi)*85.081*pi);
 }
 vec3 a=normalize(C),c=vec3(1),e=B,f=a,g=e,b=vec3(0),s=vec3(1,-1,-1)*.0005;
 vec4 l=vec4(B,1),k=vec4(0),j=k,h=j;
 int m=1;
 float t=.0,o=1.,p=1.,q=D*.01+.99,n;
 for(int i=0;i<64;++i) {//scene5 adds +32 iterations here. 
  //...i removed that. performance loss not wirth that.
  g=e+f*t;
  float d=T(g);
  if(d<(t*5.+1.)*.0001){
   vec3 u=normalize(T(g+s)*s+T(g+s.yyx)*s.yyx+T(g+s.yxy)*s.yxy+T(g+s.xxx)*s.xxx);//normal
   float r=pow(abs(1.-abs(dot(u,f))),5.)*.9+.1;
   o+=t*p;p*=5./r;
   e=g+u*.0001;f=reflect(f,u);t=.0;
   float v=dd(u);
   if(v<.9||1.1<v||v!= v)u=vec3(0);
   if(m<4){h=j;j=k;k=l;l=vec4(g,max(floor(o),1.)+clamp(r,.001,.999));++m;
   }
  }else t=min(t+d*q,100.);
 }
 if(m<4){h=j;j=k;k=l;l=vec4(g,o+t*p);++m;}
 int nn=m;for(int i=0;i<4;++i)if(nn < 4){h=j;j=k;k=l;++nn;}
 f=normalize(j.xyz-h.xyz);n=length(j.xyz-h.xyz);
 t=.0;o=1.;p=.0;e=h.xyz;
 q=D*.1+.8;//scene specific, no mod for scene5
 for(int i=0;i<64+32;++i){//scene5 adds 32 iterations here
  if(t>n){
   if(m<3)break;
   h=j;j=k;k=l;
   --m;
   e=h.xyz;
   f=normalize(j.xyz - h.xyz);
   n=length(j.xyz - h.xyz);
   t=.0;
   if(n<.0001)break;
   float r=fract(h.w);
   o = h.w-r;
   p=(floor(j.w)-o)/n;
   c*=mix(vec3(.17,.15,.12),vec3(1),r);}
  g=e+f*t;
  vec4 y=Y(g,o+p*t,A);//scene specific
  float u=U(g);
  u=min(u, y.w);//scene specific
  g-=normalize(U(g+s)*s+U(g+s.yyx)*s.yyx+U(g+s.yxy)*s.yxy+U(g+s.xxx)*s.xxx)*u;
  float v=sin(A*.05+g.z)*.5,w=u*q;//scene specific
  vec3 x=G(g,v);//scene specific
  b+=(W(x,v,u,o+p*t)+W(x,v,u,o+p*t+50.)+ y.xyz)*c*w;//scene specific
  c*=pow(.7,w);t+=w;
 }
 //O is scene specific, nno modifier for scene 5.
 O = vec4(pow(b, vec3(.45)), 1.0);
}
