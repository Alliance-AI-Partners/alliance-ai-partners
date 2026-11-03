// Scene renderer for the Alliance AI Partners brand kit. build.py lays everything out and writes a scene JSON;
// this script turns it into a native Illustrator document. build.py prepends `var SCENE_PATH = "...";`.
//
// Scene: {out, swatches: [{group, colors: [{name, hex, spotCMYK?: [c, m, y, k]}]}],
//         gradients: [{name, stops: [{pos, swatch, tint}]}],
//         components: {key: svgPath}, artboards: [{name, rect: [x, y, w, h], bg: swatch|null, group?, items: [...]}],
//         exports: [{type: "png"|"svg", folder, scale, artboards: "1-4,7", transparent, prefix}], keepBackground: bool,
//         patterns: [{name: "AAP Pattern X", tile: tile artboard name, item: name of the tile's art}]}
// Canvas coordinates are points with y down; document y is the negative.
// Items: {type: "svg", component, x, y, scale, recolor?: swatch, name}   x, y = where the SVG's (0, 0) lands
//        {type: "text", runs: [{text, swatch}], font, size, tracking, x, baseline, align, name}
//        {type: "rect", x, y, w, h, r?, fill?, pattern?, stroke?, strokeWidth?, dash?, name}   pattern: a pattern swatch name
//        {type: "line", x1, y1, x2, y2, stroke, strokeWidth, cap?, dash?, name}
//        {type: "ellipse", x, y, w, h, fill?, stroke?, strokeWidth?, name}
//        {type: "pathtext", text, font, size, tracking, swatch, cx, cy, r, startAngle, name}  (type on a circle)

function readText(p) { var f = new File(p); f.encoding = "UTF-8"; f.open("r"); var s = f.read(); f.close(); return s; }
function writeText(p, s) { var f = new File(p); f.encoding = "UTF-8"; f.open("w"); f.write(s); f.close(); }
var S = eval("(" + readText(SCENE_PATH) + ")");

function rgb(hex) {
    var c = new RGBColor();
    c.red = parseInt(hex.substr(1, 2), 16); c.green = parseInt(hex.substr(3, 2), 16); c.blue = parseInt(hex.substr(5, 2), 16);
    return c;
}
function hexOf(c) {
    function h(v) { var s = Math.round(v).toString(16).toUpperCase(); return s.length < 2 ? "0" + s : s; }
    return "#" + h(c.red) + h(c.green) + h(c.blue);
}

var unbound = {};
var prevLevel = app.userInteractionLevel;
app.userInteractionLevel = UserInteractionLevel.DONTDISPLAYALERTS;

// A rebuild saves over the previous file, so close that file if it is still open.
for (var o = app.documents.length - 1; o >= 0; o--) {
    try { if (app.documents[o].fullName.fsName === new File(S.out).fsName) app.documents[o].close(SaveOptions.DONOTSAVECHANGES); } catch (e) {}
}

var ab0 = S.artboards[0].rect;
var doc = app.documents.add(DocumentColorSpace.RGB, ab0[2], ab0[3]);
// A half-built document left open by a failed run makes later runs' swatch references unreliable, so any failure
// closes this document before it is reported.
var RESULT;
try {

// ---------------------------------------------------------------- swatches
// A brand master carries brand swatches only: drop the new-document defaults (colors, gradients, patterns).
for (var d0 = doc.swatches.length - 1; d0 >= 0; d0--) {
    var nm = doc.swatches[d0].name;
    if (nm !== "[None]" && nm !== "[Registration]") try { doc.swatches[d0].remove(); } catch (e) {}
}
for (var d1 = doc.gradients.length - 1; d1 >= 0; d1--) try { doc.gradients[d1].remove(); } catch (e) {}
for (var d3 = doc.swatchGroups.length - 1; d3 >= 0; d3--)  // the now-empty default groups (Grays, Web Color Group)
    try { if (doc.swatchGroups[d3].name !== "" && doc.swatchGroups[d3].getAllSwatches().length === 0) doc.swatchGroups[d3].remove(); } catch (e) {}
for (var d2 = doc.patterns.length - 1; d2 >= 0; d2--) try { doc.patterns[d2].remove(); } catch (e) {}
var SW = {}, BYHEX = {};
// Past ~125 swatches the object doc.spots.add() returns is already stale (even reading its name fails), so the new
// spot is re-read from the collection by its default name, and every swatch is re-resolved by name once all exist.
var MADE = {"[Registration]": 1};
function newSpot() {
    doc.spots.add();
    try { return doc.spots.getByName("Spot Color"); } catch (e0) {}  // name lookup survives when index reads fail
    var seen = [];
    for (var k = doc.spots.length - 1; k >= 0; k--) {
        var nm = null;
        try { nm = doc.spots[k].name; } catch (e) { seen.push(k + ":ERR"); continue; }
        if (!MADE[nm]) return doc.spots[k];  // the one spot not created and named by this script
        if (seen.length < 8) seen.push(k + ":" + nm);
    }
    throw new Error("new spot swatch not found among " + doc.spots.length + " (" + seen.join(", ") + ")");
}
for (var g = 0; g < S.swatches.length; g++) {
    var grp = doc.swatchGroups.add();
    grp.name = S.swatches[g].group;
    for (var i = 0; i < S.swatches[g].colors.length; i++) {
        var c = S.swatches[g].colors[i], sp = newSpot();
        sp.name = c.name;
        MADE[c.name] = 1;
        if (c.spotCMYK) {  // a real spot ink (e.g. the CutContour die line), defined in CMYK for every RIP
            var cm = new CMYKColor();
            cm.cyan = c.spotCMYK[0]; cm.magenta = c.spotCMYK[1]; cm.yellow = c.spotCMYK[2]; cm.black = c.spotCMYK[3];
            sp.colorType = ColorModel.SPOT; sp.spotKind = SpotColorKind.SPOTCMYK; sp.color = cm;
        } else { sp.colorType = ColorModel.PROCESS; sp.color = rgb(c.hex); }
        grp.addSwatch(doc.swatches.getByName(c.name));
    }
}
for (var g2 = 0; g2 < S.swatches.length; g2++) {
    for (var i2 = 0; i2 < S.swatches[g2].colors.length; i2++) {
        var c2 = S.swatches[g2].colors[i2];
        SW[c2.name] = doc.spots.getByName(c2.name);
        if (!c2.spotCMYK && !BYHEX[c2.hex.toUpperCase()]) BYHEX[c2.hex.toUpperCase()] = SW[c2.name];
    }
}
function spot(name, tint) {
    if (!SW[name]) throw new Error("unknown swatch " + name);
    var c = new SpotColor(); c.spot = SW[name]; c.tint = tint === undefined ? 100 : tint; return c;
}
for (var gi = 0; gi < (S.gradients || []).length; gi++) {
    var gd = S.gradients[gi], gr = doc.gradients.add();
    gr.name = gd.name; gr.type = GradientType.LINEAR;
    while (gr.gradientStops.length < gd.stops.length) gr.gradientStops.add();
    for (var k = 0; k < gd.stops.length; k++) {
        gr.gradientStops[k].rampPoint = gd.stops[k].pos;
        gr.gradientStops[k].color = spot(gd.stops[k].swatch, gd.stops[k].tint);
    }
}

function bindColor(c) {
    if (c.typename === "RGBColor") {
        var s = BYHEX[hexOf(c)];
        if (s) { var sc = new SpotColor(); sc.spot = s; sc.tint = 100; return sc; }
        unbound[hexOf(c)] = 1;
    }
    return null;
}
function bindPath(p) {
    if (p.filled) {
        var f = p.fillColor;
        if (f.typename === "RGBColor") { var b = bindColor(f); if (b) p.fillColor = b; }
        else if (f.typename === "GradientColor") {
            var st = f.gradient.gradientStops;
            for (var k = 0; k < st.length; k++) { var bb = bindColor(st[k].color); if (bb) st[k].color = bb; }
        }
    }
    if (p.stroked && p.strokeColor.typename === "RGBColor") { var b2 = bindColor(p.strokeColor); if (b2) p.strokeColor = b2; }
}
function eachPath(item, fn) {
    if (item.typename === "GroupItem") { for (var i = 0; i < item.pageItems.length; i++) eachPath(item.pageItems[i], fn); }
    else if (item.typename === "CompoundPathItem") { for (var j = 0; j < item.pathItems.length; j++) fn(item.pathItems[j]); }
    else if (item.typename === "PathItem") fn(item);
}

// ---------------------------------------------------------------- layers
var artLayer = doc.layers[0];
artLayer.name = "Logo";
var bgLayer = doc.layers.add();
bgLayer.name = "Background";
bgLayer.zOrder(ZOrderMethod.SENDTOBACK);
var libLayer = doc.layers.add();
libLayer.name = "_library";
var NAMED = {};
function layerNamed(n) {  // production layers such as the CutContour die line, above the art
    if (!NAMED[n]) { NAMED[n] = doc.layers.add(); NAMED[n].name = n; NAMED[n].zOrder(ZOrderMethod.BRINGTOFRONT); }
    return NAMED[n];
}

// ---------------------------------------------------------------- components: import once, bind colors, duplicate per use
var LIB = {};
function component(key) {
    if (LIB[key]) return LIB[key];
    var path = S.components[key];
    if (!path) throw new Error("unknown component " + key);
    var gr = libLayer.groupItems.createFromFile(new File(path));
    gr.name = key;
    eachPath(gr, bindPath);
    LIB[key] = gr;
    return gr;
}
function findRef(item) {
    for (var i = 0; i < item.pageItems.length; i++) {
        var p = item.pageItems[i];
        if (p.name === "aap-ref") return p;
        if (p.typename === "GroupItem") { var r = findRef(p); if (r) return r; }
    }
    return null;
}
function placeSVG(it) {
    // on top, like every other item type, so artwork stacks in scene order
    var d = component(it.component).duplicate(artLayer, ElementPlacement.PLACEATBEGINNING);
    var pct = it.scale * 100;
    d.resize(pct, pct, true, true, true, true, pct, Transformation.TOPLEFT);
    var ref = findRef(d);
    if (!ref) throw new Error("component " + it.component + " has no aap-ref rectangle");
    var gb = ref.geometricBounds;  // [left, top, right, bottom]
    d.translate(it.x - gb[0], -it.y - gb[1]);
    ref.remove();
    if (it.recolor) {
        var col = spot(it.recolor, it.tint);
        eachPath(d, function (p) { if (p.filled) p.fillColor = col; if (p.stroked) p.strokeColor = col; });
    }
    d.name = it.name || it.component;
    return d;
}

// ---------------------------------------------------------------- primitives
var PATTERN_FILLS = [];  // [path, pattern swatch name]: filled once the pattern swatches exist
function paint(p, it) {
    if (it.fill) { p.filled = true; p.fillColor = spot(it.fill, it.fillTint); } else p.filled = false;
    if (it.pattern) PATTERN_FILLS.push([p, it.pattern]);
    if (it.stroke) {
        p.stroked = true; p.strokeColor = spot(it.stroke, it.strokeTint); p.strokeWidth = it.strokeWidth || 1;
        if (it.dash) p.strokeDashes = it.dash;
        if (it.cap === "round") p.strokeCap = StrokeCap.ROUNDENDCAP;
        if (it.overprint) p.strokeOverprint = true;
    } else p.stroked = false;
    p.name = it.name || it.type;
    return p;
}
function addText(it) {
    var t = artLayer.textFrames.pointText([it.x, -it.baseline]);
    var s = "";
    for (var r = 0; r < it.runs.length; r++) s += it.runs[r].text;
    t.contents = s;
    var a = t.textRange.characterAttributes;
    a.textFont = app.textFonts.getByName(it.font);
    a.size = it.size;
    a.tracking = it.tracking || 0;
    a.kerningMethod = AutoKernType.AUTO;
    a.horizontalScale = 100;
    if (it.align === "center") t.textRange.paragraphAttributes.justification = Justification.CENTER;
    if (it.align === "right") t.textRange.paragraphAttributes.justification = Justification.RIGHT;
    var pos = 0;
    for (var r2 = 0; r2 < it.runs.length; r2++) {
        var col = spot(it.runs[r2].swatch, it.runs[r2].tint);
        for (var k = 0; k < it.runs[r2].text.length; k++) t.characters[pos + k].characterAttributes.fillColor = col;
        pos += it.runs[r2].text.length;
    }
    if (it.live) { t.name = it.name || s; return t; }
    var o = t.createOutline();
    o.name = it.name || s;
    return o;
}
function addPathText(it) {
    // Type on a circle. Text on pathItems.ellipse starts at 9 o'clock and runs clockwise with the glyphs outside
    // (probed); startAngle is where it should start instead, in degrees clockwise from 12 o'clock.
    var r = it.r, circle = artLayer.pathItems.ellipse(-it.cy + r, it.cx - r, 2 * r, 2 * r, false, true);
    circle.filled = false; circle.stroked = false;
    circle.rotate(-(it.startAngle + 90));  // rotate() is counter-clockwise for positive angles
    var t = artLayer.textFrames.pathText(circle);
    t.contents = it.text;
    var a = t.textRange.characterAttributes;
    a.textFont = app.textFonts.getByName(it.font);
    a.size = it.size; a.tracking = it.tracking || 0; a.fillColor = spot(it.swatch);
    if (it.align === "center") t.textRange.paragraphAttributes.justification = Justification.CENTER;
    if (it.ring) fitRing(t, it);
    if (it.live) { t.name = it.name || "path text"; return t; }
    var o = t.createOutline();
    o.name = it.name || "path text";
    if (it.ring) centreRing(o, it);
    return o;
}
// Glyph centres of path text as clockwise angles from 12 o'clock (degrees), sorted from the path start.
function ringAngles(item, it, outlineFirst) {
    var g = outlineFirst ? item.duplicate().createOutline() : item, rel = [];
    for (var i = 0; i < g.pageItems.length; i++) {
        var b = g.pageItems[i].geometricBounds;
        var ang = Math.atan2((b[0] + b[2]) / 2 - it.cx, (b[1] + b[3]) / 2 + it.cy) * 180 / Math.PI;
        var d = ((ang - it.startAngle) % 360 + 360) % 360;
        rel.push(d > 350 ? d - 360 : d);
    }
    if (outlineFirst) g.remove();
    rel.sort(function (p, q) { return p - q; });
    return rel;
}
// Close the ring: Illustrator's laid-out string must leave exactly its own word gap (bullet to first letter,
// it.ring.seam0 pt centre to centre at tracking 0, plus two tracking steps) between its last and first glyph.
// The span between glyph centres is linear in tracking, so a couple of solve-and-measure passes converge.
function fitRing(t, it) {
    var k = it.size / 1000, n = it.text.length, C = 2 * Math.PI * it.r, tr = it.tracking || 0;
    for (var pass = 0; pass < 3; pass++) {
        var rel = ringAngles(t, it, true), span = (rel[rel.length - 1] - rel[0]) * Math.PI / 180 * it.r;
        var next = (C - span - it.ring.seam0 + (n - 1) * tr * k) / ((n + 1) * k);
        if (Math.abs(next - tr) < 0.05) break;
        tr = next;
        t.textRange.characterAttributes.tracking = tr;
    }
    it.fittedTracking = tr;
}
// Turn the outlined ring so the glyphs it.ring.name [first, last] are centred on 12 o'clock.
function centreRing(o, it) {
    var rel = ringAngles(o, it, false), mid = it.startAngle + (rel[it.ring.name[0]] + rel[it.ring.name[1]]) / 2;
    var R = it.r * 1.5, guide = artLayer.pathItems.ellipse(-it.cy + R, it.cx - R, 2 * R, 2 * R);  // symmetric bounds
    guide.filled = false; guide.stroked = false;
    guide.move(o, ElementPlacement.PLACEATEND);
    o.rotate(mid, true, true, true, true, Transformation.CENTER);
    guide.remove();
}

function addItem(it) {
    var p;
    if (it.type === "svg") return placeSVG(it);
    if (it.type === "text") return addText(it);
    if (it.type === "pathtext") return addPathText(it);
    if (it.type === "rect") {
        p = it.r ? artLayer.pathItems.roundedRectangle(-it.y, it.x, it.w, it.h, it.r, it.r) : artLayer.pathItems.rectangle(-it.y, it.x, it.w, it.h);
        return paint(p, it);
    }
    if (it.type === "ellipse") return paint(artLayer.pathItems.ellipse(-it.y, it.x, it.w, it.h), it);
    if (it.type === "line") {
        p = artLayer.pathItems.add();
        p.setEntirePath([[it.x1, -it.y1], [it.x2, -it.y2]]);
        p.closed = false;
        return paint(p, it);
    }
    throw new Error("unknown item type " + it.type);
}

// ---------------------------------------------------------------- artboards
for (var a = 0; a < S.artboards.length; a++) {
    var A = S.artboards[a], R = A.rect;
    var rect = [R[0], -R[1], R[0] + R[2], -(R[1] + R[3])];
    var ab = a === 0 ? doc.artboards[0] : doc.artboards.add(rect);
    ab.artboardRect = rect;
    ab.name = A.name;
    if (A.bg) {
        var b = bgLayer.pathItems.rectangle(-R[1], R[0], R[2], R[3]);
        b.filled = true; b.fillColor = spot(A.bg); b.stroked = false; b.name = "bg " + A.name;
    }
    var grpA = null;
    for (var j = 0; j < A.items.length; j++) {
        var made = addItem(A.items[j]);
        if (A.items[j].layer) { made.move(layerNamed(A.items[j].layer), ElementPlacement.PLACEATBEGINNING); continue; }
        if (A.group) {  // one group per artboard, so a lockup moves as a unit; later items stay on top
            if (!grpA) { grpA = artLayer.groupItems.add(); grpA.name = A.name; }
            made.move(grpA, ElementPlacement.PLACEATBEGINNING);
        }
    }
}
// ---------------------------------------------------------------- pattern swatches
// Each pattern swatch is made from its tile artboard's art, already bound to the brand swatches, with Object >
// Pattern > Make: an SVG <pattern> imports as a pattern of plain colours that no swatch controls, which the CMYK
// conversion then separates with Illustrator's working profile instead of the print builds. The tile is the artboard
// square: a backmost empty rectangle sets it and a clipping group trims art over its edge, as SVG does.
function findNamed(container, nm) {
    for (var i = 0; i < container.pageItems.length; i++) {
        var p = container.pageItems[i];
        if (p.name === nm) return p;
        if (p.typename === "GroupItem") { var r = findNamed(p, nm); if (r) return r; }
    }
    return null;
}
var PAT = {};
for (var pt = 0; pt < (S.patterns || []).length; pt++) {
    var PS = S.patterns[pt], tr = doc.artboards.getByName(PS.tile).artboardRect;  // [left, top, right, bottom]
    var tileArt = findNamed(artLayer, PS.item);
    if (!tileArt) throw new Error("pattern " + PS.name + ": no tile art named " + PS.item);
    var outer = artLayer.groupItems.add(), clip = outer.groupItems.add();
    tileArt.duplicate(clip, ElementPlacement.PLACEATBEGINNING);
    var cp = clip.pathItems.rectangle(tr[1], tr[0], tr[2] - tr[0], tr[1] - tr[3]);
    cp.zOrder(ZOrderMethod.BRINGTOFRONT); clip.clipped = true;
    var tileBox = outer.pathItems.rectangle(tr[1], tr[0], tr[2] - tr[0], tr[1] - tr[3]);
    tileBox.filled = false; tileBox.stroked = false; tileBox.zOrder(ZOrderMethod.SENDTOBACK);
    var had = {}, nLayers = doc.layers.length;
    for (var q = 0; q < doc.patterns.length; q++) had[doc.patterns[q].name] = 1;
    doc.selection = null; outer.selected = true;
    app.executeMenuCommand("Adobe Make Pattern");
    app.executeMenuCommand("exitFocus");  // leaves pattern editing mode and keeps the new pattern
    if (doc.layers.length !== nLayers) throw new Error("pattern " + PS.name + ": still in pattern editing mode");
    var newPat = null;
    for (var q2 = 0; q2 < doc.patterns.length; q2++) if (!had[doc.patterns[q2].name]) newPat = doc.patterns[q2];
    if (!newPat) throw new Error("pattern " + PS.name + ": Make Pattern made nothing");
    newPat.name = PS.name; PAT[PS.name] = newPat;
    outer.remove();
}
for (var pf = 0; pf < PATTERN_FILLS.length; pf++) {  // a scripted PatternColor starts at 0 % scale: state the transform
    var pc = new PatternColor();
    pc.pattern = PAT[PATTERN_FILLS[pf][1]] || doc.patterns.getByName(PATTERN_FILLS[pf][1]);
    pc.matrix = app.getIdentityMatrix(); pc.scaleFactor = [100, 100]; pc.rotation = 0; pc.shiftDistance = 0; pc.shiftAngle = 0;
    PATTERN_FILLS[pf][0].filled = true; PATTERN_FILLS[pf][0].fillColor = pc;
}
libLayer.remove();
bgLayer.locked = true;
if (!S.keepBackground) bgLayer.printable = false;

// ---------------------------------------------------------------- save and export
doc.saveAs(new File(S.out), new IllustratorSaveOptions());
var EX = S.exports || [];
for (var e = 0; e < EX.length; e++) {
    var E = EX[e], sel = new ExportForScreensItemToExport();
    sel.artboards = E.artboards || "1-" + doc.artboards.length;
    sel.document = false;
    bgLayer.visible = !E.transparent;
    for (var hn in NAMED) NAMED[hn].visible = true;
    for (var hl = 0; hl < (E.hideLayers || []).length; hl++) if (NAMED[E.hideLayers[hl]]) NAMED[E.hideLayers[hl]].visible = false;
    if (E.type === "png") {
        var po = new ExportForScreensOptionsPNG24();
        po.scaleType = ExportForScreensScaleType.SCALEBYFACTOR; po.scaleTypeValue = E.scale || 1;
        po.transparency = true; po.antiAliasing = AntiAliasingMethod.ARTOPTIMIZED;
        doc.exportForScreens(new Folder(E.folder), ExportForScreensType.SE_PNG24, po, sel, E.prefix || "");
    } else {
        var so = new ExportForScreensOptionsWebOptimizedSVG();
        so.coordinatePrecision = 3; so.fontType = SVGFontType.OUTLINEFONT;
        so.cssProperties = SVGCSSPropertyLocation.PRESENTATIONATTRIBUTES;
        doc.exportForScreens(new Folder(E.folder), ExportForScreensType.SE_SVG, so, sel, E.prefix || "");
    }
}
bgLayer.visible = true;
for (var hn2 in NAMED) NAMED[hn2].visible = true;

var u = [], rings = [];
for (var h in unbound) u.push(h);
for (var a2 = 0; a2 < S.artboards.length; a2++)
    for (var j2 = 0; j2 < S.artboards[a2].items.length; j2++)
        if (S.artboards[a2].items[j2].fittedTracking !== undefined) rings.push(S.artboards[a2].items[j2].fittedTracking);
writeText(S.inventory, '{"artboards":' + doc.artboards.length + ',"unboundColors":["' + u.join('","') + '"],"ringTracking":[' + rings.join(",") + "]}");
doc.close(SaveOptions.DONOTSAVECHANGES);
RESULT = "built " + S.artboards.length + " artboards -> " + S.out + (u.length ? "; colors without a swatch: " + u.join(" ") : "");
} catch (err) {
    try { doc.close(SaveOptions.DONOTSAVECHANGES); } catch (e9) {}
    app.userInteractionLevel = prevLevel;
    throw new Error(err.message + " (aap_render.jsx line " + err.line + ")");
}
app.userInteractionLevel = prevLevel;
RESULT;
