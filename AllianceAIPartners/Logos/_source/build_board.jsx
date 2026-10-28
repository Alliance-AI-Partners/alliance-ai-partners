// Builds one Illustrator board per track. generate_logos.py prepends `var BOARD = {...};` holding:
//   items[]: {name, art (vector file), wordmark[] ({text, family, style, size, color, tracking?, hscale?}), caption}
//   lockup: true when the art already includes the wordmark (Nano Banana lockups)
//   out: .ai path to save, preview: .png overview path
var W = 900, H = 560;
var missing = [];
var FONTS = {};
for (var i = 0; i < app.textFonts.length; i++) {
    var f = app.textFonts[i];
    if (!FONTS[f.family]) FONTS[f.family] = {};
    FONTS[f.family][f.style] = f;
}

function findFont(family, style) {
    var styles = FONTS[family];
    if (!styles) { missing.push(family); return app.textFonts[0]; }
    if (styles[style]) return styles[style];
    if (styles["Regular"]) return styles["Regular"];
    for (var s in styles) return styles[s];
}

function rgb(hex) {
    var c = new RGBColor();
    c.red = parseInt(hex.substr(1, 2), 16);
    c.green = parseInt(hex.substr(3, 2), 16);
    c.blue = parseInt(hex.substr(5, 2), 16);
    return c;
}

function isWhite(c) {
    if (c.typename === "RGBColor") return c.red > 245 && c.green > 245 && c.blue > 245;
    if (c.typename === "GrayColor") return c.gray < 4;
    return false;
}

// Recraft SVGs carry a full-size white background rectangle; drop it so the mark sits on the artboard.
function dropWhiteBackground(container, w, h) {
    for (var k = container.pageItems.length - 1; k >= 0; k--) {
        var p = container.pageItems[k];
        if (p.typename === "GroupItem") { dropWhiteBackground(p, w, h); continue; }
        if (p.typename === "PathItem" && p.filled && isWhite(p.fillColor) && p.width >= w * 0.95 && p.height >= h * 0.95) p.remove();
    }
}

function fit(item, left, top, width, height) {
    var s = Math.min(width / item.width, height / item.height) * 100;
    item.resize(s, s);
    item.left = left + (width - item.width) / 2;
    item.top = top - (height - item.height) / 2;
}

function addText(layer, str, family, style, size, color, x, y) {
    var t = layer.textFrames.add();
    t.contents = str;
    var a = t.textRange.characterAttributes;
    a.textFont = findFont(family, style);
    a.size = size;
    a.fillColor = rgb(color);
    t.left = x;
    t.top = y;
    return t;
}

var previousLevel = app.userInteractionLevel;
app.userInteractionLevel = UserInteractionLevel.DONTDISPLAYALERTS;
// A rebuild saves over the previous board, so close that board if it is still open (only that one).
for (var o = app.documents.length - 1; o >= 0; o--) {
    try {
        if (app.documents[o].fullName.fsName === new File(BOARD.out).fsName) app.documents[o].close(SaveOptions.DONOTSAVECHANGES);
    } catch (e) {}  // unsaved documents have no file to compare
}
var n = BOARD.items.length;
var doc = app.documents.add(DocumentColorSpace.RGB, W, H, n, DocumentArtboardLayout.GridByRow, 60, 2);
var artLayer = doc.layers[0];
artLayer.name = "Logos";
var frames = doc.layers.add();
frames.name = "Artboard frames";
frames.zOrder(ZOrderMethod.SENDTOBACK);

for (var i = 0; i < n; i++) {
    var item = BOARD.items[i], ab = doc.artboards[i], r = ab.artboardRect;
    ab.name = item.name;
    var frame = frames.pathItems.rectangle(r[1], r[0], W, H);
    frame.filled = false;
    frame.strokeColor = rgb("#D5D7DA");
    frame.strokeWidth = 0.5;

    var art = artLayer.groupItems.createFromFile(new File(item.art));
    dropWhiteBackground(art, art.width, art.height);
    if (BOARD.lockup) {
        fit(art, r[0] + 60, r[1] - 40, W - 120, H - 110);
    } else {
        fit(art, r[0] + 50, r[1] - 70, 360, 360);
        var y = r[1] - 210;
        for (var j = 0; j < item.wordmark.length; j++) {
            var w = item.wordmark[j];
            var t = addText(artLayer, w.text, w.family, w.style, w.size, w.color, r[0] + 450, y);
            var a = t.textRange.characterAttributes;
            if (w.tracking) a.tracking = w.tracking;
            if (w.hscale) a.horizontalScale = w.hscale;
            y -= w.size * 1.6;
        }
    }
    addText(artLayer, item.caption, "DM Mono", "Regular", 8.5, "#6B6F76", r[0] + 40, r[3] + 32);
}
frames.locked = true;

doc.saveAs(new File(BOARD.out), new IllustratorSaveOptions());
var png = new ExportOptionsPNG24();
png.artBoardClipping = false;
png.horizontalScale = 50;
png.verticalScale = 50;
png.transparency = false;
doc.exportFile(new File(BOARD.preview), ExportType.PNG24, png);
app.userInteractionLevel = previousLevel;
"saved " + n + " artboards" + (missing.length ? "; fonts not found: " + missing.join(", ") : "");
