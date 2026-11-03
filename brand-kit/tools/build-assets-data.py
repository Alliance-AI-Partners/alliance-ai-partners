"""Gather the design system's manifests into brand-kit/assets-data.js (window.AAP_ASSETS) for the showcase page, and pack
the downloadable logo kit. Run after any asset changes: python brand-kit/tools/build-assets-data.py"""
import json
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BK, DS = ROOT / "brand-kit", ROOT / "design-system"
rel = lambda p: "../" + Path(p).relative_to(ROOT).as_posix()  # paths as the showcase (brand-kit/index.html) sees them
load = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))


def lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def wcag(a, b):
    x, y = sorted((lum(a), lum(b)), reverse=True)
    return round((x + 0.05) / (y + 0.05), 2)


# logos: lockup -> state -> files
logos = {}
LOCKUP_NAMES = {"primary-horizontal": "Primary", "secondary-stacked": "Stacked", "horizontal-tagline": "Horizontal with tagline",
                "horizontal-descriptor": "Horizontal with descriptor", "stacked-tagline": "Stacked with tagline", "stacked-two-line": "Stacked two-line",
                "logomark": "Logomark", "wordmark": "Wordmark", "favicon-32": "Favicon 32 px", "favicon-16": "Favicon 16 px"}
for f in load(DS / "logos/logos.json")["files"]:
    e = logos.setdefault(f["lockup"], {"name": LOCKUP_NAMES[f["lockup"]], "states": {}})
    s = e["states"].setdefault(f["state"], {"ground": f["ground"]})
    s[f["format"]] = rel(DS / f["path"])

pal = load(ROOT / "docs/brand-kit/_build/palette.json")
pc = load(ROOT / "docs/brand-kit/_build/print-colors.json")["colors"]
tok = load(DS / "tokens/tokens.json")
colours = []
for c in pal["core"]:
    if c["name"] == "Black":
        continue
    rec = pc.get(c["name"], {}).get("recommended", {})
    h = c["hex"]
    colours.append({"name": c["name"], "hex": h, "rgb": [int(h[i:i + 2], 16) for i in (1, 3, 5)], "role": c["role"], "story": c.get("story", ""),
                    "cmyk": rec.get("cmyk"), "pantone_c": rec.get("pantone_c"), "pantone_u": rec.get("pantone_u"),
                    "token": f"--aap-color-brand-{c['name'].lower().replace(' ', '-')}",
                    "on_daylight": wcag(h, "#F4F7FB"), "on_navy": wcag(h, "#121B2A"), "on_white": wcag(h, "#FFFFFF")})
shading = [{"name": c["name"], "hex": c["hex"], "ramp": c["ramp"], "role": c["role"], "token": f"--aap-color-shading-{c['name'].lower().replace(' ', '-')}"} for c in pal["shading"]]
neutrals = [{"step": k, "hex": v["$value"]} for k, v in tok["color"]["neutral"].items() if not k.startswith("$")]
contrast = [{"fg": f, "bg": b, "fg_hex": fh, "bg_hex": bh, "ratio": wcag(fh, bh), "use": u} for f, fh, b, bh, u in (
    ("Partner Navy", "#121B2A", "Daylight", "#F4F7FB", "All text and links on light grounds"),
    ("Partner 46", "#42587C", "Daylight", "#F4F7FB", "Secondary text"),
    ("Alliance Blue", "#1B56FF", "Daylight", "#F4F7FB", "The one primary button against the page"),
    ("Pure White", "#FFFFFF", "Alliance Blue", "#1B56FF", "Text on the primary button"),
    ("Daylight", "#F4F7FB", "Partner Navy", "#121B2A", "All text on navy"),
    ("Ribbon Cyan", "#00D5FF", "Partner Navy", "#121B2A", "Links and accent words on navy"),
    ("Ribbon Cyan", "#00D5FF", "Daylight", "#F4F7FB", "Never text: decoration only"))]

icons = load(DS / "icons/icons.json")["files"]
inline = lambda p: (DS / p).read_text(encoding="utf-8").strip()  # inlined: Chrome blocks sprite <use> and fetch on file://
icon_data = {"ui": [{"name": i["name"], "svg": rel(DS / i["path"]), "markup": inline(i["path"])} for i in icons if i["category"] == "ui"],
             "social": [{"name": i["name"], "svg": rel(DS / i["path"]), "markup": inline(i["path"])} for i in icons if i["category"] == "social"],
             "services": sorted({i["service"] for i in icons if i["category"] == "brand"})}
graphics = [{**{k: g[k] for k in ("name", "category", "description")}, "png": rel(DS / g["path"]), "svg": rel(DS / g["path"].replace(".png", ".svg"))}
            for g in load(DS / "imagery/imagery.json")["files"] if g["path"].endswith(".png") and g.get("category") != "background"]
backgrounds = [{"name": g["name"], "description": g["description"], "src": rel(DS / g["path"]), "prompt": g.get("prompt", "")}
               for g in load(DS / "imagery/imagery.json")["files"] if g.get("category") == "background"]

merch = []
for it in load(BK / "merch/merch.json")["files"]:
    stem = Path(it["path"]).stem
    mock = next(iter(sorted((BK / "merch/mockups").glob(f"{stem.split('-')[0]}*.webp"))), None) if (BK / "merch/mockups").exists() else None
    merch.append({**it, "artwork": f"merch/{it['path']}", "preview": f"merch/previews/{stem}-artwork.png", "mockup": f"merch/mockups/{mock.name}" if mock else None})


def gallery(folder, pattern):
    out = []
    for html in sorted((BK / folder).glob("*.html")):
        prev = sorted((BK / folder / "previews").glob(pattern.format(html.stem)))
        if prev:
            out.append({"name": html.stem, "html": f"{folder}/{html.name}", "previews": [f"{folder}/previews/{p.name}" for p in prev]})
    return out


emails = gallery("emails", "{}-*.png")
templates = gallery("templates", "{}.png")

# the downloadable logo kit: every logo file, the app icons and a short usage note
dl = BK / "downloads"
dl.mkdir(exist_ok=True)
kit_zip = dl / "alliance-ai-partners-logo-kit.zip"
with zipfile.ZipFile(kit_zip, "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted((DS / "logos").rglob("*")):
        if p.is_file() and p.suffix in (".svg", ".png", ".ico", ".webmanifest"):
            z.write(p, "logos/" + p.relative_to(DS / "logos").as_posix())
    z.writestr("README.txt", "Alliance AI Partners logo kit (2026-11-02)\n\n"
               "lockups/ and marks/: SVG for screens and print, PNG at 2x for documents.\n"
               "Use full-color-light on Daylight or white, full-color-dark on Partner Navy, mono-white on photographs,\n"
               "flat-* where gradients cannot print (embroidery, screen print), mono-black for one-ink work.\n"
               "Clear space: 0.287 x the mark's height on every side. Do not recolour, stretch, outline or rebuild the logo.\n"
               "Colours: Alliance Blue #1B56FF, Ribbon Cyan #00D5FF, Partner Navy #121B2A, Daylight #F4F7FB.\n")
downloads = [{"name": "Logo kit", "file": "downloads/" + kit_zip.name, "size_kb": round(kit_zip.stat().st_size / 1024), "what": "Every lockup and state in SVG and PNG, plus app icons"},
             {"name": "Design tokens", "file": rel(DS / "tokens/tokens.css"), "size_kb": round((DS / "tokens/tokens.css").stat().st_size / 1024), "what": "CSS custom properties (also tokens.json and a Tailwind v4 theme)"},
             {"name": "Fonts", "file": rel(DS / "fonts/FONTS.md"), "size_kb": None, "what": "Mona Sans and Mona Sans Mono, SIL Open Font License"},
             {"name": "Icon sprite", "file": rel(DS / "icons/sprite.svg"), "size_kb": round((DS / "icons/sprite.svg").stat().st_size / 1024), "what": "28 UI and 5 social icons, currentColor"}]
board = BK / "brand-board.png"
if board.exists():  # captured from the #brand-board element of index.html; its pixel size comes from the PNG header
    w, h = struct.unpack(">II", board.read_bytes()[16:24])
    downloads.insert(1, {"name": "Brand board", "file": board.name, "size_kb": round(board.stat().st_size / 1024), "what": f"The brand on one page for decks and briefs, PNG, {w} by {h} px"})

data = {"generated": "2026-11-02", "logos": logos, "colours": colours, "shading": shading, "neutrals": neutrals,
        "daybreak": pal["signature"], "contrast": contrast, "icons": icon_data, "graphics": graphics, "backgrounds": backgrounds,
        "merch": merch, "emails": emails, "templates": templates, "downloads": downloads}
(BK / "assets-data.js").write_text("/* Generated by brand-kit/tools/build-assets-data.py from the design-system manifests. Do not edit by hand. */\n"
                                    "window.AAP_ASSETS = " + json.dumps(data, indent=1, ensure_ascii=False) + ";\n", encoding="utf-8")
print(f"logos {len(logos)} lockups | colours {len(colours)} | icons {len(icon_data['ui'])}+{len(icon_data['social'])} | graphics {len(graphics)} | "
      f"backgrounds {len(backgrounds)} | merch {len(merch)} | emails {len(emails)} | templates {len(templates)} | logo kit {downloads[0]['size_kb']} KB")
