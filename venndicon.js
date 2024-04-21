// Create a hash function
function simpleHash(str) {
    let hash = 0
    for (let i = 0; i < str.length; i++) {
      hash = ((hash << 5) - hash + str.charCodeAt(i)) | 0
    }
    return hash >>> 0
  }
  
// Generate a deterministic number from a hash
var generateDeterministicNumberFromHash = (str) => {
    var hashValue = simpleHash(str);
    var number = hashValue / 0xFFFFFFFF; // Convert to number between 0 and 1
    return number;
};

var generateNDeterministicNumbersFromHash = (str, n) => {
    var numbers = [];
    for (let i = 0; i < n; i++) {
        if (i == 0) {
            numbers.push(generateDeterministicNumberFromHash(str));
        }
        else {
            numbers.push(generateDeterministicNumberFromHash(numbers[i-1].toString()+str));
        }
    }
    return numbers;
}


function make_venndicon(hsh, size=100) {
    var numbers = generateNDeterministicNumbersFromHash(hsh, 43);
    console.log(numbers);

    var w, h, draw, empty1,  empty2, empty3, empty3a, empty3b,
        rect, cir1, cir2, cir3, ci12, ci13, ci23, c123

    h = size

    var cx1, cx2, cx3,
        cy1, cy2, cy3,
        cr1, cr2, cr3 

    cx1 = Math.floor((numbers[0] * 7) + 2)*h/10
    cx2 = Math.floor((numbers[1] * 7) + 2)*h/10
    cx3 = Math.floor((numbers[2] * 7) + 2)*h/10
    cy1 = Math.floor((numbers[3] * 7) + 2)*h/10
    cy2 = Math.floor((numbers[4] * 7) + 2)*h/10
    cy3 = Math.floor((numbers[5] * 7) + 2)*h/10
    cr1 = Math.floor((numbers[6] * 7) + 4)*h/10
    cr2 = Math.floor((numbers[7] * 7) + 4)*h/10
    cr3 = Math.floor((numbers[8] * 7) + 4)*h/10

    c1 =  new SVG.Color({ 
        r: Math.floor((numbers[9] * 255) + 1), 
        g: Math.floor((numbers[10] * 255) + 1), 
        b: Math.floor((numbers[11] * 255) + 1),
    }).toHex()
    c2 =  new SVG.Color({ 
        r: Math.floor((numbers[12] * 255) + 1), 
        g: Math.floor((numbers[13] * 255) + 1), 
        b: Math.floor((numbers[14] * 255) + 1),
    }).toHex()
    c3 =  new SVG.Color({ 
        r: Math.floor((numbers[15] * 255) + 1), 
        g: Math.floor((numbers[16] * 255) + 1), 
        b: Math.floor((numbers[17] * 255) + 1),
    }).toHex()
    c4 =  new SVG.Color({ 
        r: Math.floor((numbers[18] * 255) + 1), 
        g: Math.floor((numbers[19] * 255) + 1), 
        b: Math.floor((numbers[20] * 255) + 1),
    }).toHex()
    c5 =  new SVG.Color({ 
        r: Math.floor((numbers[21] * 255) + 1), 
        g: Math.floor((numbers[22] * 255) + 1), 
        b: Math.floor((numbers[23] * 255) + 1),
    }).toHex()
    c6 =  new SVG.Color({ 
        r: Math.floor((numbers[24] * 255) + 1), 
        g: Math.floor((numbers[25] * 255) + 1), 
        b: Math.floor((numbers[26] * 255) + 1),
    }).toHex()
    c7 =  new SVG.Color({ 
        r: Math.floor((numbers[27] * 255) + 1), 
        g: Math.floor((numbers[28] * 255) + 1), 
        b: Math.floor((numbers[29] * 255) + 1),
    }).toHex()
    c8 =  new SVG.Color({ 
        r: Math.floor((numbers[30] * 255) + 1), 
        g: Math.floor((numbers[31] * 255) + 1), 
        b: Math.floor((numbers[32] * 255) + 1),
    }).toHex()

    draw = new SVG(hsh).size(h, h)

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
}

function genDivs(u, v, size, salt){ 
    var e = document.body;
    var ids = [];
    for(var i = 0; i < v; i++){ 
      var row = document.createElement("div"); 
      row.className = "row"; 
      for(var x = 0; x < u; x++){ 
          var id = (i*10000).toString() + x.toString() + salt;
          ids.push(id);
          var cell = document.createElement("div"); 
          cell.id = id; 
          if (x < u-1) {
            cell.style = "float:left;"; 
          }
          row.appendChild(cell);
      } 
      e.appendChild(row); 
    } 
    for (let i = 0; i < ids.length; i++) {
        make_venndicon(ids[i], size);
    }
  }

var params = (new URL(location)).searchParams;
genDivs(parseInt(params.get('w') || '1'), parseInt(params.get('h') || '1'), parseInt(params.get('size') || '600'), params.get('salt') || (Math.random() + 1).toString(36))
