// Save every artboard of a finished master as its own .ai file. build.py prepends `var SPLIT_PATH = "...";` pointing
// at {jobs: [{src, folder, prefix}]}; Illustrator writes <folder>/<prefix>_<artboard name>.ai for each artboard.
function readText(p) { var f = new File(p); f.encoding = "UTF-8"; f.open("r"); var s = f.read(); f.close(); return s; }
var C = eval("(" + readText(SPLIT_PATH) + ")");
var prevLevel = app.userInteractionLevel;
app.userInteractionLevel = UserInteractionLevel.DONTDISPLAYALERTS;
var report = [];
for (var j = 0; j < C.jobs.length; j++) {
    var J = C.jobs[j], doc = app.open(new File(J.src));
    try {
        new Folder(J.folder).create();
        var o = new IllustratorSaveOptions();
        o.saveMultipleArtboards = true;
        o.artboardRange = "1-" + doc.artboards.length;
        doc.saveAs(new File(J.folder + "/" + J.prefix + ".ai"), o);
        report.push(J.prefix + ": " + doc.artboards.length + " artboards");
    } finally {
        doc.close(SaveOptions.DONOTSAVECHANGES);
    }
}
app.userInteractionLevel = prevLevel;
report.join("; ");
