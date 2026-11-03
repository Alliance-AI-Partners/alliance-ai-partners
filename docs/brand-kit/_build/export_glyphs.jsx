// Exports Montserrat glyph outlines and Illustrator's own kerned layout of every string the originals
// use, to glyphs.json next to this script (read by kit.text_paths for type fitting in Python).
// Coordinates: size 100 pt, tracking 0, Auto (metrics) kerning, origin at x=0 on the baseline, y down.
var WEIGHTS = ["Light", "Regular", "Medium", "SemiBold", "Bold", "ExtraBold"];
var STRINGS = [
    "ALLIANCE AI PARTNERS", "ALLIANCE", "AI PARTNERS", "ALLIANCE AI", "PARTNERS", "AI",
    "Partners in AI. Partners in growth.", "ENTERPRISE AI CONSULTING",
    "BRAND GUIDELINES & STYLE BOARD", "01 | LOGO VARIATIONS", "02 | COLOR PALETTE", "03 | TYPOGRAPHY",
    "04 | CLEAR SPACE", "05 | GRAPHIC ELEMENTS", "Vibrant", "Blue", "Vibrant Blue", "Bright Cyan", "Deep Navy",
    "Pure White", "Off-White", "#1B56FF", "#00D5FF", "#121B2A", "#FFFFFF", "#F4F7FB",
    "Aa Bb Cc Dd Ee Ff", "Gg Hh Ii Jj Kk Ll Mm", "Nn Oo Pp Qq Rr Ss", "Tt Uu Ww Xx Yy Zz", "0123456789",
    "HEADLINE", "(Bold)", "SUBHEADER", "(Medium)", "BODY TEXT", "(Regular)", "x",
    // badges; the seal string ends in a sentinel "A" whose position is the ring text's total advance
    "ALLIANCE AI PARTNERS • PARTNERS IN AI • PARTNERS IN GROWTH • A", "CERTIFIED", "AI PARTNER"
];

function r3(v) { return Math.round(v * 1000) / 1000; }

function contourD(pi) {
    var p = pi.pathPoints, n = p.length, s = "M" + r3(p[0].anchor[0]) + " " + r3(-p[0].anchor[1]);
    for (var k = 1; k <= n; k++) {
        if (k === n && !pi.closed) break;
        var a = p[k - 1], b = p[k % n];
        s += " C" + r3(a.rightDirection[0]) + " " + r3(-a.rightDirection[1]) + " " + r3(b.leftDirection[0]) + " "
            + r3(-b.leftDirection[1]) + " " + r3(b.anchor[0]) + " " + r3(-b.anchor[1]);
    }
    return s + (pi.closed ? " Z" : "");
}

function itemD(item) {
    if (item.typename === "PathItem") return contourD(item);
    var parts = [], kids = item.typename === "CompoundPathItem" ? item.pathItems : item.pageItems;
    for (var i = 0; i < kids.length; i++) parts.push(itemD(kids[i]));
    return parts.join(" ");
}

function outline(doc, str, font) {
    var t = doc.textFrames.pointText([0, 0]);
    t.contents = str;
    var a = t.textRange.characterAttributes;
    a.textFont = font; a.size = 100; a.tracking = 0; a.kerningMethod = AutoKernType.AUTO;
    var g = t.createOutline(), items = [];
    for (var i = 0; i < g.pageItems.length; i++) items.push(g.pageItems[i]);
    items.sort(function (p, q) { return p.geometricBounds[0] - q.geometricBounds[0]; });
    return {group: g, items: items};
}

function jsonStr(s) {
    return '"' + s.replace(/\\/g, "\\\\").replace(/"/g, '\\"') + '"';
}

var prev = app.userInteractionLevel;
app.userInteractionLevel = UserInteractionLevel.DONTDISPLAYALERTS;
var doc = app.documents.add(DocumentColorSpace.RGB, 2000, 2000);
var charset = {};
for (var s = 0; s < STRINGS.length; s++)
    for (var c = 0; c < STRINGS[s].length; c++) if (STRINGS[s].charAt(c) !== " ") charset[STRINGS[s].charAt(c)] = 1;

var warnings = [], out = ['{"family":"Montserrat","size":100,"weights":{'];
for (var w = 0; w < WEIGHTS.length; w++) {
    var font = app.textFonts.getByName("Montserrat-" + WEIGHTS[w]);
    var chars = {}, cj = [];
    for (var ch in charset) {
        var o = outline(doc, ch, font), it = o.items[0];
        chars[ch] = {left: it.geometricBounds[0], width: it.geometricBounds[2] - it.geometricBounds[0]};
        cj.push(jsonStr(ch) + ':{"d":' + jsonStr(itemD(it)) + ',"left":' + r3(chars[ch].left) + "}");
        o.group.remove();
    }
    var sj = [];
    for (var s2 = 0; s2 < STRINGS.length; s2++) {
        var str = STRINGS[s2], o2 = outline(doc, str, font), lay = [], gi = 0;
        for (var idx = 0; idx < str.length; idx++) {
            var chr = str.charAt(idx);
            if (chr === " ") continue;
            var item = o2.items[gi++];
            if (!item) { warnings.push(WEIGHTS[w] + " '" + str + "': ran out of glyphs"); break; }
            var gw = item.geometricBounds[2] - item.geometricBounds[0];
            if (Math.abs(gw - chars[chr].width) > 0.05) warnings.push(WEIGHTS[w] + " '" + str + "' char " + idx + " width mismatch");
            lay.push("[" + jsonStr(chr) + "," + idx + "," + r3(item.geometricBounds[0] - chars[chr].left) + "]");
        }
        sj.push(jsonStr(str) + ":[" + lay.join(",") + "]");
        o2.group.remove();
    }
    out.push((w ? "," : "") + jsonStr(WEIGHTS[w]) + ':{"chars":{' + cj.join(",") + '},"strings":{' + sj.join(",") + "}}");
}
out.push("}}");
doc.close(SaveOptions.DONOTSAVECHANGES);
app.userInteractionLevel = prev;

var f = new File(File($.fileName).parent.fsName + "/glyphs.json");
f.encoding = "UTF-8";
f.open("w");
f.write(out.join(""));
f.close();
"glyphs.json written; warnings: " + (warnings.length ? warnings.join("; ") : "none");
