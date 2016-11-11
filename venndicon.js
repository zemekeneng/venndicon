
var w, h, draw, empty1,  empty2, empty3, empty3a, empty3b,
     rect, cir1, cir2, cir3, ci12, ci13, ci23, c123

h = 350

var cx1, cx2, cx3,
    cy1, cy2, cy3,
    cr1, cr2, cr3 

cx1 = Math.floor((Math.random() * 7) + 2)*h/10
cx2 = Math.floor((Math.random() * 7) + 2)*h/10
cx3 = Math.floor((Math.random() * 7) + 2)*h/10
cy1 = Math.floor((Math.random() * 7) + 2)*h/10
cy2 = Math.floor((Math.random() * 7) + 2)*h/10
cy3 = Math.floor((Math.random() * 7) + 2)*h/10
cr1 = Math.floor((Math.random() * 7) + 4)*h/10
cr2 = Math.floor((Math.random() * 7) + 4)*h/10
cr3 = Math.floor((Math.random() * 7) + 4)*h/10

c1 =  new SVG.Color({ 
    r: Math.floor((Math.random() * 255) + 1), 
    g: Math.floor((Math.random() * 255) + 1), 
    b: Math.floor((Math.random() * 255) + 1),
}).toHex()
c2 =  new SVG.Color({ 
    r: Math.floor((Math.random() * 255) + 1), 
    g: Math.floor((Math.random() * 255) + 1), 
    b: Math.floor((Math.random() * 255) + 1),
}).toHex()
c3 =  new SVG.Color({ 
    r: Math.floor((Math.random() * 255) + 1), 
    g: Math.floor((Math.random() * 255) + 1), 
    b: Math.floor((Math.random() * 255) + 1),
}).toHex()
c4 =  new SVG.Color({ 
    r: Math.floor((Math.random() * 255) + 1), 
    g: Math.floor((Math.random() * 255) + 1), 
    b: Math.floor((Math.random() * 255) + 1),
}).toHex()
c5 =  new SVG.Color({ 
    r: Math.floor((Math.random() * 255) + 1), 
    g: Math.floor((Math.random() * 255) + 1), 
    b: Math.floor((Math.random() * 255) + 1),
}).toHex()
c6 =  new SVG.Color({ 
    r: Math.floor((Math.random() * 255) + 1), 
    g: Math.floor((Math.random() * 255) + 1), 
    b: Math.floor((Math.random() * 255) + 1),
}).toHex()
c7 =  new SVG.Color({ 
    r: Math.floor((Math.random() * 255) + 1), 
    g: Math.floor((Math.random() * 255) + 1), 
    b: Math.floor((Math.random() * 255) + 1),
}).toHex()
c8 =  new SVG.Color({ 
    r: Math.floor((Math.random() * 255) + 1), 
    g: Math.floor((Math.random() * 255) + 1), 
    b: Math.floor((Math.random() * 255) + 1),
}).toHex()

draw = SVG('venndicon').size(h, h)

empty1 = draw.circle(cr1).cx(cx1).cy(cy1).attr({ fill: '#fff' })
empty2 = draw.circle(cr2).cx(cx2).cy(cy2).attr({ fill: '#fff' })
empty3 = draw.circle(cr3).cx(cx3).cy(cy3).attr({ fill: '#fff' })
empty3a = draw.circle(cr3).cx(cx3).cy(cy3).attr({ fill: '#fff' })
empty3b = draw.circle(cr3).cx(cx3).cy(cy3).attr({ fill: '#fff' })

rect = draw.rect(h, h).attr({ fill: c1})
cir1 = draw.circle(cr1).attr({ fill: c2 }).cx(cx1).cy(cy1)
cir2 = draw.circle(cr2).attr({ fill: c3 }).cx(cx2).cy(cy2)
cir3 = draw.circle(cr3).attr({ fill: c4 }).cx(cx3).cy(cy3)
ci12 = draw.circle(cr1).attr({ fill: c5 }).cx(cx1).cy(cy1).clipWith(empty2)
ci13 = draw.circle(cr1).attr({ fill: c6 }).cx(cx1).cy(cy1).clipWith(empty3)
ci23 = draw.circle(cr2).attr({ fill: c7 }).cx(cx2).cy(cy2).clipWith(empty3a)
c123 = draw.circle(cr2).attr({ fill: c8 }).cx(cx2).cy(cy2).clipWith(empty3b.clipWith(empty1))
