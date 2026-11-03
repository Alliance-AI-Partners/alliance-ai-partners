// Audit dump of finished brand-kit documents. build.py prepends `var INV_PATH = "...";` pointing at
// {files: [".ai", ...], out: "inventory.json"}; for each document this records what a vendor or designer would
// check: colour mode, artboards, layers, every swatch with its colour model and values, patterns, gradients,
// live text, rasters / placed files, and the colours actually painted that are not global swatches.
function readText(p) { var f = new File(p); f.encoding = "UTF-8"; f.open("r"); var s = f.read(); f.close(); return s; }
var CFG = eval("(" + readText(INV_PATH) + ")");
var prevLevel = app.userInteractionLevel;
app.userInteractionLevel = UserInteractionLevel.DONTDISPLAYALERTS;

function q(s) { return '"' + String(s).replace(/\\/g, "\\\\").replace(/"/g, '\\"') + '"'; }
function colorStr(c) {
    if (!c) return q("none");
    var t = c.typename;
    if (t === "RGBColor") return q("RGB " + [c.red, c.green, c.blue].join("/"));
    if (t === "CMYKColor") return q("CMYK " + [c.cyan, c.magenta, c.yellow, c.black].join("/"));
    if (t === "LabColor") return q("Lab " + [c.l, c.a, c.b].join("/"));
    if (t === "GrayColor") return q("Gray " + c.gray);
    if (t === "SpotColor") return q("Spot " + c.spot.name + " " + c.tint);
    if (t === "GradientColor") return q("Gradient " + c.gradient.name);
    if (t === "PatternColor") return q("Pattern " + c.pattern.name);
    return q(t);
}
// doc.spots[i] goes stale in documents with many swatches, so each spot is reached through its swatch's colour (or by
// name), every field read defensively. -> {spot: true, json} for a global (spot) swatch, {spot: false, json} for any
// other kind (pattern, gradient, [None], a colour that is not global), null if it will not answer.
function readSwatch(doc, nm) {
    var sp = null;
    try {
        var c0 = doc.swatches.getByName(nm).color;
        if (c0.typename !== "SpotColor") return {spot: false, json: "{" + '"name":' + q(nm) + ',"type":' + q(c0.typename) + "}"};
        sp = c0.spot;
    } catch (e1) { try { sp = doc.spots.getByName(nm); } catch (e2) { return null; } }
    var t = "?", k = "?", cs = q("?");
    for (var pass = 0; pass < 3 && (t === "?" || cs === q("?")); pass++) {  // passes 1 and 2: fresh lookups by name
        if (pass === 1) { try { sp = doc.spots.getByName(nm); } catch (e6) {} }
        if (pass === 2) { try { sp = doc.swatches.getByName(nm).color.spot; } catch (e7) {} }
        try { t = sp.colorType; } catch (e3) {}
        try { k = sp.spotKind; } catch (e4) {}
        try { cs = colorStr(sp.color); } catch (e5) {}
    }
    return t === "?" || cs === q("?") ? null : {spot: true, json: "{" + '"name":' + q(nm) + ',"type":' + q(t) + ',"kind":' + q(k) + ',"color":' + cs + "}"};
}
var docsOut = [];
try {  // every exit, error or not, hands Illustrator back its alert level
for (var i = 0; i < CFG.files.length; i++) {
    var f = new File(CFG.files[i]), doc = app.open(f), o = [], names = [], rec = {}, todo = [], unnamedAt = [];
    try {
    o.push('"file":' + q(f.fsName), '"colorSpace":' + q(doc.documentColorSpace));
    var abs = [];
    for (var a = 0; a < doc.artboards.length; a++) abs.push("[" + q(doc.artboards[a].name) + "," + doc.artboards[a].artboardRect.join(",") + "]");
    o.push('"artboards":[' + abs.join(",") + "]");
    var lay = [];
    for (var l = 0; l < doc.layers.length; l++) {
        var L = doc.layers[l];
        lay.push("{" + '"name":' + q(L.name) + ',"printable":' + L.printable + ',"locked":' + L.locked + ',"visible":' + L.visible + ',"items":' + L.pageItems.length + "}");
    }
    o.push('"layers":[' + lay.join(",") + "]");
    for (var s = 0; s < doc.swatches.length; s++) { try { names.push(doc.swatches[s].name); } catch (e0) { unnamedAt.push(s); } }
    for (var s1 = 0; s1 < names.length; s1++) { var r1 = readSwatch(doc, names[s1]); if (r1 === null) todo.push(names[s1]); else rec[names[s1]] = r1; }
    var pats = [];
    for (var p = 0; p < doc.patterns.length; p++) pats.push(q(doc.patterns[p].name));
    o.push('"patterns":[' + pats.join(",") + "]", '"gradients":' + doc.gradients.length);
    var grp = [];
    for (var g = 0; g < doc.swatchGroups.length; g++) grp.push(q(doc.swatchGroups[g].name) + ":" + doc.swatchGroups[g].getAllSwatches().length);
    o.push('"swatchGroups":{' + grp.join(",") + "}");
    o.push('"textFrames":' + doc.textFrames.length, '"rasterItems":' + doc.rasterItems.length,
           '"placedItems":' + doc.placedItems.length, '"pathItems":' + doc.pathItems.length,
           '"compoundPathItems":' + doc.compoundPathItems.length);
    // painted colours that are not global swatches (process RGB/CMYK set directly on an object)
    var loose = {}, n = doc.pathItems.length, cap = Math.min(n, 200000);
    for (var k = 0; k < cap; k++) {
        var pi = doc.pathItems[k];
        if (pi.filled && (pi.fillColor.typename === "RGBColor" || pi.fillColor.typename === "CMYKColor")) loose[colorStr(pi.fillColor)] = 1;
        if (pi.stroked && (pi.strokeColor.typename === "RGBColor" || pi.strokeColor.typename === "CMYKColor")) loose[colorStr(pi.strokeColor)] = 1;
        if (pi.filled && pi.fillColor.typename === "GradientColor") {
            var st = pi.fillColor.gradient.gradientStops;
            for (var z = 0; z < st.length; z++) if (st[z].color.typename !== "SpotColor") loose["stop " + colorStr(st[z].color)] = 1;
        }
    }
    var ll = [];
    for (var key in loose) ll.push(key.charAt(0) === '"' ? key : q(key));
    o.push('"pathsScanned":' + cap, '"nonSwatchColors":[' + ll.join(",") + "]");
    } finally {
        doc.close(SaveOptions.DONOTSAVECHANGES);
    }
    // which swatches answer varies from one open session to the next (as in aap_print.jsx's rounds), so the document
    // is reopened for the rest (names that would not read included) until every swatch has been read or a round makes
    // no progress
    for (var round = 0; (todo.length || unnamedAt.length) && round < 6; round++) {
        var d2 = app.open(f), left = [], stillUnnamed = [], before = todo.length + unnamedAt.length;
        try {
            for (var u2 = 0; u2 < unnamedAt.length; u2++) {
                try { var nm3 = d2.swatches[unnamedAt[u2]].name; names.push(nm3); todo.push(nm3); } catch (e8) { stillUnnamed.push(unnamedAt[u2]); }
            }
            for (var t2 = 0; t2 < todo.length; t2++) { var r2 = readSwatch(d2, todo[t2]); if (r2 === null) left.push(todo[t2]); else rec[todo[t2]] = r2; }
        } finally { d2.close(SaveOptions.DONOTSAVECHANGES); }
        todo = left; unnamedAt = stillUnnamed;
        if (todo.length + unnamedAt.length === before) break;
    }
    var sw = [], other = [];
    for (var s2 = 0; s2 < names.length; s2++) {
        var got = rec[names[s2]];
        if (got) (got.spot ? sw : other).push(got.json);
        else sw.push("{" + '"name":' + q(names[s2]) + ',"type":"?","kind":"?","color":"?"}');  // never answered
    }
    o.push('"spots":[' + sw.join(",") + "]", '"otherSwatches":[' + other.join(",") + "]",
           '"unreadableSwatches":' + (todo.length + unnamedAt.length));
    docsOut.push("{" + o.join(",") + "}");
}
var outF = new File(CFG.out);
outF.encoding = "UTF-8"; outF.open("w"); outF.write("[" + docsOut.join(",\n") + "]"); outF.close();
} finally { app.userInteractionLevel = prevLevel; }
"inventory: " + docsOut.length + " documents";
