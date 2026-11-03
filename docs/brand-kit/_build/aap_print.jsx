// Print masters for the Alliance AI Partners brand kit. build.py prepends `var PRINT_PATH = "...";` pointing at
// {src, swatches: {"AAP Alliance Blue": {cmyk: [c, m, y, k], spots: {C: {name, cmyk}, U: {name, cmyk}} | null}, ...},
//  cmyk: {ai, pdf, proofPdf, epsFolder, epsPrefix, artboards: "1-40"},
//  pms: [{side: "C" | "U", ai, epsFolder, epsPrefix}]}
// Every logo colour is a global swatch, so converting the document and then setting each swatch's build recolours
// every object, gradient stop and tint that uses it. Spot inks are defined in CMYK with explicit alternates (the
// process build a RIP uses if it converts the spot), computed for the master's printing condition; the document
// itself cannot be tagged by script, so build.py writes the PDF/X-4 output intent and checks it afterwards.

function readText(p) { var f = new File(p); f.encoding = "UTF-8"; f.open("r"); var s = f.read(); f.close(); return s; }
var P = eval("(" + readText(PRINT_PATH) + ")");
var prevLevel = app.userInteractionLevel;
app.userInteractionLevel = UserInteractionLevel.DONTDISPLAYALERTS;
var report = [];

function closeIfOpen(path) {
    for (var o = app.documents.length - 1; o >= 0; o--) {
        try { if (app.documents[o].fullName.fsName === new File(path).fsName) app.documents[o].close(SaveOptions.DONOTSAVECHANGES); } catch (e) {}
    }
}
function cmyk(v) { var c = new CMYKColor(); c.cyan = v[0]; c.magenta = v[1]; c.yellow = v[2]; c.black = v[3]; return c; }
function dropLayer(doc, nm) { try { var l = doc.layers.getByName(nm); l.locked = false; l.remove(); } catch (e) {} }
// After doc-color-cmyk, doc.spots[i] goes stale as soon as any swatch changes, so swatches are reached by name.
function spotOf(doc, nm) { return doc.swatches.getByName(nm).color.spot; }

function saveEPS(doc, folder, prefix, range) {
    new Folder(folder).create();
    var o = new EPSSaveOptions();
    o.saveMultipleArtboards = true;
    o.artboardRange = range || "1-" + doc.artboards.length;
    o.cmykPostScript = true;
    o.embedAllFonts = true;
    o.embedLinkedFiles = true;
    o.compatibility = Compatibility.ILLUSTRATOR16;  // Illustrator CS6 EPS: opens in CS6 and later, any RIP
    o.preview = EPSPreview.TRANSPARENTCOLORTIFF;
    o.includeDocumentThumbnails = true;
    doc.saveAs(new File(folder + "/" + prefix + ".eps"), o);
}
function savePDF(doc, path, preset, range, layers) {
    var o = new PDFSaveOptions();
    o.pDFPreset = preset;
    o.preserveEditability = false;
    o.viewAfterSaving = false;
    o.acrobatLayers = !!layers;
    if (range) o.artboardRange = range;
    doc.saveAs(new File(path), o);
}

var C = P.cmyk;
try {  // every exit, error or not, hands Illustrator back its alert level
closeIfOpen(P.src); closeIfOpen(C.ai);
for (var pj = 0; pj < (P.pms || []).length; pj++) closeIfOpen(P.pms[pj].ai);
var doc = app.open(new File(P.src));
try {
    // ------------------------------------------------------------ CMYK master
    // Swatch handles go stale in the session that ran doc-color-cmyk (and an RGB document refuses CMYK swatch
    // definitions), so the converted document is saved, closed and reopened before the exact builds are set.
    // (The loop variable is not `name`: a global `name` in Illustrator's ExtendScript is app.name.)
    // In one open session only part of the swatches are reachable, and which part varies, so the builds are set in
    // rounds: open, set every swatch that answers, save, close, and repeat for the rest until none is left.
    app.executeMenuCommand("doc-color-cmyk");
    doc.saveAs(new File(C.ai), new IllustratorSaveOptions());
    doc.close(SaveOptions.DONOTSAVECHANGES);
    var pending = [], n = 0, rounds = 0;
    for (var swName in P.swatches) { pending.push(swName); n++; }
    while (pending.length && rounds < 8) {
        rounds++;
        doc = app.open(new File(C.ai));
        var still = [];
        for (var pi0 = 0; pi0 < pending.length; pi0++) {
            try { spotOf(doc, pending[pi0]).color = cmyk(P.swatches[pending[pi0]].cmyk); } catch (eS) { still.push(pending[pi0]); }
        }
        doc.save();
        doc.close(SaveOptions.DONOTSAVECHANGES);
        if (still.length === pending.length) break;  // no progress this round
        pending = still;
    }
    report.push("CMYK builds set in " + rounds + " rounds" + (pending.length ? "; NOT SET: " + pending.join(", ") : ""));
    doc = app.open(new File(C.ai));
    // doc.spots.getByName still answers when the swatch route has gone stale; a swatch neither route can read is
    // reported as unreadable, not as a mismatch (build.py inventory reads every master again in a fresh session)
    var off = [], unread = [];
    for (var swName2 in P.swatches) {
        var want = P.swatches[swName2].cmyk, cc = null;
        try { cc = doc.spots.getByName(swName2).color; } catch (eR) { try { cc = spotOf(doc, swName2).color; } catch (eR2) {} }
        try {
            if (cc.typename !== "CMYKColor" || Math.abs(cc.cyan - want[0]) + Math.abs(cc.magenta - want[1]) + Math.abs(cc.yellow - want[2]) + Math.abs(cc.black - want[3]) > 0.5)
                off.push(swName2);
        } catch (eR3) { unread.push(swName2); }
    }
    report.push("CMYK builds: " + (off.length ? "MISMATCH " + off.join(", ") + "; " : "") + (n - off.length - unread.length) + " of " + n +
                " read back exact" + (unread.length ? "; unreadable in this session: " + unread.join(", ") : ""));
    // one-colour black prints on the K plate only and overprints, as the print spec says. A fill is matched to AAP
    // Black by its spot handle or, when that comparison misses, by the spot's name; a path whose fill answers neither
    // way in this session is retried after a save, close and reopen (like the swatch builds), and any left is NOT SET.
    var black = null;
    function blackSpot() { try { return spotOf(doc, "AAP Black"); } catch (e) { try { return doc.spots.getByName("AAP Black"); } catch (e2) { return null; } } }
    function markBlack(k) {  // -> 1 marked, 0 not black, -1 could not tell
        try {
            var pi = doc.pathItems[k];
            if (!pi.filled || pi.fillColor.typename !== "SpotColor") return 0;
            var isK = false;
            try { isK = black !== null && pi.fillColor.spot === black; } catch (e) {}
            if (!isK) isK = pi.fillColor.spot.name === "AAP Black";
            if (!isK) return 0;
            pi.fillOverprint = true;
            return 1;
        } catch (eK) { return -1; }
    }
    var kOver = 0, todoK = [];
    black = blackSpot();
    for (var k = 0; k < doc.pathItems.length; k++) { var mk = markBlack(k); if (mk < 0) todoK.push(k); else kOver += mk; }
    for (var rk = 0; todoK.length && rk < 6; rk++) {
        doc.save(); doc.close(SaveOptions.DONOTSAVECHANGES);
        doc = app.open(new File(C.ai)); black = blackSpot();
        var leftK = [];
        for (var t3 = 0; t3 < todoK.length; t3++) { var mk3 = markBlack(todoK[t3]); if (mk3 < 0) leftK.push(todoK[t3]); else kOver += mk3; }
        if (leftK.length === todoK.length) break;
        todoK = leftK;
    }
    report.push("K100 overprint on " + kOver + " paths" + (todoK.length ? "; overprint NOT SET on " + todoK.length + " paths whose fill would not read" : ""));
    doc.saveAs(new File(C.ai), new IllustratorSaveOptions());
    if (C.proofPdf) {  // viewing proof: the dark and knockout panels print here so white artwork can be seen
        var bg = null;
        try { bg = doc.layers.getByName("Background"); bg.printable = true; } catch (e2) {}
        savePDF(doc, C.proofPdf, "[High Quality Print]", C.artboards, true);
        if (bg) bg.printable = false;
    }
    if (C.pdf) {  // the press file carries no background panels (the proof shows them), not even as a hidden layer
        dropLayer(doc, "Labels"); dropLayer(doc, "Background");
        savePDF(doc, C.pdf, "[PDF/X-4:2008]", C.artboards, true);
    }
    dropLayer(doc, "Background"); dropLayer(doc, "Labels");
    if (C.epsFolder) saveEPS(doc, C.epsFolder, C.epsPrefix, C.artboards);
    report.push("CMYK master, PDFs and EPS written");
} catch (eC) {
    try { doc.close(SaveOptions.DONOTSAVECHANGES); } catch (eX) {}
    throw new Error("CMYK stage: " + eC.message + " (line " + eC.line + ")");
}
doc.close(SaveOptions.DONOTSAVECHANGES);

// ---------------------------------------------------------------- Pantone (spot) masters, from the CMYK master
for (var j = 0; j < (P.pms || []).length; j++) {
    var J = P.pms[j];
    try {  // any failure, in the copy, a round or the EPS, closes this master and names the stage
    // the same rounds as the CMYK builds: a copy of the CMYK master, then each logo ink turned into its spot in
    // whichever open session can reach it (black, white and the shading tones stay process)
    var srcF = new File(C.ai), dstF = new File(J.ai);
    if (dstF.exists) dstF.remove();
    srcF.copy(dstF.fsName);
    var todo = [], made = [], tries = 0;
    for (var nm2 in P.swatches) if (P.swatches[nm2].spots && P.swatches[nm2].spots[J.side]) todo.push(nm2);
    while (todo.length && tries < 8) {
        tries++;
        doc = app.open(dstF);
        var left = [];
        for (var q2 = 0; q2 < todo.length; q2++) {
            var s = P.swatches[todo[q2]].spots[J.side];
            try {
                var sp = spotOf(doc, todo[q2]);
                sp.colorType = ColorModel.SPOT;
                sp.spotKind = SpotColorKind.SPOTCMYK;
                sp.color = cmyk(s.cmyk);
                sp.name = s.name;
                made.push(s.name);
            } catch (eT) { left.push(todo[q2]); }
        }
        doc.save();
        doc.close(SaveOptions.DONOTSAVECHANGES);
        if (left.length === todo.length) break;
        todo = left;
    }
    if (todo.length) report.push("PMS " + J.side + " NOT CONVERTED: " + todo.join(", "));
    doc = app.open(dstF);
    var chk = [];
    for (var m = 0; m < made.length; m++) {
        try { chk.push(made[m] + (spotOf(doc, made[m]).colorType === ColorModel.SPOT ? " spot" : " NOT SPOT")); }
        catch (e3) { chk.push(made[m] + " missing"); }
    }
    report.push("PMS " + J.side + ": " + chk.join(", "));
    dropLayer(doc, "Background"); dropLayer(doc, "Labels");
    if (J.epsFolder) saveEPS(doc, J.epsFolder, J.epsPrefix, C.artboards);
    doc.close(SaveOptions.DONOTSAVECHANGES);
    } catch (eP) {
        closeIfOpen(J.ai);
        throw new Error("PMS " + J.side + " stage: " + eP.message + " (line " + eP.line + ")");
    }
}
} finally { app.userInteractionLevel = prevLevel; }
report.join("; ");
