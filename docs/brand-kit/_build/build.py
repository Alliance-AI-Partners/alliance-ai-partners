"""Assemble the Alliance AI Partners Illustrator masters from the verified vector components.

    python build.py suite | recreations | graphics | print | all

Python lays out every artboard (points, y down) from the component SVGs and the fit data, writes a scene JSON to
scenes/ and runs aap_render.jsx in Illustrator over COM; `print` runs aap_print.jsx on the suite. Each document is
then checked: Illustrator's PNG export against a VectorCraft render of the same layout (import fidelity), and every
recreation against its original image (verify/)."""
import json
import math
import re
import shutil
import subprocess
import sys
import zlib
from pathlib import Path

import numpy as np
from PIL import Image

import kit

sys.path.insert(0, str(kit.WORK / "print"))
import match  # noqa: E402  CMYK builds through the ICC profiles

PREP, SCENES = kit.BUILD / "prepared", kit.BUILD / "scenes"
CAP = 0.70004  # Montserrat cap height / em
WM, TAG, DESC = "ALLIANCE AI PARTNERS", "Partners in AI. Partners in growth.", "ENTERPRISE AI CONSULTING"
SEAL = "ALLIANCE AI PARTNERS • PARTNERS IN AI • PARTNERS IN GROWTH •"  # the ring closes back to "ALLIANCE"
BRAND = json.loads((kit.BUILD / "palette.json").read_text(encoding="utf-8"))  # the unified palette (README "Colour")
CORE = {"AAP " + c["name"]: c["hex"] for c in BRAND["core"]}
CORE_HEX = {v: k for k, v in CORE.items()}
SHADING = {c["hex"]: c["name"] for c in BRAND["shading"]}  # hex -> the 3D mark's shading token


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


HERO = jload(kit.COMP / "ap-hero.json")
MB = HERO["bbox"]
MW, MH = MB[2] - MB[0], MB[3] - MB[1]
P_STEM_X = 541.4  # left edge of the P stem in master space (measured line, ap-hero.json)
H = 240.0  # mark height of every master lockup, pt
MWH = MW * H / MH
CS = 0.287  # clear space x = 0.287 x mark height (measured on board 02, panel "04 | CLEAR SPACE")
GUT = 96


# ---------------------------------------------------------------- geometry and SVG helpers

def bbox(ds):
    pts = np.array([p for d in ds for poly in kit.flatten(kit.parse_d(d)) for p in poly])
    return [float(v) for v in (*pts.min(0), *pts.max(0))]


def ink(string, style, size, tracking):
    """Ink bbox [x0, y0, x1, y1] of a Montserrat setting with its pen origin at 0 on the baseline (y down)."""
    return bbox(kit.text_paths(string, style, size, tracking))


def inner(svg):
    return svg[svg.index(">", svg.index("<svg")) + 1: svg.rindex("</svg>")]


def ns(t, p):
    """Prefix every id and its url(#..)/href references so several SVGs can share one document."""
    t = re.sub(r'\bid="([^"]+)"', lambda m: f'id="{p}-{m.group(1)}"', t)
    t = re.sub(r"url\(#([^)]+)\)", lambda m: f"url(#{p}-{m.group(1)})", t)
    return re.sub(r'href="#([^"]+)"', lambda m: f'href="#{p}-{m.group(1)}"', t)


def text_of(src):
    return src if isinstance(src, str) and src.lstrip().startswith("<") else Path(src).read_text(encoding="utf-8")


def edit(t, strip=(), recolor=None):
    for pat in strip:
        t = re.sub(pat, "", t, flags=re.S)
    for a, b in (recolor or {}).items():
        t = re.sub(re.escape(a), b, t, flags=re.I)
    return t


def compose(w, h, layers):
    """layers: [(key, svg path or text, s, tx, ty, strip, recolor)] bottom first -> one SVG; defs are hoisted."""
    defs, body = [], []
    for key, src, s, tx, ty, strip, recolor in layers:
        t = ns(inner(edit(text_of(src), strip, recolor)), key)
        defs += re.findall(r"<defs>(.*?)</defs>", t, re.S)
        t = re.sub(r"<defs>.*?</defs>", "", t, flags=re.S)
        sx, sy = s if isinstance(s, (tuple, list)) else (s, s)  # (sx, sy) for a reproportioned placement
        tf = "" if (sx, sy, tx, ty) == (1, 1, 0, 0) else f' transform="matrix({sx:.6f} 0 0 {sy:.6f} {tx:.4f} {ty:.4f})"'
        body.append(f'<g id="{key}"{tf}>{t}</g>')
    return kit.svg_doc(w, h, "\n".join(body), "\n".join(defs))


def L(key, src, s=1.0, tx=0.0, ty=0.0, strip=(), recolor=None):
    return (key, src, s, tx, ty, strip, recolor)


def prep(key, src, strip=(), recolor=None):
    """Write prepared/<key>.svg: the SVG plus the unpainted aap-ref rectangle over its viewBox, which
    aap_render.jsx positions by."""
    t = edit(text_of(src), strip, recolor)
    x, y, w, h = (float(v) for v in re.search(r'viewBox="([^"]+)"', t).group(1).replace(",", " ").split())
    i = t.index(">", t.index("<svg")) + 1
    t = t[:i] + f'\n<rect id="aap-ref" x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" fill="none"/>' + t[i:]
    PREP.mkdir(parents=True, exist_ok=True)
    (PREP / f"{key}.svg").write_text(t, encoding="utf-8")
    return str(PREP / f"{key}.svg")


# ---------------------------------------------------------------- swatches

HEX_RE = re.compile(r'(?:fill|stroke|stop-color)="(#[0-9A-Fa-f]{6})"')
_NAMES = {}


def tone_names():
    """hex -> tone name from every component / fit JSON (the agents' supporting-tone lists)."""
    if not _NAMES:
        def walk(o):
            if isinstance(o, dict):
                if isinstance(o.get("hex"), str) and isinstance(o.get("name"), str):
                    _NAMES.setdefault(o["hex"].upper(), o["name"])
                for v in o.values():
                    walk(v)
            elif isinstance(o, list):
                for v in o:
                    walk(v)
        for p in sorted(kit.COMP.glob("**/*.json")) + sorted(kit.FIT.glob("*.json")):
            walk(jload(p))
    return _NAMES


def swatch_groups(svg_files, extra=(), spots=()):
    used = {h.upper() for f in svg_files for h in HEX_RE.findall(Path(f).read_text(encoding="utf-8"))}
    used |= {h.upper() for h in extra}
    taken, tones = set(CORE) | {"AAP " + n for n in SHADING.values()}, []
    for h in sorted(used - set(CORE_HEX) - set(SHADING)):
        n = "AAP " + re.sub(r"^AP ", "Mark ", tone_names().get(h) or "Tone " + kit.nearest_palette(h)[0])
        if n in taken:
            n += " " + h[1:]
        taken.add(n)
        tones.append({"name": n, "hex": h})
    groups = [{"group": "AAP Core", "colors": [{"name": k, "hex": v} for k, v in CORE.items()]}]
    shading = [{"name": "AAP " + c["name"], "hex": c["hex"]} for c in BRAND["shading"] if c["hex"] in used]
    if shading:
        groups.append({"group": "AAP Mark Shading", "colors": shading})
    if tones:
        groups.append({"group": "AAP Supporting Tones", "colors": sorted(tones, key=lambda c: c["name"])})
    if spots:
        groups.append({"group": "AAP Production", "colors": list(spots)})
    return groups


def fidelity(hex_):
    """Recreation colour rule: keep the measured colour unless it is within dE2000 2 of a core colour."""
    _, ph, de = kit.nearest_palette(hex_)
    return ph if de <= 2.0 else hex_.upper()


def hex_swatch(groups, hex_):
    for g in groups:
        for c in g["colors"]:
            if c.get("hex", "").upper() == hex_.upper() and not c.get("spotCMYK"):
                return c["name"]
    raise KeyError(hex_)


# ---------------------------------------------------------------- scene items

def svg_item(comp, x, y, s=1.0, recolor=None, name=None):
    it = {"type": "svg", "component": comp, "x": x, "y": y, "scale": s, "name": name or comp}
    if recolor:
        it["recolor"] = recolor
    return it


def text_item(string, style, size, tracking, x, baseline, colors, name, align="left"):
    """colors: one swatch name, or [(start, end, swatch), ...] covering the string."""
    spans = [(0, len(string), colors)] if isinstance(colors, str) else colors
    return {"type": "text", "runs": [{"text": string[a:b], "swatch": sw} for a, b, sw in spans if b > a],
            "font": "Montserrat-" + style, "size": size, "tracking": tracking, "x": x, "baseline": baseline,
            "align": align, "name": name}


def shift(it, dx, dy):
    it = dict(it)
    for k in ("x", "x1", "x2", "cx"):
        if k in it:
            it[k] += dx
    for k in ("y", "y1", "y2", "cy", "baseline"):
        if k in it:
            it[k] += dy
    return it


def ranges(idx):
    """1-based artboard indices -> '1-4,7' for ExportForScreensItemToExport.artboards."""
    idx, out, i = sorted(idx), [], 0
    while i < len(idx):
        j = i
        while j + 1 < len(idx) and idx[j + 1] == idx[j] + 1:
            j += 1
        out.append(str(idx[i]) if i == j else f"{idx[i]}-{idx[j]}")
        i = j + 1
    return ",".join(out)


def centre_layout(abs_):
    """Illustrator's canvas (16383 pt square) is centred on the first artboard as created, so the whole layout is
    centred on the origin to keep every artboard on the canvas; integer offsets keep pixel-snapped artboards snapped."""
    x0 = min(a["rect"][0] for a in abs_)
    y0 = min(a["rect"][1] for a in abs_)
    x1 = max(a["rect"][0] + a["rect"][2] for a in abs_)
    y1 = max(a["rect"][1] + a["rect"][3] for a in abs_)
    dx, dy = -round((x0 + x1) / 2), -round((y0 + y1) / 2)
    for a in abs_:
        a["rect"] = [a["rect"][0] + dx, a["rect"][1] + dy, a["rect"][2], a["rect"][3]]
        a["items"] = [shift(it, dx, dy) for it in a["items"]]
    return abs_


def grid(cells, cols, gut=GUT, x0=0, y0=0):
    """cells: [(name, w, h, bg, items)] -> artboards laid out left to right in rows of `cols`, integer origins."""
    abs_, y = [], y0
    for r in range(0, len(cells), cols):
        row, x = cells[r:r + cols], x0
        for name, w, h, bg, items in row:
            abs_.append({"name": name, "rect": [x, y, w, h], "bg": bg, "items": [shift(it, x, y) for it in items]})
            x += math.ceil(w) + gut
        y += math.ceil(max(c[2] for c in row)) + gut
    return abs_, y


# ---------------------------------------------------------------- Illustrator

def illustrator(script, var, cfg):
    runner = SCENES / f"run_{Path(cfg).stem}.jsx"
    runner.write_text(f'var {var} = "{Path(cfg).as_posix()}";\n$.evalFile(new File("{(kit.BUILD / script).as_posix()}"));\n',
                      encoding="utf-8")
    ps = f"$ai = New-Object -ComObject Illustrator.Application; $ai.DoJavaScriptFile('{runner}')"
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0 or r.stderr.strip():
        raise RuntimeError(f"Illustrator {script}: {r.stdout[-1500:]} {r.stderr[-1500:]}")
    return r.stdout.strip()


def render_scene(name, scene):
    SCENES.mkdir(parents=True, exist_ok=True)
    for e in scene.get("exports", []):
        Path(e["folder"]).mkdir(parents=True, exist_ok=True)
    Path(scene["out"]).parent.mkdir(parents=True, exist_ok=True)
    scene["inventory"] = str(kit.VERIFY / f"{name}.inventory.json")  # build by-products stay out of the kit folders
    cfg = SCENES / f"{name}.json"
    cfg.write_text(json.dumps(scene, indent=1), encoding="utf-8")
    for attempt in range(3):
        # after a failed run Illustrator's swatch references can stay unreliable for the next run; a clean retry works
        try:
            msg = illustrator("aap_render.jsx", "SCENE_PATH", cfg)
            break
        except RuntimeError as e:
            if attempt == 2 or not ("PARM" in str(e) or "spot swatch not found" in str(e)):
                raise
            print(f"{name}: Illustrator swatch error, retrying ({attempt + 1})")
    inv = jload(scene["inventory"])
    print(name, "->", msg or inv)
    if inv["unboundColors"] and inv["unboundColors"] != [""]:
        raise RuntimeError(f"{name}: colours without a swatch {inv['unboundColors']}")
    return inv


# ---------------------------------------------------------------- import check: Illustrator export vs VectorCraft

def expected_svg(scene, ab, groups, with_bg=False):
    """The artboard as plain SVG (same components, Montserrat outlines from glyphs.json) for a reference render."""
    hexof = {c["name"]: c.get("hex", "#FF00FF") for g in groups for c in g["colors"]}
    X, Y, W, Hh = ab["rect"]
    body, defs = ([f'<rect width="{W}" height="{Hh}" fill="{hexof[ab["bg"]]}"/>'] if with_bg and ab.get("bg") else []), []
    for n, it in enumerate(ab["items"]):
        if it["type"] == "svg":
            t = edit(text_of(scene["components"][it["component"]]), [r'<rect id="aap-ref"[^>]*/>'])
            if it.get("recolor"):
                t = re.sub(r'(fill|stroke|stop-color)="#[0-9A-Fa-f]{6}"', lambda m: f'{m.group(1)}="{hexof[it["recolor"]]}"', t)
            t = ns(inner(t), f"i{n}")
            defs += re.findall(r"<defs>(.*?)</defs>", t, re.S)
            t = re.sub(r"<defs>.*?</defs>", "", t, flags=re.S)
            s = it["scale"]
            body.append(f'<g transform="matrix({s} 0 0 {s} {it["x"] - X} {it["y"] - Y})">{t}</g>')
        elif it["type"] == "text":
            string = "".join(r["text"] for r in it["runs"])
            style = it["font"].split("-", 1)[1]
            cols = []
            for r in it["runs"]:
                cols += [hexof[r["swatch"]]] * len(r["text"])
            lay = kit.glyphs()["weights"][style]["strings"][string]
            ds = kit.text_paths(string, style, it["size"], it["tracking"], it["x"] - X, it["baseline"] - Y)
            body += [f'<path d="{d}" fill="{cols[g[1]]}"/>' for d, g in zip(ds, lay)]
        elif it["type"] == "rect":
            body.append(f'<rect x="{it["x"] - X}" y="{it["y"] - Y}" width="{it["w"]}" height="{it["h"]}" '
                        f'rx="{it.get("r", 0)}" fill="{hexof[it["fill"]] if it.get("fill") else "none"}"/>')
        else:
            return None  # path text and other Illustrator-only constructs are not checked here
    return kit.svg_doc(W, Hh, "\n".join(body), "\n".join(defs))


def check_exports(name, scene, folder, scale, abs_idx, bg="#808080", with_bg=False):
    """Compare Illustrator's PNG export of each listed artboard with a VectorCraft render of the same layout."""
    rows, sheet, labels = [], [], []
    for i in abs_idx:
        ab = scene["artboards"][i - 1]
        svg = expected_svg(scene, ab, scene["swatches"], with_bg)
        hits = sorted(Path(folder).rglob(f"*{ab['name']}*.png"))
        if svg is None or not hits:
            rows.append({"artboard": ab["name"], "checked": False, "png": bool(hits)})
            continue
        got = np.asarray(Image.open(hits[0]).convert("RGBA"), float) / 255.0
        ref = kit.render_svg(svg, scale)
        h, w = min(got.shape[0], ref.shape[0]), min(got.shape[1], ref.shape[1])
        g, r = got[:h, :w], ref[:h, :w]
        ga, ra = g[..., 3] > 0.5, r[..., 3] > 0.5
        m = ga | ra
        de = kit.de2000(kit.srgb_to_lab(kit.over(g, bg)), kit.srgb_to_lab(kit.over(r, bg)))
        # anti-aliasing differs between the two rasterisers by up to a pixel on thin strokes; the shape check
        # therefore asks how much of each mask lies within 1 px of the other
        tol = min(float((ga & kit.dilate(ra, 1)).sum() / max(1, ga.sum())), float((ra & kit.dilate(ga, 1)).sum() / max(1, ra.sum())))
        rows.append({"artboard": ab["name"], "checked": True, "alpha_iou": round(kit.iou(ga, ra), 4), "within_1px": round(tol, 4),
                     "de_mean": round(float(de[m].mean()), 2), "de_p95": round(float(np.percentile(de[m], 95)), 2),
                     "size_px": [int(got.shape[1]), int(got.shape[0])]})
        if len(sheet) < 24:
            sheet += [kit.over(g, bg), kit.over(r, bg)]
            labels += [f"{ab['name']} Illustrator", f"reference  within 1px {rows[-1]['within_1px']} dE {rows[-1]['de_mean']}"]
    (kit.VERIFY / f"{name}_import-check.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    if sheet:
        kit.contact(sheet, labels, kit.VERIFY / f"{name}_import-check.png", cols=2, width=420)
    bad = [r for r in rows if r.get("checked") and (r["within_1px"] < 0.995 or r["de_mean"] > 2.0)]
    print(f"{name}: {sum(r.get('checked', False) for r in rows)} artboards checked, {len(bad)} off:", bad[:6])
    unchecked = [r["artboard"] for r in rows if not r.get("checked")]
    if bad or unchecked:
        raise RuntimeError(f"{name}: export differs from the reference on {[r['artboard'] for r in bad]}; "
                           f"not checked (no PNG or no reference): {unchecked}")
    return rows


# ---------------------------------------------------------------- 01 Master Logo Suite

STATES = [
    ("FullColor-Light", dict(mark="ap-hero", recolor=None, text="AAP Partner Navy", accent="AAP Alliance Blue",
                             rule="AAP Ribbon Cyan", micro="AAP Alliance Blue", bg=None)),
    ("FullColor-Dark", dict(mark="ap-hero-dark", recolor=None, text="AAP Pure White", accent="AAP Ribbon Cyan",
                            rule="AAP Ribbon Cyan", micro="AAP Ribbon Cyan", bg="AAP Partner Navy")),
    ("Mono-Black", dict(mark="ap-mono", recolor="AAP Black", text="AAP Black", accent="AAP Black",
                        rule="AAP Black", micro="AAP Black", bg=None)),
    ("Mono-White", dict(mark="ap-mono", recolor="AAP Pure White", text="AAP Pure White", accent="AAP Pure White",
                        rule="AAP Pure White", micro="AAP Pure White", bg="AAP Alliance Blue")),
    # flat brand-colour versions: the one-colour mark in the palette, so every lockup also exists in solid inks
    # (pure spot in the Pantone master: screen print, promo goods, 2-3 colour offset)
    ("Flat-Light", dict(mark="ap-mono", recolor="AAP Alliance Blue", text="AAP Partner Navy", accent="AAP Alliance Blue",
                        rule="AAP Ribbon Cyan", micro=None, bg=None)),
    ("Flat-Dark", dict(mark="ap-mono", recolor="AAP Ribbon Cyan", text="AAP Pure White", accent="AAP Ribbon Cyan",
                       rule="AAP Ribbon Cyan", micro=None, bg="AAP Partner Navy")),
]


def mark(st, x, y, h=H):
    s = h / MH
    return svg_item(st["mark"], x - MB[0] * s, y - MB[1] * s, s, st["recolor"], "AAP mark")


def wordmark(st, size, x, baseline):
    return text_item(WM, "Bold", size, -11, x, baseline,
                     [(0, 9, st["text"]), (9, 11, st["accent"]), (11, 20, st["text"])], "wordmark")


def lk_horizontal(st):  # board 02 + original 04: mark beside ALLIANCE / AI PARTNERS, justified block
    s1 = 0.4353 * H
    s2, c1 = 0.7446 * s1, CAP * s1
    l1, l2 = ink("ALLIANCE", "Bold", s1, 6), ink("AI PARTNERS", "Bold", s2, 8)
    left = MWH + 0.5074 * c1
    b1 = (H - 2.1004 * c1) / 2 + c1
    b2 = b1 + 1.1004 * c1
    x1, x2 = left - l1[0], left - l2[0]
    return ([mark(st, 0, 0), text_item("ALLIANCE", "Bold", s1, 6, x1, b1, st["text"], "wordmark line 1"),
             text_item("AI PARTNERS", "Bold", s2, 8, x2, b2, [(0, 2, st["accent"]), (2, 11, st["text"])], "wordmark line 2")],
            [0, 0, max(x1 + l1[2], x2 + l2[2]), H])


def lk_stacked(st):  # original 14: mark centred above the one-line wordmark
    s = 0.2136 * H
    c, w = CAP * s, ink(WM, "Bold", s, -11)
    base = H + 1.0704 * c + c
    x = MWH / 2 - (w[0] + w[2]) / 2
    return [mark(st, 0, 0), wordmark(st, s, x, base)], [min(0, x + w[0]), 0, max(MWH, x + w[2]), base]


def lk_mark(st):
    return [mark(st, 0, 0)], [0, 0, MWH, H]


def lk_wordmark(st):  # Montserrat Bold, tracking -11 (median of the originals), metric kerning
    w = ink(WM, "Bold", 100, -11)
    return [wordmark(st, 100, -w[0], 0)], [0, w[1], w[2] - w[0], w[3]]


def lk_favicon(n, h):
    """Micro-mark: the silhouette without the interlace cuts, apex and baseline on whole pixel rows and the P stem
    on a pixel column. At 16 px the mark is drawn on the pixel grid instead (micro16_svg)."""
    def build(st):
        if n == 16:
            return [svg_item("ap-micro16", 0, 0, 1.0, st["micro"], "AAP micro-mark 16 px")], [0, 0, n, n]
        s = h / MH
        w, top, left = MW * s, (n - h) // 2, (n - MW * s) / 2
        stem = left + (P_STEM_X - MB[0]) * s
        if 0.25 <= left + round(stem) - stem and left + round(stem) - stem + w <= n - 0.25:
            left += round(stem) - stem
        return [svg_item("ap-micro", left - MB[0] * s, top - MB[1] * s, s, st["micro"], "AAP micro-mark")], [0, 0, n, n]
    return build


def xf_d(d, sx, sy, tx, ty):
    subs = kit.parse_d(d)
    t = lambda x, y: (x * sx + tx, y * sy + ty)
    for s in subs:
        s["start"] = t(*s["start"])
        s["segs"] = [("L",) + t(g[1], g[2]) if g[0] == "L" else ("C",) + t(g[1], g[2]) + t(g[3], g[4]) + t(g[5], g[6])
                     for g in s["segs"]]
    return kit.format_d(subs)


def micro16_svg():
    """The 16 px micro-mark on the pixel grid: the silhouette condensed to 14 x 10 px (1 px side margins, 3 px top and
    bottom), thresholded at half coverage so both counters stay open and every edge is crisp at 16 x 16 (the
    scaled-down vector left a 1 px A counter and grey haze). It is drawn as one outline with the counters as holes,
    not as per-row pixel runs: Illustrator's rasteriser bleeds a quarter pixel below edges two runs share, which at
    16 px half-filled the counters (fully, with anti-aliasing off); the single outline exports exactly either way."""
    w, h, top = 14, 10, 3
    sx, sy = w / MW, h / MH
    on = kit.raster([xf_d(HERO["silhouette_d"], sx, sy, (16 - w) / 2 - MB[0] * sx, top - MB[1] * sy)], 16, 16, ss=16) > 0.5
    ink = lambda x, y: 0 <= x < 16 and 0 <= y < 16 and on[y, x]
    out = {}  # boundary edges, clockwise round the ink (y down): corner -> next corners
    for y, x in np.argwhere(on).tolist():
        for nx, ny, a, b in ((x, y - 1, (x, y), (x + 1, y)), (x + 1, y, (x + 1, y), (x + 1, y + 1)),
                             (x, y + 1, (x + 1, y + 1), (x, y + 1)), (x - 1, y, (x, y + 1), (x, y))):
            if not ink(nx, ny):
                out.setdefault(a, []).append(b)
    loops = []
    while out:  # every corner has as many edges in as out, so each walk returns to its start
        start = p = next(iter(out))
        loop = [start]
        while True:
            q = out[p].pop()
            if not out[p]:
                del out[p]
            if q == start:
                break
            loop.append(q)
            p = q
        n = len(loop)  # keep the corners only
        c = [v for i, v in enumerate(loop)
             if (v[0] - loop[i - 1][0], v[1] - loop[i - 1][1]) != (loop[(i + 1) % n][0] - v[0], loop[(i + 1) % n][1] - v[1])]
        loops.append(f"M{c[0][0]} {c[0][1]}" + "".join(f"H{b[0]}" if b[1] == a[1] else f"V{b[1]}" for a, b in zip(c, c[1:])) + "Z")
    d = "".join(loops)
    assert ((kit.raster([d], 16, 16, ss=4) > 0.5) == on).all(), "micro-16 outline does not match its pixel mask"
    return kit.svg_doc(16, 16, f'<path id="ap-micro-16" d="{d}" fill="#000000"/>')


def check_favicon16(out, abs_):
    """The 16 px micro-mark must export as exactly its pixels, each fully on or off. The generic export check ignores
    alpha under 0.5, which is where rasteriser haze shows at this size."""
    m16 = (kit.raster([re.search(r' d="([^"]+)"', micro16_svg()).group(1)], 16, 16, ss=4) > 0.5) * 255
    for a in abs_:
        if "Favicon-16" in a["name"]:
            f = out / "PNG-Favicon" / f"AAP_{a['name']}.png"
            if not (np.asarray(Image.open(f).convert("RGBA"))[..., 3] == m16).all():
                raise RuntimeError(f"{f.name}: not the micro-mark's exact pixels (whole pixels only, alpha 0 or 255)")


def unify(svg, mark):
    """Artwork drawn from the unified palette: each measured colour becomes its palette token (palette.json stopMap:
    "light" or "dark" for the 3D mark's colourways, "graphics" for the Brand Graphics' illustration tones). Every master
    uses it; the Original Recreations keep the measured inks."""
    tok = {c["name"]: c["hex"] for c in BRAND["core"] + BRAND["shading"]}
    stops = {h.upper(): tok[t] for h, t in BRAND["stopMap"][mark].items()}
    out = re.sub(r"#[0-9A-Fa-f]{6}\b", lambda m: stops.get(m.group(0).upper(), m.group(0)), svg)
    stray = {h.upper() for h in re.findall(r"#[0-9A-Fa-f]{6}\b", out)} - set(tok.values())
    assert not stray, f"{mark}: colours outside the palette {sorted(stray)}"
    return out


def lift_dark(svg):
    """FullColor-Dark mark that holds up on slate as well as Partner Navy: shading tones darker than L* 50 are lifted
    (up to +14 L* for the darkest, nothing at L* 50 and above), hue and chroma kept, so the faces that sank into a
    dark background separate from it while the bright ribbon and legs stay as drawn."""
    names = tone_names()

    def lift(m):
        hx = m.group(2).upper()
        L, a, b = (float(v) for v in kit.srgb_to_lab(kit.hexrgb(hx)))
        if L >= 50:
            return m.group(0)
        L2 = L + 14 * min(1.0, (50 - L) / 30)
        new = kit.rgbhex(lab_to_srgb(L2, a, b))
        if hx in names:
            _NAMES.setdefault(new, names[hx] + " Lift")
        return f'{m.group(1)}"{new}"'
    return re.sub(r'(stop-color=|fill=)"(#[0-9A-Fa-f]{6})"', lift, svg)


def lab_to_srgb(L, a, b):
    """CIELAB (D65, as kit.srgb_to_lab) -> sRGB 0..255, clipped."""
    fy = (L + 16) / 116
    f = np.array([fy + a / 500, fy, fy - b / 200])
    xyz = np.where(f ** 3 > 216 / 24389, f ** 3, (116 * f - 16) / (24389 / 27)) * np.array([0.95047, 1.0, 1.08883])
    lin = np.linalg.solve(np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750],
                                    [0.0193339, 0.1191920, 0.9503041]]), xyz)
    lin = np.clip(lin, 0, 1)
    return np.where(lin <= 0.0031308, 12.92 * lin, 1.055 * lin ** (1 / 2.4) - 0.055) * 255


TAG_TR = 24  # tagline tracking (01 measured +23.9); Illustrator tracking is set in whole units throughout


def lk_htag(st):  # original 01: mark + wordmark + tagline, one shared left edge
    s = 0.2832 * H
    c, w = CAP * s, ink(WM, "Bold", s, -11)
    ts = 0.6066 * s
    t = ink(TAG, "Regular", ts, TAG_TR)
    left = MWH + 0.7425 * c
    b1 = (H - 2.1864 * c) / 2 + c
    b2 = b1 + 1.1864 * c
    x1, x2 = left - w[0], left - t[0]
    return ([mark(st, 0, 0), wordmark(st, s, x1, b1), text_item(TAG, "Regular", ts, TAG_TR, x2, b2, st["text"], "tagline")],
            [0, 0, max(x1 + w[2], x2 + t[2]), max(H, b2 + t[3])])


def lk_hdesc(st):  # original 13: mark + wordmark + cyan rule + descriptor justified to the wordmark
    s = 0.2832 * H
    c, w = CAP * s, ink(WM, "Bold", s, -11)
    ds = 0.7473 * s
    d0 = ink(DESC, "Medium", ds, 0)
    tr = round(((w[2] - w[0]) - (d0[2] - d0[0])) / ((len(DESC) - 1) * ds / 1000))  # justified to the wordmark
    d = ink(DESC, "Medium", ds, tr)
    left = MWH + 0.7425 * c
    b1 = (H - 3.0752 * c) / 2 + c
    b3 = b1 + 2.0752 * c
    x1, x3 = left - w[0], left - d[0]
    ry, rt = b1 + 0.6798 * c, 0.145 * c
    rule = {"type": "rect", "x": x1 + w[0], "y": ry - rt / 2, "w": w[2] - w[0], "h": rt, "fill": st["rule"], "name": "rule"}
    return ([mark(st, 0, 0), wordmark(st, s, x1, b1), rule,
             text_item(DESC, "Medium", ds, tr, x3, b3, st["text"], "descriptor")],
            [0, 0, max(x1 + w[2], x3 + d[2]), max(H, b3)])


def lk_stag(st):  # board 02 hero lockup: mark, wordmark and tagline centred, tagline sized and spaced as on the board
    s = 0.2136 * H
    c, w = CAP * s, ink(WM, "Bold", s, -11)
    ts = 0.5874 * s  # board: tagline 14.729 / wordmark 25.073
    t = ink(TAG, "Regular", ts, TAG_TR)
    b1 = H + 1.0704 * c + c
    b2 = b1 + 1.111 * c  # board: 19.49 / 17.55 cap
    x1, x2 = MWH / 2 - (w[0] + w[2]) / 2, MWH / 2 - (t[0] + t[2]) / 2
    return ([mark(st, 0, 0), wordmark(st, s, x1, b1), text_item(TAG, "Regular", ts, TAG_TR, x2, b2, st["text"], "tagline")],
            [min(0, x1 + w[0], x2 + t[0]), 0, max(MWH, x1 + w[2], x2 + t[2]), b2 + t[3]])


def lk_stacked2(st):  # original 09: mark above ALLIANCE AI / PARTNERS, centred, Bold / Bold
    runs = {r["id"]: r for r in jload(kit.FIT / "text-09.json")["runs"]}
    r1, r2 = runs["text-09-line1"], runs["text-09-line2"]
    m09 = jload(kit.FIT / "flat-09.json")["mark_bbox"]
    k = H / (m09[3] - m09[1])
    # one size and one tracking for both lines (09's raster fit differed by 1.9 % in cap height, which a master
    # should not carry): the mean of the two fits
    s1 = s2 = (r1["size"] + r2["size"]) / 2 * k
    trk = round((r1["tracking"] + r2["tracking"]) / 2)
    r1, r2 = dict(r1, tracking=trk), dict(r2, tracking=trk)
    l1, l2 = ink("ALLIANCE AI", "Bold", s1, r1["tracking"]), ink("PARTNERS", "Bold", s2, r2["tracking"])
    b1 = H + (r1["baseline"] - m09[3]) * k
    b2 = b1 + (r2["baseline"] - r1["baseline"]) * k
    x1, x2 = MWH / 2 - (l1[0] + l1[2]) / 2, MWH / 2 - (l2[0] + l2[2]) / 2
    return ([mark(st, 0, 0),
             text_item("ALLIANCE AI", "Bold", s1, r1["tracking"], x1, b1, [(0, 9, st["text"]), (9, 11, st["accent"])], "wordmark line 1"),
             text_item("PARTNERS", "Bold", s2, r2["tracking"], x2, b2, st["text"], "wordmark line 2")],
            [min(0, x1 + l1[0], x2 + l2[0]), 0, max(MWH, x1 + l1[2], x2 + l2[2]), b2])


SUITE_ROWS = [("Primary-Horizontal", lk_horizontal, None), ("Secondary-Stacked", lk_stacked, None),
              ("Logomark", lk_mark, None), ("Wordmark", lk_wordmark, CS * CAP * 100 / 0.1982),
              ("Favicon-32", lk_favicon(32, 17), 0), ("Favicon-16", lk_favicon(16, 9), 0),
              ("Horizontal-Tagline", lk_htag, None), ("Horizontal-Descriptor", lk_hdesc, None),
              ("Stacked-Tagline", lk_stag, None), ("Stacked-TwoLine", lk_stacked2, None)]


def suite_components():
    return {"ap-hero": prep("ap-hero", unify(text_of(kit.COMP / "ap-hero.svg"), "light")),
            "ap-hero-dark": prep("ap-hero-dark", unify(lift_dark((kit.COMP / "ap-hero-dark.svg").read_text(encoding="utf-8")), "dark")),
            "ap-mono": prep("ap-mono", kit.COMP / "ap-mono.svg"),
            "ap-micro": prep("ap-micro", kit.svg_doc(1024, 1024, f'<path id="ap-micro" d="{HERO["silhouette_d"]}" fill="#000000"/>')),
            "ap-micro16": prep("ap-micro16", micro16_svg())}


def suite_cells(row_filter=None):
    cells, fav = [], []
    for r, (lname, fn, pad) in enumerate(SUITE_ROWS, 1):
        if row_filter and lname not in row_filter:
            continue
        pad = CS * H if pad is None else pad
        built = [(sn, st) + fn(st) for sn, st in STATES if st["micro"] or not lname.startswith("Favicon")]
        bb = built[0][3]
        w, h = math.ceil(bb[2] - bb[0] + 2 * pad), math.ceil(bb[3] - bb[1] + 2 * pad)
        ox, oy = (w - (bb[2] - bb[0])) / 2 - bb[0], (h - (bb[3] - bb[1])) / 2 - bb[1]
        for sn, st, items, _ in built:
            cells.append((f"{r:02d}-{lname}_{sn}", w, h, st["bg"], [shift(it, ox, oy) for it in items]))
            if lname.startswith("Favicon"):
                fav.append(len(cells))
    return cells, fav


def suite():
    out = kit.KIT / "01_Master-Logo-Suite"
    comps = suite_components()
    cells, fav = suite_cells()
    abs_, y = [], 0
    for lname in [r[0] for r in SUITE_ROWS]:  # one row per lockup: its 6 states (4 for the favicons)
        row = [c for c in cells if c[0].split("_")[0].split("-", 1)[1] == lname]
        a, y = grid(row, len(row), y0=y)
        abs_ += a
    for a in abs_:
        a["group"] = True
    centre_layout(abs_)
    n = len(abs_)
    fav = [i + 1 for i, a in enumerate(abs_) if "Favicon" in a["name"]]
    scene = {"out": str(out / "AAP_Master-Logo-Suite.ai"), "components": comps, "artboards": abs_,
             "swatches": swatch_groups(comps.values()),
             "exports": [{"type": "png", "folder": str(out / "PNG"), "scale": 2, "transparent": True, "prefix": "AAP_",
                          "artboards": ranges(set(range(1, n + 1)) - set(fav))},
                         {"type": "png", "folder": str(out / "PNG-Favicon"), "scale": 1, "transparent": True,
                          "prefix": "AAP_", "artboards": ranges(fav)},
                         {"type": "svg", "folder": str(out / "SVG"), "transparent": True, "prefix": "AAP_",
                          "artboards": "1-%d" % n}]}
    render_scene("suite", scene)
    tidy_exports(out, "AAP-suite")
    check_favicon16(out, abs_)
    check_exports("suite", scene, out / "PNG", 2, sorted(set(range(1, n + 1)) - set(fav)))
    check_exports("suite-favicon", scene, out / "PNG-Favicon", 1, fav)
    return scene


def tidy_exports(out, idbase):
    """Export for Screens nests files by scale (PNG/2x, SVG/SVG); flatten those into PNG/ and SVG/, and make every
    SVG safe to inline next to the others on one web page: ids and url(#..) carry a file-unique prefix, gradient
    templates (xlink:href) are written out in full, the root gets width/height, and the Mono-Black files (whose paths
    relied on the SVG default fill) get an explicit fill="#000000" on the root for every path to inherit."""
    for sub in [p for p in out.iterdir() if p.is_dir() and p.name in ("PNG", "PNG-Favicon", "PNG-Icons", "SVG")]:
        for nested in [q for q in sub.iterdir() if q.is_dir()]:
            for f in nested.iterdir():
                f.replace(sub / f.name)
            nested.rmdir()
    for f in sorted((out / "SVG").glob("*.svg")):
        t = f.read_text(encoding="utf-8")
        pre = re.sub(r"[^a-z0-9]+", "-", f.stem.lower().replace("aap_", "")).strip("-")
        grads = {m.group(1): m.group(0) for m in re.finditer(r'<linearGradient id="([^"]+)"[^>]*>.*?</linearGradient>', t, re.S)}

        def inline(m):  # <linearGradient id=X x1.. xlink:href="#Y"/> -> full gradient with Y's units, transform and stops
            src = grads.get(m.group(2))
            if not src:
                return m.group(0)
            head = re.search(r"<linearGradient\b([^>]*)>", src).group(1)
            extra = "".join(f' {k}="{v}"' for k, v in re.findall(r'(gradientUnits|gradientTransform)="([^"]*)"', head)
                            if k + "=" not in m.group(1))
            stops = re.search(r">(.*)</linearGradient>", src, re.S).group(1)
            return f'<linearGradient{m.group(1)}{extra}>{stops}</linearGradient>'
        t = re.sub(r'<linearGradient\b([^>]*?)\s+xlink:href="#([^"]+)"\s*/>', inline, t)
        t = re.sub(r'\bid="([^"]+)"', lambda m: f'id="{pre}-{m.group(1)}"', t)
        t = re.sub(r"url\(#([^)]+)\)", lambda m: f"url(#{pre}-{m.group(1)})", t)
        t = re.sub(r'href="#([^"]+)"', lambda m: f'href="#{pre}-{m.group(1)}"', t)
        vb = re.search(r'viewBox="([^"]+)"', t)
        if vb and " width=" not in t[:t.index(">", t.index("<svg"))]:
            w, h = vb.group(1).split()[2:4]
            t = t.replace("<svg ", f'<svg width="{w}" height="{h}" ', 1)
        if "Mono-Black" in f.stem and ' fill="#000000"' not in t[:t.index(">", t.index("<svg"))]:
            t = t.replace("<svg ", '<svg fill="#000000" ', 1)
        f.write_text(t, encoding="utf-8")


# ---------------------------------------------------------------- 02 Original Recreations

def border_hex(rgb):
    m = np.ones(rgb.shape[:2], bool)
    m[6:-6, 6:-6] = False
    return kit.rgbhex(np.median(rgb[m].astype(float), 0))


def placement(key):
    return jload(kit.FIT / "placements.json")[key]


def hero_layer(oid, fallback):
    """The per-original AP rebuild if its agent delivered one (source space), else the placed master."""
    rec = kit.COMP / "rec" / f"hero-{oid}.svg"
    if rec.exists():
        return L("mark", rec)
    p = placement(fallback)
    return L("mark", kit.COMP / p["component"], p["s"], p["tx"], p["ty"])


def text_layer(oid):
    """An original's type as Montserrat outlines from its fit (fit/text-<id>.json). Each run uses the per-character
    spacing the fit measured (the AI-made letter spacing is irregular) wherever that matched the original better than
    one tracking value; colours the fit had snapped to the palette at dE 2-4 go back to the measured ink."""
    d = jload(kit.FIT / f"text-{oid}.json")
    gw = kit.glyphs()["weights"]
    body = []
    for run in d["runs"]:
        style, size, string = run["style"], run["size"], run["string"]
        k, fs = size / 100, run.get("faithful_spacing")
        if fs and fs.get("iou", 0) > run["iou"]:
            cum = np.concatenate([[0.0], np.cumsum(fs["tracking_per_char"])])
            pen = lambda idx, x0=fs["x"], cum=cum: x0 + cum[idx] / 1000 * size
        else:
            pen = lambda idx, x0=run["x"], tr=run["tracking"]: x0 + idx * tr / 1000 * size
        col = {}
        for c in run["colors"]:
            hx = c["hex"].upper()
            if hx in CORE_HEX and fidelity(c["measured_hex"]) != hx:
                hx = fidelity(c["measured_hex"])
            col.update({i: hx for i in range(c["start"], c["end"])})
        for ch, idx, dx in gw[style]["strings"][string]:
            dd = kit.transform_d(gw[style]["chars"][ch]["d"], k, dx * k + pen(idx), run["baseline"])
            body.append(f'<path id="{run["id"]}-{idx:02d}-{ch}" d="{dd}" fill="{col[idx]}" fill-rule="evenodd"/>')
    for r in d.get("rules", []):
        body.append(f'<path id="{r["id"]}" d="M{r["x0"]} {r["top"]} L{r["x1"]} {r["top"]} L{r["x1"]} {r["bottom"]} '
                    f'L{r["x0"]} {r["bottom"]} Z" fill="{fidelity(r["measured_hex"])}"/>')
    return L("text", kit.svg_doc(*d["image_size"], "\n".join(body)))


def flat_layer(oid):
    cols = jload(kit.FIT / f"flat-{oid}.json")["colors"]
    swap = {c["snapped"]: fidelity(c["measured"]) for k, c in cols.items()
            if isinstance(c, dict) and k != "background" and "snapped" in c}
    return L("mark", kit.COMP / f"flat-{oid}.svg", strip=[r'<rect id="bg"[^>]*/>'], recolor=swap)


def bird_layer(oid):
    src = kit.COMP / ("bird.svg" if oid == "15" else f"bird-{oid}.svg")
    if oid == "15":  # the master bird snapped five wing stops to Alliance Blue at dE 4; 15 measures #2463F8 there
        return L("mark", src, recolor={CORE["AAP Alliance Blue"]: "#2566F7"})
    if (kit.FIT / f"bird-{oid}.json").exists():
        return L("mark", src)
    m = jload(kit.FIT / "bird-placements.json")[oid]["matrix"]  # master-space fallback (rotation < 0.6 deg ignored)
    return L("mark", src, math.hypot(m[0], m[1]), m[4], m[5])


def keyline(p, width_px):
    """White outline around the placed mark (17 cuts one into the shield frame), drawn in source space."""
    sx, sy, tx, ty = p["affine"]
    t = kit.svg_doc(1024, 1024, f'<path id="keyline" d="{HERO["silhouette_d"]}" fill="#FFFFFF" stroke="#FFFFFF" '
                                f'stroke-width="{width_px * 2 / (sx + sy):.3f}" stroke-linejoin="miter" stroke-miterlimit="4"/>')
    return L("keyline", t, (sx, sy), tx, ty)


def white_gap_17():
    """17 leaves a clean white channel between the A's left foot and the upper banner bar, where the frame's inner
    side bands end; trace that white from the original (only pixels white there, above the bar's top edge)."""
    rgb = kit.load("17")
    bar_top = jload(kit.FIT / "shield-layout.json")["banner"]["upper_bar_top_inside_y"]
    m = ~kit.bg_mask(rgb, "#FFFFFF", 6.0)
    box = np.zeros(m.shape, bool)
    box[440:int(bar_top), 396:492] = True
    ds = kit.trace_mask(m & box, upscale=4, blur=0.4, noise=2)
    return L("gap", kit.svg_doc(1376, 768, "".join(f'<path d="{d}" fill="#FFFFFF"/>' for d in ds)))


def rec_layers(oid):
    if oid in ("03", "07", "09", "10", "11", "12", "16"):
        return [flat_layer(oid)] + ([text_layer(oid)] if (kit.FIT / f"text-{oid}.svg").exists() else [])
    if oid in ("05", "08", "15"):
        return [bird_layer(oid)] + ([text_layer(oid)] if oid != "15" else [])
    if oid == "06":
        return [L("mark", kit.COMP / "ap-hero.svg")]
    if oid == "04":
        rec = kit.COMP / "rec" / "hero-04.svg"
        p = placement("hero-dark@04")
        return [L("mark", rec) if rec.exists() else L("mark", kit.COMP / "ap-hero-dark.svg", p["s"], p["tx"], p["ty"]),
                text_layer("04")]
    if oid in ("01", "13", "14"):
        return [hero_layer(oid, f"hero@{oid}"), text_layer(oid)]
    if oid == "17":
        p = placement("hero@17")
        return [L("frame", kit.COMP / "shield-frame.svg"), keyline(p, 20.0), white_gap_17(),
                L("mark", kit.COMP / p["component"], p["s"], p["tx"], p["ty"]), text_layer("17")]
    if oid == "02":  # its background goes to the Background layer like every other recreation's
        lay = [L("board", kit.COMP / "board-02.svg", strip=[r'<g id="slots".*?</g>', r'<rect id="background"[^>]*/>']),
               L("wave", kit.COMP / "graphic-wave.svg"), L("mesh", kit.COMP / "graphic-datamesh.svg")]
        for slot in ("slot-hero-stacked", "slot-hero-horizontal", "slot-clearspace-mark", "slot-tile-twotone", "slot-tile-flat"):
            p = placement(slot)
            lay.append(L(slot, kit.COMP / p["component"], p["s"], p["tx"], p["ty"]))
        return lay
    raise KeyError(oid)


def rec_bg(oid, rgb):
    f, h = kit.FIT / f"flat-{oid}.json", kit.COMP / "rec" / f"hero-{oid}.json"
    if f.exists():
        return fidelity(jload(f)["colors"]["background"]["measured"])
    if h.exists() and "background_measured" in jload(h):  # measured over the whole field, away from mark and glow
        return fidelity(jload(h)["background_measured"])
    return fidelity(border_hex(rgb))


def recreations(ai=True):
    out = kit.KIT / "02_Original-Recreations"
    comps, cells, report, sheet, labels = {}, [], {}, [], []
    for oid in sorted(kit.ORIGINALS):
        rgb = kit.load(oid)
        h, w = rgb.shape[:2]
        svg = compose(w, h, rec_layers(oid))
        bg = rec_bg(oid, rgb)
        key = f"rec-{oid}"
        comps[key] = prep(key, svg)
        ren = kit.over(kit.render_svg(svg), bg or "#FFFFFF")
        m = kit.compare(rgb, ren)
        fo, fr = kit.bg_mask(rgb, bg or "#F5F9FC", 18.0), kit.bg_mask(ren, bg or "#F5F9FC", 18.0)
        fg = kit.compare(rgb, ren, fo | fr)
        report[oid] = {"bg": bg, "de_mean": m["de_mean"], "de_p95": m["de_p95"], "fg_iou": round(kit.iou(fo, fr), 4),
                       "fg_de_mean": fg["de_mean"], "fg_de_p95": fg["de_p95"]}
        kit.diff_sheet(rgb, ren, kit.VERIFY / f"rec-{oid}_diff.png", m["de_map"],
                       f"rec-{oid} fg IoU {report[oid]['fg_iou']} dE {m['de_mean']}/{m['de_p95']}")
        sheet += [rgb, ren]
        labels += [f"{oid} original", f"{oid} vector  IoU {report[oid]['fg_iou']}  dE {m['de_mean']}"]
        print(oid, report[oid], flush=True)
        cells.append((f"Recreation-{oid}", w, h, bg, [svg_item(key, 0, 0, 1.0, name=f"recreation {oid}")]))
    (kit.VERIFY / "recreations.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    kit.contact(sheet, labels, kit.VERIFY / "recreations_sheet.png", cols=4, width=300)
    # one swatch group per original (a tone shared by several is listed with the first), so a recreation can be
    # moved onto the exact palette by editing its own group
    flat = swatch_groups(comps.values(), [c[3] for c in cells if c[3]])
    tones = {c["hex"]: c for g in flat[1:] for c in g["colors"]}
    groups, seen = [flat[0]], set()
    for oid, (key, path), cell in zip(sorted(kit.ORIGINALS), comps.items(), cells):
        hx = {h.upper() for h in HEX_RE.findall(Path(path).read_text(encoding="utf-8"))} | ({cell[3]} if cell[3] else set())
        mine = sorted((tones[h] for h in hx if h in tones and h not in seen), key=lambda c: c["name"])
        seen |= {c["hex"] for c in mine}
        if mine:
            groups.append({"group": f"AAP Rec {oid}", "colors": mine})
    cells = [(n, w, h, hex_swatch(groups, bg) if bg else None, items) for n, w, h, bg, items in cells]
    abs_, _ = grid(cells, 4, gut=120)
    centre_layout(abs_)
    n = len(abs_)
    scene = {"out": str(out / "AAP_Original-Recreations.ai"), "components": comps, "artboards": abs_, "swatches": groups,
             "keepBackground": True,
             "exports": [{"type": "png", "folder": str(out / "PNG"), "scale": 1, "transparent": False, "prefix": "AAP_",
                          "artboards": "1-%d" % n},
                         {"type": "svg", "folder": str(out / "SVG"), "transparent": False, "prefix": "AAP_", "artboards": "1-%d" % n}]}
    if ai:
        render_scene("recreations", scene)
        tidy_exports(out, "AAP-rec")
        check_exports("recreations", scene, out / "PNG", 1, range(1, n + 1), bg="#FFFFFF", with_bg=True)
    return scene


# ---------------------------------------------------------------- 03 Brand Graphics

ICONS = ["ai-strategy", "machine-learning", "automation", "data-analytics", "partnership", "security-governance",
         "growth", "cloud-integration", "advisory", "training-enablement", "research-insights", "launch"]
PATTERNS = [("datamesh", "Data Mesh"), ("halftone", "Halftone"), ("ap-monogram", "AP Monogram"),
            ("facets", "Facets"), ("ribbon-lines", "Ribbon Lines")]


def paths_bbox(svg):
    return bbox([d for d, a in kit.parse_svg_paths(text_of(svg)) if a.get("fill", "none") != "none"])


def art_bbox(svg):
    """Bounds of every painted path and rect in an SVG."""
    t = text_of(svg)
    boxes = [paths_bbox(t)] if any(a.get("fill", "none") != "none" for _, a in kit.parse_svg_paths(t)) else []
    for m in re.finditer(r"<rect\b([^>]*)/?>", t):
        a = dict(re.findall(r'([\w-]+)="([^"]*)"', m.group(1)))
        if a.get("id") in ("aap-ref", "bg") or a.get("fill", "#") == "none" or "width" not in a:
            continue
        x, y = float(a.get("x", 0)), float(a.get("y", 0))
        boxes.append([x, y, x + float(a["width"]), y + float(a["height"])])
    b = np.array(boxes)
    return [float(b[:, 0].min()), float(b[:, 1].min()), float(b[:, 2].max()), float(b[:, 3].max())]


def span_at(pts, y):
    """Width of a closed polygon at height y (outermost crossings)."""
    xs = []
    for (x0, y0), (x1, y1) in zip(pts, np.roll(pts, -1, 0)):
        if (y0 - y) * (y1 - y) <= 0 and y0 != y1:
            xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
    return max(xs) - min(xs) if len(xs) >= 2 else 0.0


def text_svg(w, h, string, style, size, tracking, x, baseline, spans):
    """Montserrat outlines (exported from Illustrator, so identical to its own) as an SVG; spans [(a, b, hex)]."""
    lay = kit.glyphs()["weights"][style]["strings"][string]
    col = {i: hx for a, b, hx in spans for i in range(a, b)}
    ds = kit.text_paths(string, style, size, tracking, x, baseline)
    return kit.svg_doc(w, h, "".join(f'<path id="{string[g[1]]}-{g[1]:02d}" d="{d}" fill="{col[g[1]]}"/>' for d, g in zip(ds, lay)))


def monogram_tile():
    """The AP-monogram tile with the master one-colour mark in place of the earlier trace of original 12."""
    t = (kit.COMP / "pattern-ap-monogram-tile.svg").read_text(encoding="utf-8")
    md, attrs = kit.parse_svg_paths((kit.COMP / "ap-mono.svg").read_text(encoding="utf-8"))[0]
    mb = bbox([md])

    def swap(m):
        b = bbox([re.search(r'\bd="([^"]+)"', m.group(0)).group(1)])
        s = (b[3] - b[1]) / (mb[3] - mb[1])
        tx = b[0] - mb[0] * s + ((b[2] - b[0]) - (mb[2] - mb[0]) * s) / 2
        el = re.sub(r'\bd="[^"]+"', f'd="{kit.transform_d(md, s, tx, b[1] - mb[1] * s)}"', m.group(0))
        return re.sub(r'fill-rule="[^"]*"', f'fill-rule="{attrs.get("fill-rule", "nonzero")}"', el)
    return re.sub(r'<path id="ap-monogram-\d+"[^>]*/>', swap, t)


def disc(cx, cy, r, fill=None, stroke=None, sw=1, name="circle"):
    return {"type": "ellipse", "x": cx - r, "y": cy - r, "w": 2 * r, "h": 2 * r, "fill": fill, "stroke": stroke,
            "strokeWidth": sw, "name": name}


def centred(string, style, size, tracking, cx, baseline, color, name):
    """Left-aligned text placed so its ink is centred on cx (tracking after the last glyph does not shift it)."""
    w = ink(string, style, size, tracking)
    return text_item(string, style, size, tracking, cx - (w[0] + w[2]) / 2, baseline, color, name)


def badge_cells(suite_scene, comps):
    cells = []
    # Shield badge (from original 17): master AP in the beveled frame with its white keyline, palette banner text
    p = placement("hero@17")
    lay = jload(kit.FIT / "shield-layout.json")
    bt = lay["banner_text"]
    size = bt["cap_height"] / CAP
    w0 = ink(WM, "Bold", size, 0)
    tr = round((bt["width"] - (w0[2] - w0[0])) / ((len(WM) - 1) * size / 1000))  # Bold, tracked to the measured width
    wi = ink(WM, "Bold", size, tr)
    axis = lay["symmetry_axis_x"]
    frame = kit.COMP / "shield-frame.svg"
    # 17's lettering overhangs the white banner panel (invisible on white, cut off on any darker background): the master
    # badge sets it inside the panel with 6 px clearance at the baseline and at cap height
    fb_d = [d for d, a in kit.parse_svg_paths(frame.read_text(encoding="utf-8")) if a.get("id", "").endswith("field-banner")]
    if fb_d:
        pts = np.array([p for poly in kit.flatten(kit.parse_d(fb_d[0])) for p in poly])
        avail = min(span_at(pts, y) for y in (bt["baseline_y"], bt["baseline_y"] - bt["cap_height"])) - 12
        if wi[2] - wi[0] > avail:
            size *= avail / (wi[2] - wi[0])
            wi = ink(WM, "Bold", size, tr)
    base = bt["baseline_y"] - (bt["cap_height"] - CAP * size) / 2  # keep the type centred on the band
    banner = text_svg(1376, 768, WM, "Bold", size, tr, axis - (wi[0] + wi[2]) / 2, base,
                      [(0, 9, CORE["AAP Partner Navy"]), (9, 11, CORE["AAP Alliance Blue"]), (11, 20, CORE["AAP Partner Navy"])])
    sx, sy, tx, ty = p["affine"]  # where 17 draws its mark; the badge keeps the master's own colours
    svg = compose(1376, 768, [L("frame", unify(text_of(frame), "graphics")), keyline(p, 20.0), L("mark", unify(text_of(kit.COMP / "ap-hero.svg"), "light"), (sx, sy), tx, ty),
                              L("banner", banner)])
    fb = paths_bbox(frame)
    comps["badge-shield"] = prep("badge-shield", svg)
    m = 48
    cells.append(("Badge-Shield", math.ceil(fb[2] - fb[0] + 2 * m), math.ceil(fb[3] - fb[1] + 2 * m), None,
                  [svg_item("badge-shield", m - fb[0], m - fb[1], 1.0, name="shield badge")]))

    # Circular seal: the tagline set on a circle with Type on a Path. The renderer closes the ring by measuring its own
    # outlines (seam = the string's own bullet-to-word gap) and centres the name on 12 o'clock; the baseline radius puts
    # the cap band in the middle of the channel between the two rings (236 and 296)
    c, size = 320, 30
    rt = (236 + 296) / 2 - CAP * size / 2
    ds0 = kit.text_paths(SEAL + " A", "Bold", size, 0)  # sentinel A where the ring meets its start again
    b_last, b_sent = bbox([ds0[-2]]), bbox([ds0[-1]])
    seam0 = (b_sent[0] + b_sent[2]) / 2 - (b_last[0] + b_last[2]) / 2  # bullet centre to A centre, tracking 0
    adv0 = (b_sent[0] - kit.glyphs()["weights"]["Bold"]["chars"]["A"]["left"] * size / 100)  # sentinel pen position
    tr = round((2 * math.pi * rt - adv0) / ((len(SEAL) + 1) * size / 1000), 1)  # first guess; the renderer refines it
    name_ink = bbox(kit.text_paths(SEAL + " A", "Bold", size, tr)[:18])  # the 18 glyphs of ALLIANCE AI PARTNERS
    start = -math.degrees((name_ink[0] + name_ink[2]) / 2 / rt)
    s = 150 / MH
    cells.append(("Badge-Seal", 640, 640, None, [
        disc(c, c, 310, "AAP Partner Navy", name="seal disc"), disc(c, c, 296, None, "AAP Ribbon Cyan", 2, "seal outer ring"),
        disc(c, c, 236, None, "AAP Ribbon Cyan", 3, "seal inner ring"),
        {"type": "pathtext", "text": SEAL, "font": "Montserrat-Bold", "size": size, "tracking": tr,
         "swatch": "AAP Pure White", "cx": c, "cy": c, "r": rt, "startAngle": start, "name": "seal text",
         "ring": {"seam0": seam0, "name": [0, 17]}},
        svg_item("ap-hero-dark", c - (MB[0] + MW / 2) * s, c - (MB[1] + MH / 2) * s, s, name="AAP mark")]))

    # Starburst certification badge
    n, R, r = 36, 310, 286
    pts = [(c + (R if k % 2 == 0 else r) * math.sin(math.pi * k / n), c - (R if k % 2 == 0 else r) * math.cos(math.pi * k / n))
           for k in range(2 * n)]
    comps["starburst"] = prep("starburst", kit.svg_doc(640, 640, '<path id="starburst" d="M' + " L".join(
        f"{x:.3f} {y:.3f}" for x, y in pts) + f' Z" fill="{CORE["AAP Alliance Blue"]}"/>'))
    s = 104 / MH
    # the block (mark, CERTIFIED, AI PARTNER) is centred on the disc; Bold, the brand's headline weight
    top, b1, b2 = 0.0, 104 + 54 + CAP * 62, 104 + 54 + CAP * 62 + 52
    dy = c - (top + b2) / 2
    cells.append(("Badge-Starburst", 640, 640, None, [
        svg_item("starburst", 0, 0, 1.0, name="starburst"), disc(c, c, 262, "AAP Partner Navy", name="badge disc"),
        disc(c, c, 244, None, "AAP Ribbon Cyan", 3, "badge ring"),
        svg_item("ap-hero-dark", c - (MB[0] + MW / 2) * s, dy + top - MB[1] * s, s, name="AAP mark"),
        centred("CERTIFIED", "Bold", 62, 20, c, dy + b1, "AAP Pure White", "CERTIFIED"),
        centred("AI PARTNER", "Bold", 34, 220, c, dy + b2, "AAP Ribbon Cyan", "AI PARTNER")]))

    # Die-cut sticker: navy pill with 9 pt bleed past the CutContour die line (spot, overprint), dark lockup inside
    ab = next(a for a in suite_scene["artboards"] if a["name"] == "01-Primary-Horizontal_FullColor-Dark")
    comps["sticker-lockup"] = prep("sticker-lockup", expected_svg(suite_scene, ab, suite_scene["swatches"]))
    aw, ah = ab["rect"][2], ab["rect"][3]
    s = 676 / (aw - 2 * CS * H)
    cells.append(("Sticker-DieCut", 860, 440, None, [  # 9 pt (3.2 mm) bleed beyond the die line
        {"type": "rect", "x": 13, "y": 13, "w": 834, "h": 414, "r": 207, "fill": "AAP Partner Navy", "name": "sticker art + bleed"},
        svg_item("sticker-lockup", 430 - aw * s / 2, 220 - ah * s / 2, s, name="lockup"),
        {"type": "rect", "x": 22, "y": 22, "w": 816, "h": 396, "r": 198, "stroke": "CutContour", "strokeWidth": 0.5,
         "overprint": True, "name": "CutContour die line", "layer": "CutContour"}]))
    return cells


def graphics(suite_scene=None):
    out = kit.KIT / "03_Brand-Graphics"
    suite_scene = suite_scene or jload(SCENES / "suite.json")
    comps = dict(suite_components())
    cells, rows = [], {}

    # Icons: overview sheet (duotone, mono and dark rows), then every icon on its own 48 pt grid artboard
    titles = {"ai-strategy": "AI Strategy", "security-governance": "Security & Governance", "data-analytics": "Data & Analytics",
              "training-enablement": "Training & Enablement", "research-insights": "Research & Insights"}
    pitch, ow = 184, 48 + 12 * 184
    ov = [{"type": "rect", "x": 0, "y": 0, "w": ow, "h": 232, "fill": "AAP Daylight", "name": "duotone panel"},
          {"type": "rect", "x": 0, "y": 232, "w": ow, "h": 232, "fill": "AAP Pure White", "name": "mono panel"},
          {"type": "rect", "x": 0, "y": 464, "w": ow, "h": 232, "fill": "AAP Partner Navy", "name": "dark panel"}]
    for k, slug in enumerate(ICONS):
        for v, src in (("duo", f"icon-{slug}.svg"), ("mono", f"icon-{slug}-mono.svg")):
            comps[f"icon-{slug}-{v}"] = prep(f"icon-{slug}-{v}", kit.COMP / "icons" / src)
        comps[f"icon-{slug}-dark"] = prep(f"icon-{slug}-dark", kit.COMP / "icons" / f"icon-{slug}.svg",
                                          recolor={CORE["AAP Alliance Blue"]: CORE["AAP Pure White"]})
        x = 48 + k * pitch + (pitch - 96) / 2
        label = titles.get(slug, slug.replace("-", " ").title())
        for row, (v, col) in enumerate((("duo", "AAP Partner Navy"), ("mono", "AAP Partner Navy"), ("dark", "AAP Pure White"))):
            ov += [svg_item(f"icon-{slug}-{v}", x, 48 + row * 232, 2.0, name=f"{slug} {v}"),
                   {**text_item(label, "Medium", 11, 0, x + 48, 176 + row * 232, col, "label"), "align": "center", "live": False}]
    cells.append(("01-Icons_Overview", ow, 696, None, ov))
    for v, bg in (("Duotone", None), ("Mono", None), ("Dark", "AAP Partner Navy")):
        for slug in ICONS:
            key = f"icon-{slug}-" + {"Duotone": "duo", "Mono": "mono", "Dark": "dark"}[v]
            cells.append((f"Icon-{slug}_{v}", 48, 48, bg, [svg_item(key, 0, 0, 1.0, name=slug)]))
    rows["icons"] = len(cells)

    # Seamless patterns: the master tile on its own artboard, and a preview filled with the pattern swatch. The renderer
    # makes each swatch from its tile's art (Object > Pattern > Make), so the pattern's colours are the brand swatches.
    pats = []
    for slug, title in PATTERNS:
        tile = monogram_tile() if slug == "ap-monogram" else (kit.COMP / f"pattern-{slug}-tile.svg").read_text(encoding="utf-8")
        if slug == "datamesh":  # a flat field (the tile's own edge-to-centre gradient repeated as stripes every 240 pt)
            tile = re.sub(r'(<rect id="bg"[^>]*fill=")url\([^)]*\)"', r'\g<1>#082348"', tile)
        if slug == "ap-monogram":  # tone-on-tone, one step lighter so it survives uncoated stock and projection
            tile = tile.replace("#1B2C48", "#22385C")
        comps[f"tile-{slug}"] = prep(f"tile-{slug}", unify(tile, "graphics"))
        pats.append({"name": "AAP Pattern " + title, "tile": f"Pattern-{title.replace(' ', '-')}_Tile", "item": f"{title} tile"})
        cells.append((f"Pattern-{title.replace(' ', '-')}_Tile", 240, 240, None, [svg_item(f"tile-{slug}", 0, 0, 1.0, name=f"{title} tile")]))
    for slug, title in PATTERNS:
        cells.append((f"Pattern-{title.replace(' ', '-')}_Swatch", 720, 405, None,
                      [{"type": "rect", "x": 0, "y": 0, "w": 720, "h": 405, "pattern": "AAP Pattern " + title,
                        "name": f"{title} swatch preview"}]))

    # Decorative graphics from the brand board: the ribbon wave master and the data mesh panel (x4)
    comps["wave"] = prep("wave", unify(text_of(kit.COMP / "graphic-wave-master.svg"), "graphics"))
    comps["mesh"] = prep("mesh", unify(text_of(kit.COMP / "graphic-datamesh.svg"), "graphics"))
    wb = art_bbox(kit.COMP / "graphic-wave-master.svg")  # the wave with its glow, 48 pt clear on every side
    cells.append(("Graphic-Wave", math.ceil(wb[2] - wb[0] + 96), math.ceil(wb[3] - wb[1] + 96), "AAP Daylight",
                  [svg_item("wave", 48 - wb[0], 48 - wb[1], 1.0, name="ribbon wave")]))
    mb = art_bbox(kit.COMP / "graphic-datamesh.svg")  # the panel fills its artboard exactly
    cells.append(("Graphic-DataMesh", round((mb[2] - mb[0]) * 4), round((mb[3] - mb[1]) * 4), None,
                  [svg_item("mesh", -mb[0] * 4, -mb[1] * 4, 4.0, name="data mesh")]))

    cells += badge_cells(suite_scene, comps)

    # Mascot: the faceted swallow, full colour and one-colour
    comps["bird"] = prep("bird", unify(text_of(kit.COMP / "bird.svg"), "graphics"))
    comps["bird-mono"] = prep("bird-mono", unify(text_of(kit.COMP / "bird-mono.svg"), "graphics"))
    bb = paths_bbox(kit.COMP / "bird.svg")
    bw, bh = math.ceil(bb[2] - bb[0] + 96), math.ceil(bb[3] - bb[1] + 96)
    for v, comp, rc, bg in (("FullColor", "bird", None, None), ("Mono-Black", "bird-mono", "AAP Black", None),
                            ("Mono-White", "bird-mono", "AAP Pure White", "AAP Partner Navy")):
        cells.append((f"Mascot-Swallow_{v}", bw, bh, bg, [svg_item(comp, 48 - bb[0], 48 - bb[1], 1.0, rc, "swallow")]))

    abs_ = []
    y = 0
    for group in (cells[:1], cells[1:37], cells[37:47], cells[47:49], cells[49:53], cells[53:]):
        a, y = grid(group, 12 if len(group) == 36 else 5, gut=48 if len(group) == 36 else GUT, y0=y)
        abs_ += a
    centre_layout(abs_)
    n = len(abs_)
    icon_idx = set(range(2, 38))
    spots = [{"name": "CutContour", "hex": "#FF00FF", "spotCMYK": [0, 100, 0, 0]}]
    swatches = swatch_groups(comps.values(), spots=spots)
    stray = [c["hex"] for g in swatches if g["group"] == "AAP Supporting Tones" for c in g["colors"]]
    assert not stray, f"Brand Graphics: colours outside the palette {stray}"  # palette.json stopMap.graphics
    scene = {"out": str(out / "AAP_Brand-Graphics.ai"), "components": comps, "artboards": abs_,
             "swatches": swatches, "patterns": pats,
             "exports": [{"type": "png", "folder": str(out / "PNG"), "scale": 2, "transparent": True, "prefix": "AAP_",
                          "artboards": ranges(set(range(1, n + 1)) - icon_idx), "hideLayers": ["CutContour"]},
                         {"type": "png", "folder": str(out / "PNG-Icons"), "scale": 4, "transparent": True, "prefix": "AAP_",
                          "artboards": ranges(icon_idx)},
                         {"type": "svg", "folder": str(out / "SVG"), "transparent": True, "prefix": "AAP_", "artboards": "1-%d" % n,
                          "hideLayers": ["CutContour"]}]}
    render_scene("graphics", scene)
    tidy_exports(out, "AAP-graphics")
    check_exports("graphics", scene, out / "PNG-Icons", 4, sorted(icon_idx))
    return scene


# ---------------------------------------------------------------- 04 Print masters

SPOT_INKS = ("Alliance Blue", "Ribbon Cyan", "Partner Navy")  # the inks the logos actually print; white is paper


PROFILE = match.PROFILES[match.MASTER][0]  # Coated GRACoL 2006 (ISO 12647-2:2004)
PROFILE_ID = "CGATS TR 006"                # its characterization in the ICC registry


def perceptual_cmyk(hex_):
    xf = getattr(perceptual_cmyk, "xf", None)
    if xf is None:
        from PIL import ImageCms
        xf = perceptual_cmyk.xf = ImageCms.buildTransform(
            ImageCms.createProfile("sRGB"), ImageCms.getOpenProfile(str(match.PROFILE_DIR / match.PROFILES[match.MASTER][1])),
            "RGB", "CMYK", ImageCms.Intent.PERCEPTUAL, ImageCms.Flags.BLACKPOINTCOMPENSATION)
    from PIL import ImageCms
    px = ImageCms.applyTransform(Image.new("RGB", (1, 1), tuple(int(v) for v in kit.hexrgb(hex_))), xf).getpixel((0, 0))
    return [int(round(v / 2.55)) for v in px]


def print_config(scene_name="suite"):
    """Per-swatch print builds on Coated GRACoL 2006: core colours from print-colors.json, shading tones through the
    profile (relative colorimetric + BPC; any pair that would print within dE2000 1 of each other although it is more
    than 2 apart on screen is re-separated with perceptual intent, which keeps the 3D mark's facets apart). The three
    logo inks also get their Pantone spot (coated, uncoated) with an explicit alternate built from the ink's own colour."""
    pc = jload(kit.BUILD / "print-colors.json")
    proc = {s["name"]: s["cmyk"] for s in pc["illustrator_swatches"] if s.get("type") == "global process"}
    spot = {(s["brand_color"], s["name"][-1]): s for s in pc["illustrator_swatches"] if s.get("type") == "spot"}
    sw = {}
    for g in jload(SCENES / f"{scene_name}.json")["swatches"]:
        for c in g["colors"]:
            if c.get("spotCMYK"):
                continue  # production spots (CutContour) stay as they are
            n, brand = c["name"], c["name"][4:]
            cmyk = [0, 0, 0, 100] if n == "AAP Black" else proc.get(n) or match.cmyk(c["hex"], match.MASTER)["clean"]
            spots = None
            if n in CORE and brand in SPOT_INKS:
                spots = {side: {"name": spot[(brand, side)]["name"],
                                "cmyk": match.cmyk(spot[(brand, side)]["hex_preview"], match.MASTER)["clean"]} for side in "CU"}
            sw[n] = {"hex": c["hex"], "cmyk": [int(v) for v in cmyk], "spots": spots}
    tones = [n for n in sw if n not in CORE]
    lab = {n: match.lab50(sw[n]["hex"]) for n in tones}
    for _ in range(2):
        prt = {n: match.cmyk_lab(sw[n]["cmyk"], match.MASTER) for n in tones}
        clash = {n for a in tones for b in tones if a < b and match.de(lab[a], lab[b]) > 2 and match.de(prt[a], prt[b]) < 1 for n in (a, b)}
        for n in clash:
            sw[n]["cmyk"], sw[n]["intent"] = perceptual_cmyk(sw[n]["hex"]), "perceptual"
    return sw


def write_output_intent(pdf):
    """Illustrator cannot be told the master's printing condition by script (it wrote SWOP's identifier and no
    profile), so the PDF/X-4 output intent is written here: Coated GRACoL 2006 embedded, CGATS TR 006."""
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import ArrayObject, DecodedStreamObject, DictionaryObject, NameObject, NumberObject, TextStringObject
    w = PdfWriter(clone_from=PdfReader(str(pdf)))
    icc = DecodedStreamObject()
    icc.set_data((match.PROFILE_DIR / match.PROFILES[match.MASTER][1]).read_bytes())
    icc[NameObject("/N")] = NumberObject(4)
    oi = DictionaryObject({NameObject("/Type"): NameObject("/OutputIntent"), NameObject("/S"): NameObject("/GTS_PDFX"),
                           NameObject("/OutputConditionIdentifier"): TextStringObject(PROFILE_ID),
                           NameObject("/OutputCondition"): TextStringObject(PROFILE),
                           NameObject("/Info"): TextStringObject(PROFILE),
                           NameObject("/RegistryName"): TextStringObject("http://www.color.org"),
                           NameObject("/DestOutputProfile"): w._add_object(icc)})
    w._root_object[NameObject("/OutputIntents")] = ArrayObject([oi])
    w.write(str(pdf))


def used_gstates(res, data, depth=0):
    """The ExtGState dictionaries a content stream actually applies (`/Name gs`), following its Form XObjects."""
    res = res.get_object() if res is not None else {}
    gs, xo, out = res.get("/ExtGState", {}), res.get("/XObject", {}), []
    for n in {"/" + m.decode("latin-1") for m in re.findall(rb"/([^\s/\[\]()<>{}%]+)\s+gs\b", data)}:
        if n in gs:
            out.append(gs[n].get_object())
    for n in {"/" + m.decode("latin-1") for m in re.findall(rb"/([^\s/\[\]()<>{}%]+)\s+Do\b", data)}:
        x = xo[n].get_object() if n in xo else None
        if x is not None and x.get("/Subtype") == "/Form" and depth < 8:
            out += used_gstates(x.get("/Resources", res), x.get_data(), depth + 1)
    return out


def check_pdfx(pdf, names):
    """names: the artboard names in page order. Fill overprint, judged by the graphics states each page's content
    actually applies: on a one-colour black artboard every one overprints (K100 overprints, per the print spec), on the
    die-cut sticker its CutContour line does, and nowhere else does any."""
    from pypdf import PdfReader
    r = PdfReader(str(pdf))
    oi = r.trailer["/Root"]["/OutputIntents"][0].get_object()
    prof = oi["/DestOutputProfile"].get_object().get_data()
    over = []
    for pg, nm in zip(r.pages, names):
        ops = [str(g.get("/op")) == "True" for g in used_gstates(pg.get("/Resources"), pg.get_contents().get_data())]
        over.append(bool(ops) and all(ops) if "Mono-Black" in nm else any(ops) if nm.startswith("Sticker-") else not any(ops))
    layers = [str(o.get_object().get("/Name")) for o in r.trailer["/Root"].get("/OCProperties", {}).get("/OCGs", [])]
    ok = {"pages": len(r.pages) == len(names), "identifier": oi["/OutputConditionIdentifier"] == PROFILE_ID,
          "profile embedded": prof[36:40] == b"acsp" and b"GRACoL" in prof,
          "PDF/X-4 by Illustrator": b"pdfxid:GTS_PDFXVersion>PDF/X-4" in Path(pdf).read_bytes(),  # its XMP; the intent's /GTS_PDFX is ours
          "no fonts": b"/FontFile" not in Path(pdf).read_bytes(), "no background layer": "Background" not in layers,
          "overprint": all(over)}
    print(Path(pdf).name, ok)
    if not all(ok.values()):
        raise RuntimeError(f"{pdf}: PDF/X-4 check failed {ok}")


def eps_plates(f):
    """An EPS file's plates from its DSC comments: (process plates, spot inks), each None when the file does not say
    (an empty list is no ink, a missing one is unknown). Long lists continue on %%+ lines; (atend) defers to the trailer."""
    lines, out = f.read_bytes().decode("latin-1").splitlines(), {}
    for key in ("DocumentProcessColors", "DocumentCustomColors"):
        at = [n for n, l in enumerate(lines) if l.startswith(f"%%{key}:")]
        if at and lines[at[0]].split(":", 1)[1].strip() == "(atend)":
            at = [n for n in at[1:] if lines[n].split(":", 1)[1].strip() != "(atend)"][-1:]
        if not at:
            out[key] = None
            continue
        i, vals = at[0], [lines[at[0]].split(":", 1)[1]]
        while i + len(vals) < len(lines) and lines[i + len(vals)].startswith("%%+"):
            vals.append(lines[i + len(vals)][3:])
        text = " ".join(vals)
        out[key] = set(re.findall(r"\(([^)]+)\)", text)) or set(text.split())
    return out["DocumentProcessColors"], out["DocumentCustomColors"]


def check_eps(pm, suite_names, badge_names):
    """Every EPS's plates against the table in Print-Specs ("Which artboards for which job"): what a vendor's RIP will
    separate. Mono-Black is K only and Mono-White no ink in every job; the CMYK jobs carry process plates and no spot
    ink but the sticker's CutContour. In the Pantone job the spots are exactly the table's: 2726 C for the AI and 7547 C
    for the type on light, 305 C on dark, plus 305 C for 08's rule; in full colour the 3D mark adds the spots of the core
    colours it is drawn from (palette.json stopMap: 2726 C and 305 C, and 7547 C on light), logomark alone included;
    Flat, favicon and wordmark files are pure spot, the other full-colour files CMYK plus their spots. Each folder holds
    exactly one EPS per artboard."""
    CMYK = {"Cyan", "Magenta", "Yellow", "Black"}
    inks = {s["brand_color"]: s["name"] for s in jload(kit.BUILD / "print-colors.json")["illustrator_swatches"]
            if s.get("type") == "spot" and s["name"].endswith(" C")}
    mark_spots = {m: {inks[t] for t in BRAND["stopMap"][m].values() if t in inks} for m in ("light", "dark")}

    def pms_spots(lock, state):
        if "Favicon" in lock:
            return {"PANTONE 305 C"} if state.endswith("Dark") else {"PANTONE 2726 C"}
        mark = (mark_spots["dark" if state.endswith("Dark") else "light"]
                if state.startswith("FullColor") and "Wordmark" not in lock else set())
        if "Logomark" in lock:
            return mark or ({"PANTONE 305 C"} if state.endswith("Dark") else {"PANTONE 2726 C"})
        if state.endswith("Dark"):
            return {"PANTONE 305 C"} | mark
        return {"PANTONE 2726 C", "PANTONE 7547 C"} | ({"PANTONE 305 C"} if lock.startswith("08-") else set()) | mark
    bad = []
    for folder, job, names in (("EPS_CMYK", "AAP_CMYK", suite_names), ("EPS_PMS-Coated", "AAP_PMS-C", suite_names),
                               ("Badges-Sticker/EPS_CMYK", "AAP_CMYK", badge_names)):
        stray = sorted({p.name for p in (pm / folder).glob("*.eps")} - {f"{job}_{nm}.eps" for nm in names})
        if stray:
            bad.append(f"{folder}: EPS files no artboard asks for: {stray}")
        for nm in names:
            f = pm / folder / f"{job}_{nm}.eps"
            if not f.exists():
                bad.append(f"{folder}: no EPS for {nm}")
                continue
            proc, spot = eps_plates(f)
            if proc is None or spot is None:
                bad.append(f"{folder}/{f.name}: no DSC colour list, so its plates are unknown")
                continue
            state, pms, lock = nm.rsplit("_", 1)[-1], "PMS" in folder, nm.split("_")[0]
            if state == "Mono-Black":
                ok = proc == {"Black"} and not spot
            elif state == "Mono-White":
                ok = not proc and not spot
            elif not pms:
                ok = bool(proc) and proc <= CMYK and spot == ({"CutContour"} if nm.startswith("Sticker-") else set())
            else:
                process_too = state.startswith("FullColor") and "Favicon" not in lock and "Wordmark" not in lock
                ok = (bool(proc) and proc <= CMYK if process_too else not proc) and spot == pms_spots(lock, state)
            if not ok:
                bad.append(f"{folder}/{f.name}: process {sorted(proc)} spot {sorted(spot)}")
    if bad:
        raise RuntimeError("EPS plates differ from Print-Specs:\n  " + "\n  ".join(bad))
    print(f"EPS plates: all {2 * len(suite_names) + len(badge_names)} files as Print-Specs lists")


def print_failures(report):
    """The failures aap_print.jsx reports without stopping: builds not set or read back wrong, inks not made spot."""
    return [s.strip() for s in re.findall(r"[^;]*(?:NOT SET|NOT CONVERTED|NOT SPOT|MISMATCH)[^;]*", report)]


def print_masters():
    pm = kit.KIT / "Print-Masters"
    suite_scene = jload(SCENES / "suite.json")
    n = len(suite_scene["artboards"])
    cfg = {"src": str(MASTER_FILES[0]), "swatches": print_config("suite"),
           "cmyk": {"ai": str(pm / "AAP_Master-Logo-Suite_CMYK.ai"), "epsFolder": str(pm / "EPS_CMYK"), "epsPrefix": "AAP_CMYK",
                    "pdf": str(pm / "AAP_Master-Logo-Suite_CMYK_PDF-X4.pdf"),
                    "proofPdf": str(pm / "AAP_Master-Logo-Suite_Proof.pdf"), "artboards": f"1-{n}"},
           "pms": [{"side": "C", "ai": str(pm / "AAP_Master-Logo-Suite_PMS-Coated.ai"), "epsFolder": str(pm / "EPS_PMS-Coated"),
                    "epsPrefix": "AAP_PMS-C"}]}  # ponytail: uncoated spot master dropped (Illustrator would not convert it reliably); U refs in Print-Specs
    g_scene = jload(SCENES / "graphics.json")
    g_idx = [i + 1 for i, a in enumerate(g_scene["artboards"]) if a["name"].startswith(("Badge-", "Sticker-"))]
    gcfg = {"src": str(MASTER_FILES[2]), "swatches": print_config("graphics"),
            "cmyk": {"ai": str(pm / "Badges-Sticker" / "AAP_Brand-Graphics_CMYK.ai"),
                     "epsFolder": str(pm / "Badges-Sticker" / "EPS_CMYK"), "epsPrefix": "AAP_CMYK",
                     "pdf": str(pm / "Badges-Sticker" / "AAP_Badges-Sticker_CMYK_PDF-X4.pdf"), "artboards": ranges(g_idx)},
            "pms": []}
    for name, c in (("print", cfg), ("print-graphics", gcfg)):
        Path(c["cmyk"]["ai"]).parent.mkdir(parents=True, exist_ok=True)
        path = SCENES / f"{name}.json"
        path.write_text(json.dumps(c, indent=1), encoding="utf-8")
        report = illustrator("aap_print.jsx", "PRINT_PATH", path)
        print(name, "->", report)
        if print_failures(report):
            raise RuntimeError(f"{name}: {'; '.join(print_failures(report))}")
        write_output_intent(c["cmyk"]["pdf"])
        check_pdfx(c["cmyk"]["pdf"], [a["name"] for a in suite_scene["artboards"]] if name == "print"
                   else [g_scene["artboards"][i - 1]["name"] for i in g_idx])
    check_eps(pm, [a["name"] for a in suite_scene["artboards"]], [g_scene["artboards"][i - 1]["name"] for i in g_idx])
    return cfg


MASTER_FILES = [kit.KIT / "01_Master-Logo-Suite" / "AAP_Master-Logo-Suite.ai",
                kit.KIT / "02_Original-Recreations" / "AAP_Original-Recreations.ai",
                kit.KIT / "03_Brand-Graphics" / "AAP_Brand-Graphics.ai",
                kit.KIT / "Print-Masters" / "AAP_Master-Logo-Suite_CMYK.ai",
                kit.KIT / "Print-Masters" / "AAP_Master-Logo-Suite_PMS-Coated.ai",
                kit.KIT / "Print-Masters" / "Badges-Sticker" / "AAP_Brand-Graphics_CMYK.ai"]


def split_masters():
    """Each logo as its own file: every artboard of the suite and of the recreations saved as a separate .ai."""
    jobs = [{"src": str(MASTER_FILES[0]), "folder": str(kit.KIT / "01_Master-Logo-Suite" / "AI_per-artboard"), "prefix": "AAP"},
            {"src": str(MASTER_FILES[1]), "folder": str(kit.KIT / "02_Original-Recreations" / "AI_per-artboard"), "prefix": "AAP"}]
    cfg = SCENES / "split.json"
    cfg.write_text(json.dumps({"jobs": jobs}), encoding="utf-8")
    print("split ->", illustrator("aap_split.jsx", "SPLIT_PATH", cfg))


def inventory():
    """What the finished .ai files actually contain (artboards, layers, swatches, patterns, live text, rasters,
    colours painted outside the swatches) -> verify/inventory.json, for the audit."""
    missing = [f.name for f in MASTER_FILES if not f.exists()]
    if missing:
        raise RuntimeError(f"masters missing from the kit, so nothing to read back: {missing}")
    cfg = SCENES / "inventory.json"
    cfg.write_text(json.dumps({"files": [str(f) for f in MASTER_FILES], "out": str(kit.VERIFY / "inventory.json")}), encoding="utf-8")
    print(illustrator("aap_inventory.jsx", "INV_PATH", cfg))
    check_inventory()


def zstd_exe():
    for c in (shutil.which("zstd"), r"C:\msys64\usr\bin\zstd.exe", r"C:\Program Files\Git\usr\bin\zstd.exe"):
        if c and Path(c).exists():
            return c
    raise RuntimeError("zstd not found: it is needed to read the pattern definitions inside the .ai masters")


def pattern_defs(ai):
    """{pattern name: (plain colour settings, names of the swatches it references)}, read from the .ai file's own native
    data: the only place a pattern's art can be seen (the scripting DOM gives a pattern a name and nothing else)."""
    from pypdf import PdfReader
    pr = PdfReader(str(ai)).pages[0]["/PieceInfo"]["/Illustrator"].get_object()["/Private"].get_object()
    keys = sorted((k for k in pr if k.startswith("/AIPrivateData")), key=lambda k: int(k[len("/AIPrivateData"):]))
    blob = b"".join(pr[k].get_object().get_data() for k in keys)
    if b"%AI24_ZStandard_Data" in blob:
        z = blob[blob.index(b"%AI24_ZStandard_Data") + len(b"%AI24_ZStandard_Data"):]
        blob = subprocess.run([zstd_exe(), "-d", "-q", "-c"], input=z, capture_output=True, check=True).stdout
    elif b"%AI12_CompressedData" in blob:
        blob = zlib.decompressobj().decompress(blob[blob.index(b"%AI12_CompressedData") + len(b"%AI12_CompressedData"):])
    t = blob.decode("latin-1").replace("\r", "\n")
    return {m.group(1): (len(re.findall(r"\n%?_?[-0-9. ]+ (?:Xa|XA|k|K|g|G)\n", m.group(2))),
                         set(re.findall(r"\(([^)]*)\) [-0-9.]+ [-0-9.]+ X[kKxX]\n", m.group(2))))
            for m in re.finditer(r"%AI3_BeginPattern: \(([^)]*)\)(.*?)%AI3_EndPattern", t, re.S)}


def check_inventory():
    """The masters as the inventory read them back, held to what the README promises: every master present and read,
    every swatch read, no live text, raster or placed art, no colour outside a swatch (inside pattern definitions too,
    read from the files themselves), only global swatches besides [None] and the brand patterns, the CutContour die
    line a spot ink of 100 % magenta in the Brand Graphics only, RGB screen masters and CMYK print masters, and every
    print-master swatch as print_config specifies: the CMYK masters' process builds; in the PMS master each logo ink as
    its Pantone spot (name, type, alternate) with no AAP-named copy left and the other swatches as process; nothing
    outside the spec. Anything else stops the build, an unread swatch included: a check that could not look is not a pass."""
    read = {Path(d["file"]).name: d for d in jload(kit.VERIFY / "inventory.json")}
    all_patterns, bad = {"AAP Pattern " + title for _, title in PATTERNS}, []
    for i, f in enumerate(MASTER_FILES):
        d = read.get(f.name)
        if not f.exists() or d is None:
            bad.append(f"{f.name}: " + ("missing from the kit" if not f.exists() else "not read back"))
            continue
        graphics = f.name.startswith("AAP_Brand-Graphics")
        pats, spots = all_patterns if graphics else set(), {s["name"]: s for s in d["spots"]}
        cut, defs, other = spots.get("CutContour"), pattern_defs(f), d.get("otherSwatches")
        # Illustrator reads a spot back in the document's colour space: CMYK 0/100/0/0 in the CMYK master, its RGB
        # rendering 236/0/140 in the RGB one (the definition stays SPOTCMYK in both)
        cut_mode, _, cut_txt = (cut["color"] if cut else "").partition(" ")
        cut_vals = [float(v) for v in cut_txt.split("/")] if cut_mode in ("CMYK", "RGB") else None
        cut_ref, cut_tol = ([0, 100, 0, 0], 0.5) if cut_mode == "CMYK" else ([236, 0, 140], 3)
        stray = None if other is None else sorted(f"{s['name']} ({s['type']})" for s in other if (s["name"], s["type"]) != ("[None]", "NoColor")
                                                  and not (s["type"] == "PatternColor" and s["name"] in pats))
        for ok, what in ((d["colorSpace"] == ("DocumentColorSpace.CMYK" if i >= 3 else "DocumentColorSpace.RGB"), f"colour mode {d['colorSpace']}"),
                         (d["unreadableSwatches"] == 0, f"{d['unreadableSwatches']} swatches unread (run python build.py inventory again)"),
                         (d["textFrames"] == 0, f"{d['textFrames']} live text frames"),
                         (d["rasterItems"] + d["placedItems"] == 0, "raster or placed images"),
                         (not d["nonSwatchColors"], f"colours outside a swatch: {d['nonSwatchColors'][:4]}"),
                         (stray == [], f"swatches that are not global brand swatches: {stray if stray is not None else 'not listed (old inventory)'}"),
                         (set(d["patterns"]) == pats == set(defs), f"patterns {sorted(d['patterns'])}, defined {sorted(defs)}; expected {sorted(pats)}"),
                         ((cut is not None and cut["type"] == "ColorModel.SPOT" and cut.get("kind") == "SpotColorKind.SPOTCMYK"
                           and cut_vals is not None and len(cut_vals) == len(cut_ref)
                           and sum(abs(a - b) for a, b in zip(cut_vals, cut_ref)) <= cut_tol) if graphics else cut is None,
                          f"CutContour {cut}; expected " + ("a spot ink of 100 % magenta" if graphics else "none"))):
            if not ok:
                bad.append(f"{f.name}: {what}")
        for nm, (plain, refs) in defs.items():
            if plain or not refs or refs - set(spots):
                bad.append(f"{f.name}: pattern {nm} has {plain} colours outside a swatch and refers to unknown swatches "
                           f"{sorted(refs - set(spots))}" + ("" if refs else " (no swatch at all)"))
    for f, scene, side in ((MASTER_FILES[3], "suite", None), (MASTER_FILES[4], "suite", "C"), (MASTER_FILES[5], "graphics", None)):
        if f.name not in read:
            continue  # already reported as not read back
        got = {s["name"]: s for s in read[f.name]["spots"]}
        want = {}
        for n, e in print_config(scene).items():
            s = (e.get("spots") or {}).get(side) if side else None
            want[s["name"] if s else n] = ("ColorModel.SPOT", s["cmyk"]) if s else ("ColorModel.PROCESS", e["cmyk"])
        for name, (kind, cmyk) in want.items():
            g = got.get(name)
            mode, _, vals = (g["color"] if g else "").partition(" ")
            if g is None:
                bad.append(f"{f.name}: {name} missing")
            elif not (mode == "CMYK" and g["type"] == kind and sum(abs(float(a) - b) for a, b in zip(vals.split("/"), cmyk)) <= 0.5):
                bad.append(f"{f.name}: {name} is {g['type']} {g['color']}; spec {kind} CMYK {cmyk}")
        extra = sorted(set(got) - set(want) - {"[Registration]", "CutContour"})
        if extra:
            bad.append(f"{f.name}: swatches outside the print spec (an unconverted ink keeps its AAP name): {extra}")
        print(f"{f.name}: {len(want)} swatches checked against the print spec")
    if bad:
        raise RuntimeError("inventory check failed:\n  " + "\n  ".join(bad))
    print("inventory check: every master as specified")


# ---------------------------------------------------------------- documentation: docs.py


# ---------------------------------------------------------------- main

if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "all"
    if what in ("suite", "all"):
        suite()
    if what in ("recreations", "all"):
        recreations()
    if what == "recreations-check":  # compose and score against the originals without Illustrator
        recreations(ai=False)
    if what in ("graphics", "all"):
        graphics()
    if what in ("print", "all"):
        print_masters()
    if what in ("split", "all"):
        split_masters()
    if what in ("inventory", "all"):
        inventory()
    if what in ("docs", "all"):
        import docs  # noqa: E402  (imports this module's constants)
        docs.write_docs()
