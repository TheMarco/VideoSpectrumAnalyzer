/*
    "Vortex" by @XorDev
    
    X: X.com/XorDev/status/1726103550986469869
    Twigl: twigl.app/?ol=true&ss=-Nj_xbLdHGKREF78Hd96
    
    <300 chars playlist: shadertoy.com/playlist/fXlGDN
    -10 Thanks to FabriceNeyret2

*/
void mainImage(out vec4 O, vec2 I)
{
    //Clear fragcolor
    O *= 0.;
    //Resolution for scaling
    vec2 v = iResolution.xy,
    //Center and scale
    p = (I+I-v)/v.y;
    
    //Loop through arcs (i=radius, P=pi, l=length)
    for(float i=.2,l; i<1.; 
    //Pick color for each arc
    O+=(cos(i*5.+vec4(0,1,2,3))+1.)*
    //Shade and attenuate light
    (1.+v.y/(l=length(v)+.003))/l)
        //Compute polar coordinate position
        v=vec2(mod(atan(p.y,p.x)+i+i*iTime,6.28)-3.14,1)*length(p)-i,
        //Clamp to light length
        v.x-=clamp(v.x+=i,-i,i),
        //Iterate radius
        i+=.05;
    
    //Tanh tonemap: shadertoy.com/view/ms3BD7
    O=tanh(O/1e2);
}

//[275]
/*
void mainImage(out vec4 O, vec2 I)
{
    //Clear fragcolor
    O *= 0.;
    //Resolution for scaling
    vec2 v = iResolution.xy,
    //Center and scale
    p = (I+I-v)/v.y;
    
    //Loop through arcs (i=radius, P=pi, l=length)
    for(float i=.2,P=acos(-1.),l; i<1.; 
    //Pick color for each arc
    O+=(cos(i*5.+vec4(0,1,2,3))+1.)*
    //Shade and attenuate light
    (1.+v.y/(l=length(v)+.003))/l/1e2)
        //Compute polar coordinate position
        v=vec2(mod(atan(p.y,p.x)+i+i*iTime,P+P)-P,1)*length(p)-i,
        //Clamp to light length
        v.x-=clamp(v.x+=i,-i,i),
        //Iterate radius
        i+=.05;
    
    //Tanh tonemap: shadertoy.com/view/ms3BD7
    O=tanh(O);
}
*/
