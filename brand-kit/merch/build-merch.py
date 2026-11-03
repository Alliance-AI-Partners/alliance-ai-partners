"""Vendor placement artwork for Alliance AI Partners merchandise: one SVG per decorated surface, drawn at its real size in
millimetres, plus merch.json. Logos are the finalized logo-kit files, inlined as vectors; text is live Mona Sans (convert to
outlines before release). Run: python brand-kit/merch/build-merch.py"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
DS = HERE.parents[1] / "design-system"
ART = HERE / "artwork"
ART.mkdir(exist_ok=True)
NAVY, BLUE, CYAN, DAY, WHITE = "#121B2A", "#1B56FF", "#00D5FF", "#F4F7FB", "#FFFFFF"
_n = 0


def logo(name, x, y, w=None, h=None):
    """A logo file from design-system/logos inlined at (x, y) mm, scaled to width w or height h; ids namespaced."""
    global _n
    _n += 1
    folder = "marks" if ("logomark" in name or "wordmark" in name) else "lockups"
    t = (DS / "logos" / folder / f"alliance-ai-partners-{name}.svg").read_text(encoding="utf-8")
    t = re.sub(r"<\?xml[^>]*>\s*", "", t)
    vw, vh = (float(v) for v in re.search(r'viewBox="[\d.\-]+ [\d.\-]+ ([\d.]+) ([\d.]+)"', t).groups())
    w = w if w is not None else h * vw / vh
    h = h if h is not None else w * vh / vw
    t = re.sub(r'\bid="([^"]+)"', lambda m: f'id="L{_n}-{m.group(1)}"', t)
    t = re.sub(r"url\(#([^)]+)\)", lambda m: f"url(#L{_n}-{m.group(1)})", t)
    t = re.sub(r'href="#([^"]+)"', lambda m: f'href="#L{_n}-{m.group(1)}"', t)
    t = re.sub(r"<svg\b[^>]*>", f'<svg x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" viewBox="0 0 {vw:g} {vh:g}">', t, count=1)
    return t, w, h


def ribbon(x0, y0, x1, y1, amp, width, gid, stops=((0, NAVY), (0.54, BLUE), (1, CYAN)), dash=None):
    """The Daybreak ribbon as one smooth S-curve across a box."""
    sx = "".join(f'<stop offset="{o:g}" stop-color="{c}"/>' for o, c in stops)
    mx = (x0 + x1) / 2
    d = f"M{x0:.1f} {y0:.1f} C {x0 + (x1 - x0) * .3:.1f} {y0 - amp:.1f}, {mx - (x1 - x0) * .1:.1f} {y1 + amp:.1f}, {mx:.1f} {(y0 + y1) / 2:.1f} S {x1 - (x1 - x0) * .25:.1f} {y1 - amp:.1f}, {x1:.1f} {y1:.1f}"
    return (f'<linearGradient id="{gid}" x1="{x0}" y1="0" x2="{x1}" y2="0" gradientUnits="userSpaceOnUse">{sx}</linearGradient>',
            f'<path d="{d}" fill="none" stroke="url(#{gid})" stroke-width="{width}" stroke-linecap="round"/>')


def text(s, x, y, size, fill, weight=600, stretch=125, anchor="start", tracking=-0.02):
    return (f'<text x="{x:.2f}" y="{y:.2f}" fill="{fill}" font-family="Mona Sans, Montserrat, Arial, sans-serif" font-size="{size:g}" '
            f'font-weight="{weight}" font-stretch="{stretch:g}%" letter-spacing="{tracking * size:.2f}" text-anchor="{anchor}">{s}</text>')


def doc(name, w, h, body, defs="", bg=None, title=""):
    rect = f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else ""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" viewBox="0 0 {w} {h}">\n'
           f'<title>{title}</title>\n<defs>{defs}</defs>\n{rect}\n{body}\n</svg>\n')
    (ART / f"{name}.svg").write_text(svg, encoding="utf-8")
    return f"artwork/{name}.svg"


items = []


def add(item, placement, path, size, method, colours, logo_file, ground, notes):
    items.append({"path": path, "item": item, "placement": placement, "size_mm": size, "method": method, "colours": colours,
                  "logo": logo_file, "garment_or_ground": ground, "notes": notes})


# 1. Cap: structured six-panel, Partner Navy. Embroidery cannot hold gradients, so the flat-dark mark (three thread colours).
m, w, h = logo("logomark-flat-dark", 0, 0, w=57)
add("Cap", "Front panel, centred, 6 mm above the seam line", doc("cap-front-embroidery", 57, round(h, 1), m, title="Cap front: logomark, flat dark, embroidery"),
    [57, round(h, 1)], "Flat embroidery in one thread, about 9,000 stitches", ["Ribbon Cyan thread (PMS 305 C match)"],
    "logomark-flat-dark", "Partner Navy structured cap",
    "The flat-dark mark is the kit's one-ink state, made for thread. Keep 3 mm clear of the panel seams; approve a sew-out before the run.")
m, w, h = logo("wordmark-flat-dark", 0, 0, w=60)
add("Cap", "Back, above the strap", doc("cap-back-embroidery", 60, round(h, 1), m, title="Cap back: wordmark, embroidery"),
    [60, round(h, 1)], "Flat embroidery", ["Daylight white thread", "Ribbon Cyan thread"], "wordmark-flat-dark", "Partner Navy structured cap",
    "Smallest legible size for the wordmark in thread; do not go smaller.")

# 2. Tumbler: 20 oz insulated, Partner Navy powder coat, full-colour UV wrap (235 x 102 mm print area).
W, H = 235, 102
g, rib = ribbon(0, 70, W, 34, 28, 3.2, "tumbler-rib")
m, mw, mh = logo("logomark-full-color-dark", 0, 0, w=46)
m = m.replace('x="0.00" y="0.00"', f'x="{W / 4 - mw / 2:.2f}" y="{H / 2 - mh / 2:.2f}"', 1)
body = rib + m + text("Put AI to work.", W * 0.75, H / 2 + 4, 9.5, DAY, anchor="middle")
add("Tumbler", "Full wrap: the mark on the front (handle at the seam), the line on the back", doc("tumbler-wrap-20oz", W, H, body, g, NAVY, "Tumbler 20 oz wrap"),
    [W, H], "UV-LED full-colour print on Partner Navy powder coat", ["CMYK + white underbase", "Partner Navy ground (PMS 7547 C)"],
    "logomark-full-color-dark", "Partner Navy 20 oz tumbler",
    "The ribbon crosses the seam; ask the printer to align it within 1 mm. For a single-colour job use laser engraving with the mono-white mark instead.")

# 3. Tee: Partner Navy cotton tee, screen printed.
m, w, h = logo("logomark-flat-dark", 0, 0, w=90)
add("T-shirt", "Left chest, 90 mm wide, 80 mm below the collar", doc("tee-front-chest", 90, round(h, 1), m, title="Tee front: logomark"),
    [90, round(h, 1)], "Screen print, 1 spot colour", ["PMS 305 C (Ribbon Cyan)"], "logomark-flat-dark", "Partner Navy cotton tee", "")
W, H = 280, 70
g, rib = ribbon(10, 58, W - 10, 52, 8, 2.2, "tee-rib")
body = text("Partners in AI.", W / 2, 22, 19, DAY, anchor="middle") + text("Partners in growth.", W / 2, 44, 19, CYAN, anchor="middle") + rib
add("T-shirt", "Back, 280 mm wide, 60 mm below the collar", doc("tee-back-tagline", W, H, body, g, title="Tee back: tagline"),
    [W, H], "Screen print, 3 spot colours (the ribbon as a 4-step halftone blend)", ["White", "PMS 305 C", "PMS 2726 C"], "none (type)", "Partner Navy cotton tee",
    "Convert the type to outlines before sending.")

# 4. Hoodie: embroidered mark, centre chest.
m, w, h = logo("logomark-flat-dark", 0, 0, w=100)
add("Hoodie", "Centre chest, 100 mm wide, 110 mm below the hood seam", doc("hoodie-chest-embroidery", 100, round(h, 1), m, title="Hoodie chest: logomark"),
    [100, round(h, 1)], "Flat embroidery in one thread", ["Ribbon Cyan thread (PMS 305 C match)"], "logomark-flat-dark", "Partner Navy heavyweight hoodie", "")

# 5. Tote: natural canvas, two-colour screen print.
W, H = 300, 300
g, rib = ribbon(0, 250, W, 205, 26, 4, "tote-rib", stops=((0, NAVY), (1, BLUE)))
m, mw, mh = logo("primary-horizontal-flat-light", 0, 0, w=210)
m = m.replace('x="0.00" y="0.00"', f'x="{W / 2 - mw / 2:.2f}" y="70.00"', 1)
add("Tote bag", "Front panel, lockup centred, ribbon across the foot", doc("tote-front", W, H, m + rib, g, title="Tote front"),
    [W, H], "Screen print, 2 spot colours (the ribbon as a navy-to-blue halftone blend)", ["PMS 7547 C (Partner Navy)", "PMS 2726 C (Alliance Blue)"],
    "primary-horizontal-flat-light", "Natural or Daylight-white canvas tote", "Print area 300 x 300 mm; keep 25 mm from the handles.")

# 6. Notebook: A5 hardcover, deboss die art plus a Ribbon Cyan ribbon marker.
m, w, h = logo("logomark-mono-black", 0, 0, w=40)
add("Notebook", "Front cover, centred, 40 mm wide", doc("notebook-cover-deboss", 40, round(h, 1), m, title="Notebook cover: deboss die art"),
    [40, round(h, 1)], "Blind deboss (black = die area)", ["Blind (no ink) on Partner Navy linen", "Ribbon marker: Ribbon Cyan satin"],
    "logomark-mono-black", "A5 hardcover, Partner Navy linen", "The cyan ribbon marker is the brand's ribbon made literal; specify PMS 305 C for the satin.")

# 7. Mug: 11 oz white ceramic, sublimation wrap (210 x 85 mm).
W, H = 210, 85
g, rib = ribbon(105, 66, W - 8, 40, 14, 2.2, "mug-rib")
m, mw, mh = logo("logomark-full-color-light", 0, 0, w=44)
m = m.replace('x="0.00" y="0.00"', f'x="{52.5 - mw / 2:.2f}" y="{H / 2 - mh / 2:.2f}"', 1)
body = m + text("Put AI to work.", 157.5, 34, 11, NAVY, anchor="middle") + rib
add("Mug", "Wrap: mark on the drinking side, line on the other", doc("mug-wrap-11oz", W, H, body, g, WHITE, "Mug 11 oz wrap"),
    [W, H], "Sublimation, full colour", ["CMYK"], "logomark-full-color-light", "White 11 oz ceramic mug", "Keep 15 mm clear either side of the handle.")

# 8. Stickers: one A5 kiss-cut sheet.
W, H = 148, 210
parts, defs = [], ""
m, mw, mh = logo("primary-horizontal-full-color-dark", 0, 0, w=110)
parts.append(f'<rect x="19" y="18" width="110" height="{mh + 16:.1f}" rx="{(mh + 16) / 2:.1f}" fill="{NAVY}"/>' + m.replace('x="0.00" y="0.00"', 'x="19.00" y="26.00"', 1))
m, mw, mh = logo("logomark-full-color-dark", 0, 0, w=34)
parts.append(f'<circle cx="44" cy="112" r="26" fill="{NAVY}"/>' + m.replace('x="0.00" y="0.00"', f'x="{44 - mw / 2:.2f}" y="{112 - mh / 2:.2f}"', 1))
parts.append(f'<rect x="80" y="96" width="56" height="32" rx="16" fill="{BLUE}"/>' + text("Put AI to work.", 108, 115, 6.2, WHITE, anchor="middle", stretch=112.5))
g, rib = ribbon(18, 178, 130, 156, 12, 6, "sticker-rib")
defs += g
parts.append(rib)
add("Stickers", "A5 kiss-cut sheet: pill lockup, round mark, 'Put AI to work.', ribbon", doc("sticker-sheet-a5", W, H, "".join(parts), defs, WHITE, "Sticker sheet A5"),
    [W, H], "Digital print on white vinyl, kiss-cut with 2 mm bleed", ["CMYK"], "primary-horizontal-full-color-dark, logomark-full-color-dark", "White gloss vinyl",
    "The die-cut sticker master with its CutContour line is in docs/brand-kit/Print-Masters/Badges-Sticker/.")

# 9. Lanyard and ID badge.
W, H = 900, 20
g = f'<linearGradient id="lan" x1="0" y1="0" x2="{W}" y2="0" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="{NAVY}"/><stop offset=".54" stop-color="{BLUE}"/><stop offset="1" stop-color="{CYAN}"/></linearGradient>'
body = f'<rect width="{W}" height="{H}" fill="url(#lan)"/>'
for i in range(6):
    mm, mw, mh = logo("wordmark-mono-white", 0, 0, h=6)
    body += mm.replace('x="0.00" y="0.00"', f'x="{40 + i * 150:.2f}" y="{(H - mh) / 2:.2f}"', 1)
add("Lanyard", "Full length, 20 x 900 mm, wordmark every 150 mm", doc("lanyard-20mm", W, H, body, g, title="Lanyard"),
    [W, H], "Dye-sublimation on polyester", ["CMYK (the Daybreak gradient)", "White"], "wordmark-mono-white", "20 mm flat polyester lanyard",
    "The lanyard is the ribbon worn: the gradient runs end to end, navy at the clip.")
W, H = 54, 86
m, mw, mh = logo("logomark-full-color-dark", 0, 0, w=18)
body = (f'<rect width="{W}" height="30" fill="{NAVY}"/>' + m.replace('x="0.00" y="0.00"', f'x="{W / 2 - mw / 2:.2f}" y="{15 - mh / 2:.2f}"', 1)
        + text("[Full name]", W / 2, 50, 4.6, NAVY, anchor="middle", stretch=112.5) + text("[Role]", W / 2, 57, 3.2, "#42587C", weight=450, stretch=100, anchor="middle", tracking=0)
        + text("Alliance AI Partners", W / 2, 79, 2.8, "#60697A", weight=500, stretch=100, anchor="middle", tracking=0.01))
g2, rib = ribbon(0, 30.5, W, 30.5, 0.01, 1.2, "badge-rib")
add("ID badge", "CR80 card, portrait", doc("id-badge-cr80", W, H, body + rib, g2, WHITE, "ID badge CR80"),
    [W, H], "Dye-sublimation or direct-to-card print", ["CMYK"], "logomark-full-color-dark", "White PVC card, 0.76 mm", "Name and role are placeholders; print per person.")

(HERE / "merch.json").write_text(json.dumps({"area": "merch", "retrieved": "2026-11-02", "files": items}, indent=1) + "\n", encoding="utf-8")

# Flat previews: each artwork inlined in a page that loads the brand fonts, captured with brand-kit/tools/capture.cjs.
prev = HERE / "previews" / "_artwork"
prev.mkdir(parents=True, exist_ok=True)
for it in items:
    name = Path(it["path"]).stem
    svg = (HERE / it["path"]).read_text(encoding="utf-8")
    w_mm, h_mm = it["size_mm"]
    scale = min(1100 / w_mm, 700 / h_mm)
    svg = re.sub(r'width="[\d.]+mm" height="[\d.]+mm"', f'width="{w_mm * scale:.0f}" height="{h_mm * scale:.0f}"', svg, count=1)
    ground = "#E3E6EC" if "mono-black" in it["logo"] or "navy" not in it["garment_or_ground"].lower() else NAVY  # die art previews on light
    (prev / f"{name}.html").write_text(
        f'<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="../../../../design-system/tokens/tokens.css">'
        f'<body style="margin:0"><div id="artefact" style="display:inline-block;padding:40px;background:{ground}">{svg}</div></body>', encoding="utf-8")
print(f"{len(items)} artwork files; preview pages in {prev}")
