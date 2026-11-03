"""Shared helpers for the Alliance AI Partners brand-kit build (docs/brand-kit).

Every component is authored as an SVG in its source image's pixel space, verified by rendering it
with VectorCraft and comparing it against the original, then assembled into Illustrator documents
by the JSX builders, which import the SVGs and bind every color to a global brand swatch.
"""
import json
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

KIT = Path(__file__).resolve().parents[1]  # docs/brand-kit
BUILD = KIT / "_build"
ORIG = KIT.parent / "logos"
COMP = BUILD / "components"
FIT = BUILD / "fit"
VERIFY = BUILD / "verify"
WORK = BUILD / "work"
VC = r"C:\Program Files\VectorCraft\vectorcraft-cli.exe"

# Core palette (palette.json): the brand guidelines board's colours (original 02, "02 | COLOR PALETTE") under their
# unified names; Black is for one-ink work only, so it is not a nearest-colour target
PALETTE = {c["name"]: c["hex"] for c in json.loads((BUILD / "palette.json").read_text(encoding="utf-8"))["core"] if c["name"] != "Black"}

# The 17 unique originals (the "(1)" copy of 1f3b28e6 is byte-identical and skipped).
ORIGINALS = {
    "01": ("0bba6030-3597-4e47-831a-3da1f20439a7.jpeg", "Horizontal: gradient AP + 'ALLIANCE AI PARTNERS' + tagline, light"),
    "02": ("11d44af0-e70b-4d0f-ba3e-1fc0d871167b.jpeg", "Brand guidelines & style board"),
    "03": ("1f3b28e6-ad6c-4e5d-80d8-e2f2e1e38954.jpeg", "App icon: flat cyan AP in rounded-square outline, navy"),
    "04": ("29138393-2121-469f-8575-a5dbb045ed7b.jpeg", "Horizontal dark: gradient AP + 'ALLIANCE / AI PARTNERS' white"),
    "05": ("449dea5f-2cbe-468a-a59e-a382b46ec7ba.jpeg", "Stacked: faceted bird above 'ALLIANCE / AI PARTNERS', light"),
    "06": ("4bdc99a9-5ffc-431f-a439-5a456f59c07e.jpeg", "Hero gradient AP mark only, light (MASTER GEOMETRY)"),
    "07": ("697cd1fe-d189-4888-a600-180e6e979700.jpeg", "Horizontal dark: flat cyan AP + 'ALLIANCE AI / PARTNERS' white"),
    "08": ("7580025b-e049-4a17-b0ab-97d45dcb6acc.jpeg", "Horizontal: bird + 'ALLIANCE / AI PARTNERS' (AI cyan), off-white"),
    "09": ("7f533882-f9ad-48ce-9044-9b179b26109d.jpeg", "Stacked dark: flat cyan AP above 'ALLIANCE AI / PARTNERS' white"),
    "10": ("8a267aa5-f173-4f96-a624-04d36e242078.jpeg", "Horizontal dark: flat cyan AP + 'ALLIANCE' bold / 'AI PARTNERS' light"),
    "11": ("8e16c218-08cf-46d6-bd9e-8d7ae6ad929b.jpeg", "Two-tone mark: white A + cyan ribbon/P, navy"),
    "12": ("90cf7a67-67f3-4bfe-8aea-0e10c2dab1a2.jpeg", "Flat cyan AP mark, navy"),
    "13": ("a9ff3937-6b76-4717-b0fd-356a7cf4de8c.jpeg", "Horizontal: gradient AP + name + cyan rule + 'ENTERPRISE AI CONSULTING'"),
    "14": ("b161ddd4-d580-4aa3-b20f-8a20e2ed1fa2.jpeg", "Stacked: gradient AP above 'ALLIANCE AI PARTNERS', light"),
    "15": ("c516876b-0a00-4b22-9252-6f521ca520a6.jpeg", "Faceted bird mark only, light (MASTER BIRD)"),
    "16": ("da60ac39-875a-4f6e-805f-a710b7e2ae17.jpeg", "Stacked dark: flat cyan AP above 'ALLIANCE AI / PARTNERS' white"),
    "17": ("e7dbe480-3073-48eb-9568-d84c3239a496.jpeg", "Shield badge: gradient AP in beveled shield + banner"),
}


def orig(oid):
    return ORIG / ORIGINALS[oid][0]


def load(oid):
    """Original image as uint8 RGB array (H, W, 3)."""
    return np.asarray(Image.open(orig(oid)).convert("RGB"))


# ---------------------------------------------------------------- color

def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def rgbhex(c):
    c = np.clip(np.round(np.asarray(c, float)), 0, 255).astype(int)
    return "#%02X%02X%02X" % tuple(c)


def srgb_to_lab(rgb):
    """sRGB (0-255, shape (..., 3)) to CIE Lab (D65)."""
    c = np.asarray(rgb, float) / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    m = np.array([[0.4124564, 0.3575761, 0.1804375],
                  [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])
    xyz = c @ m.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def de2000(lab1, lab2):
    """CIEDE2000 color difference, vectorized over the leading axes."""
    lab1, lab2 = np.broadcast_arrays(np.asarray(lab1, float), np.asarray(lab2, float))
    L1, a1, b1 = lab1[..., 0], lab1[..., 1], lab1[..., 2]
    L2, a2, b2 = lab2[..., 0], lab2[..., 1], lab2[..., 2]
    cm = (np.hypot(a1, b1) + np.hypot(a2, b2)) / 2
    g = 0.5 * (1 - np.sqrt(cm ** 7 / (cm ** 7 + 25.0 ** 7)))
    a1p, a2p = (1 + g) * a1, (1 + g) * a2
    c1p, c2p = np.hypot(a1p, b1), np.hypot(a2p, b2)
    h1p = np.degrees(np.arctan2(b1, a1p)) % 360
    h2p = np.degrees(np.arctan2(b2, a2p)) % 360
    zero = (c1p * c2p) == 0
    dh = h2p - h1p
    dh = np.where(dh > 180, dh - 360, np.where(dh < -180, dh + 360, dh))
    dh = np.where(zero, 0, dh)
    dL, dC = L2 - L1, c2p - c1p
    dH = 2 * np.sqrt(c1p * c2p) * np.sin(np.radians(dh / 2))
    Lm, cpm = (L1 + L2) / 2, (c1p + c2p) / 2
    hs = h1p + h2p
    hm = np.where(zero, hs, np.where(np.abs(h1p - h2p) <= 180, hs / 2, np.where(hs < 360, (hs + 360) / 2, (hs - 360) / 2)))
    t = (1 - 0.17 * np.cos(np.radians(hm - 30)) + 0.24 * np.cos(np.radians(2 * hm))
         + 0.32 * np.cos(np.radians(3 * hm + 6)) - 0.20 * np.cos(np.radians(4 * hm - 63)))
    dtheta = 30 * np.exp(-(((hm - 275) / 25) ** 2))
    rc = 2 * np.sqrt(cpm ** 7 / (cpm ** 7 + 25.0 ** 7))
    sl = 1 + 0.015 * (Lm - 50) ** 2 / np.sqrt(20 + (Lm - 50) ** 2)
    sc, sh = 1 + 0.045 * cpm, 1 + 0.015 * cpm * t
    rt = -np.sin(np.radians(2 * dtheta)) * rc
    return np.sqrt((dL / sl) ** 2 + (dC / sc) ** 2 + (dH / sh) ** 2 + rt * (dC / sc) * (dH / sh))


def nearest_palette(hex_or_rgb):
    """(name, hex, dE2000) of the closest core palette color."""
    lab = srgb_to_lab(hexrgb(hex_or_rgb) if isinstance(hex_or_rgb, str) else hex_or_rgb)
    best = min(PALETTE.items(), key=lambda kv: float(de2000(lab, srgb_to_lab(hexrgb(kv[1])))))
    return best[0], best[1], float(de2000(lab, srgb_to_lab(hexrgb(best[1]))))


# ---------------------------------------------------------------- SVG paths

_TOKEN = re.compile(r"[MmLlHhVvCcSsQqTtZz]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")


def parse_d(d):
    """SVG path data -> subpaths [{'start': (x, y), 'segs': [('L', x, y) | ('C', x1, y1, x2, y2, x, y)], 'closed': bool}].
    Handles absolute/relative M L H V C S Q T Z (quadratics become cubics; arcs are not supported)."""
    toks = _TOKEN.findall(d)
    i, cmd, cur, start, last_c = 0, None, (0.0, 0.0), (0.0, 0.0), None
    subs, sub = [], None

    def num():
        nonlocal i
        v = float(toks[i]); i += 1
        return v

    while i < len(toks):
        if re.match(r"[A-Za-z]", toks[i]):
            cmd = toks[i]; i += 1
            if cmd in "Zz":
                if sub:
                    sub["closed"] = True
                cur, last_c = start, None
                continue
        rel = cmd.islower()
        c = cmd.upper()
        ox, oy = cur if rel else (0.0, 0.0)
        if c == "M":
            x, y = num() + ox, num() + oy
            sub = {"start": (x, y), "segs": [], "closed": False}
            subs.append(sub)
            cur = start = (x, y)
            cmd = "l" if rel else "L"
            last_c = None
        elif c == "L":
            x, y = num() + ox, num() + oy
            sub["segs"].append(("L", x, y)); cur = (x, y); last_c = None
        elif c == "H":
            x = num() + ox
            sub["segs"].append(("L", x, cur[1])); cur = (x, cur[1]); last_c = None
        elif c == "V":
            y = num() + (cur[1] if rel else 0.0)
            sub["segs"].append(("L", cur[0], y)); cur = (cur[0], y); last_c = None
        elif c == "C":
            x1, y1, x2, y2, x, y = num() + ox, num() + oy, num() + ox, num() + oy, num() + ox, num() + oy
            sub["segs"].append(("C", x1, y1, x2, y2, x, y)); cur = (x, y); last_c = (x2, y2)
        elif c == "S":
            x1, y1 = (2 * cur[0] - last_c[0], 2 * cur[1] - last_c[1]) if last_c else cur
            x2, y2, x, y = num() + ox, num() + oy, num() + ox, num() + oy
            sub["segs"].append(("C", x1, y1, x2, y2, x, y)); cur = (x, y); last_c = (x2, y2)
        elif c in "QT":
            if c == "Q":
                qx, qy = num() + ox, num() + oy
            else:
                qx, qy = (2 * cur[0] - last_c[0], 2 * cur[1] - last_c[1]) if last_c else cur
            x, y = num() + ox, num() + oy
            sub["segs"].append(("C", cur[0] + 2 / 3 * (qx - cur[0]), cur[1] + 2 / 3 * (qy - cur[1]),
                                x + 2 / 3 * (qx - x), y + 2 / 3 * (qy - y), x, y))
            cur = (x, y); last_c = (qx, qy)  # ponytail: T after Q reflects the quadratic control point, as SVG does
        else:
            raise ValueError("unsupported path command " + cmd)
    return subs


def format_d(subs, nd=3):
    f = lambda v: ("%.*f" % (nd, v)).rstrip("0").rstrip(".")
    out = []
    for s in subs:
        out.append("M%s %s" % (f(s["start"][0]), f(s["start"][1])))
        for g in s["segs"]:
            out.append(("L%s %s" % (f(g[1]), f(g[2]))) if g[0] == "L" else "C" + " ".join(f(v) for v in g[1:]))
        if s["closed"]:
            out.append("Z")
    return " ".join(out)


def transform_d(d, scale=1.0, dx=0.0, dy=0.0, nd=3):
    """Scale about the origin, then translate."""
    subs = parse_d(d)
    t = lambda x, y: (x * scale + dx, y * scale + dy)
    for s in subs:
        s["start"] = t(*s["start"])
        s["segs"] = [("L",) + t(g[1], g[2]) if g[0] == "L" else ("C",) + t(g[1], g[2]) + t(g[3], g[4]) + t(g[5], g[6])
                     for g in s["segs"]]
    return format_d(subs, nd)


def flatten(subs, tol=0.25):
    """Subpaths -> list of polylines (lists of (x, y)), curves split until flat within ~tol px."""
    polys = []
    for s in subs:
        pts, cur = [s["start"]], s["start"]
        for g in s["segs"]:
            if g[0] == "L":
                cur = (g[1], g[2]); pts.append(cur)
                continue
            p0, p1, p2, p3 = np.array(cur), np.array(g[1:3]), np.array(g[3:5]), np.array(g[5:7])
            est = np.linalg.norm(p1 - p0) + np.linalg.norm(p2 - p1) + np.linalg.norm(p3 - p2)
            n = int(min(400, max(2, np.sqrt(est / max(tol, 1e-3)) * 2)))
            for k in range(1, n + 1):
                t = k / n
                q = (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3
                pts.append(tuple(q))
            cur = (g[5], g[6])
        polys.append(pts)
    return polys


def raster(ds, w, h, scale=1.0, ss=4):
    """Fill path data strings (even-odd within each path, union across paths) into a float coverage
    mask (h*scale, w*scale), anti-aliased by ss x ss supersampling."""
    W, H = int(round(w * scale)), int(round(h * scale))
    acc = np.zeros((H * ss, W * ss), bool)
    for d in ([ds] if isinstance(ds, str) else ds):
        m = np.zeros_like(acc)
        for poly in flatten(parse_d(d), tol=0.2 / (scale * ss)):
            if len(poly) < 3:
                continue
            img = Image.new("1", (W * ss, H * ss), 0)
            ImageDraw.Draw(img).polygon([(x * scale * ss, y * scale * ss) for x, y in poly], fill=1)
            m ^= np.asarray(img, bool)
        acc |= m
    return acc.reshape(H, ss, W, ss).mean((1, 3))


# ---------------------------------------------------------------- VectorCraft

def _vc(args):
    r = subprocess.run([VC] + [str(a) for a in args], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise RuntimeError("vectorcraft failed: " + (r.stderr or r.stdout)[-800:])
    return r.stdout


def render_svg(svg, scale=1.0, out_png=None):
    """Render an SVG file (or SVG text) with VectorCraft -> float RGBA array in 0..1, shape (H, W, 4)."""
    WORK.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=WORK) as td:
        src = Path(svg) if not str(svg).lstrip().startswith("<") else Path(td) / "in.svg"
        if src.name == "in.svg":
            src.write_text(svg, encoding="utf-8")
        png = Path(out_png) if out_png else Path(td) / "out.png"
        _vc(["convert", src, png, "--scale", scale])
        return np.asarray(Image.open(png).convert("RGBA"), float) / 255.0


def over(rgba, bg="#FFFFFF"):
    """Composite a float RGBA render over a solid background -> float RGB 0..255."""
    a = rgba[..., 3:4]
    return rgba[..., :3] * 255 * a + hexrgb(bg) * (1 - a)


def parse_svg_paths(svg_text):
    """[(d, attrs)] for every <path> element (attrs: fill, fill-rule, id, ...)."""
    out = []
    for m in re.finditer(r"<path\b([^>]*)/?>", svg_text):
        attrs = dict(re.findall(r'([\w:-]+)="([^"]*)"', m.group(1)))
        if "d" in attrs:
            out.append((attrs.pop("d"), attrs))
    return out


def trace_image(img, colors, noise=4, ignore_white=True):
    """Logo-mode trace of an RGB image (uint8 array or path) to the given flat colors.
    Returns [(d, fill_hex_upper)]. Edges are fitted to a fraction of a pixel, corners and lines snapped."""
    WORK.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=WORK) as td:
        td = Path(td)
        png = td / "in.png"
        if isinstance(img, (str, Path)):
            Image.open(img).convert("RGB").save(png)
        else:
            Image.fromarray(np.asarray(img, np.uint8)).convert("RGB").save(png)
        cmds = td / "cmd.json"
        cmds.write_text(json.dumps([
            {"command": "select.all", "params": {}},
            {"command": "imageTrace.makeAndExpand", "params": {"params": {
                "mode": "logo", "logoColors": list(colors), "noise": noise, "ignoreWhite": ignore_white}}}]))
        svg = td / "out.svg"
        _vc(["run", "--in", png, "--commands", cmds, "--export", svg])
        return [(d, a.get("fill", "").upper()) for d, a in parse_svg_paths(svg.read_text(encoding="utf-8"))]


def trace_mask(mask, upscale=4, blur=0.6, noise=4):
    """Trace a boolean/float mask (H, W) into smooth path data in the mask's own pixel space.
    The mask is upsampled and lightly smoothed first so curves come out clean, then traced in
    VectorCraft logo mode and scaled back. Returns a list of path d strings."""
    m = np.asarray(mask, float)
    im = Image.fromarray((m * 255).astype(np.uint8)).resize((m.shape[1] * upscale, m.shape[0] * upscale), Image.BILINEAR)
    if blur:
        from PIL import ImageFilter
        im = im.filter(ImageFilter.GaussianBlur(blur * upscale))
    g = 255 - np.asarray(im, np.uint8)  # shape black on white
    rgb = np.repeat(g[..., None], 3, -1)
    paths = trace_image(rgb, ["#000000"], noise=noise * upscale, ignore_white=True)
    return [transform_d(d, 1.0 / upscale) for d, f in paths if f in ("#000000", "#000")]


# ---------------------------------------------------------------- SVG writing

def svg_doc(w, h, body, defs=""):
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n'
            + (f"<defs>\n{defs}\n</defs>\n" if defs else "") + body + "\n</svg>\n")


def lin_grad(gid, x1, y1, x2, y2, stops):
    """stops: [(offset 0..1, '#RRGGBB'), ...]; userSpaceOnUse so Illustrator imports the exact vector."""
    s = "".join(f'<stop offset="{o:.4f}" stop-color="{c}"/>' for o, c in stops)
    return (f'<linearGradient id="{gid}" x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" '
            f'gradientUnits="userSpaceOnUse">{s}</linearGradient>')


# ---------------------------------------------------------------- masks and metrics

def bg_mask(rgb, bg_hex, thresh=18.0):
    """Foreground = pixels farther than `thresh` (dE2000) from the background color."""
    return de2000(srgb_to_lab(rgb), srgb_to_lab(hexrgb(bg_hex))) > thresh


def dilate(mask, r):
    """Binary dilation by a disk of radius r (pixels)."""
    m = np.asarray(mask, bool)
    out = m.copy()
    r = int(round(r))
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy > r * r or (dx == 0 and dy == 0):
                continue
            out |= np.roll(np.roll(m, dy, 0), dx, 1)
    return out


def erode(mask, r):
    return ~dilate(~np.asarray(mask, bool), r)


def compare(orig_rgb, render_rgb, region=None):
    """Metrics between an original and a render (both 0..255 RGB, same size).
    region: bool mask where color error is measured (default: everywhere)."""
    lo, lr = srgb_to_lab(orig_rgb), srgb_to_lab(render_rgb)
    de = de2000(lo, lr)
    reg = np.ones(de.shape, bool) if region is None else region
    return {"de_mean": round(float(de[reg].mean()), 2), "de_p95": round(float(np.percentile(de[reg], 95)), 2),
            "de_map": de}


def iou(a, b):
    a, b = np.asarray(a, bool), np.asarray(b, bool)
    return float((a & b).sum() / max(1, (a | b).sum()))


def diff_sheet(orig_rgb, render_rgb, out, de_map=None, label=""):
    """Original | render | dE heatmap (0 white .. 10+ red) side by side."""
    o = Image.fromarray(np.asarray(orig_rgb, np.uint8))
    r = Image.fromarray(np.clip(np.asarray(render_rgb), 0, 255).astype(np.uint8))
    if de_map is None:
        de_map = de2000(srgb_to_lab(orig_rgb), srgb_to_lab(render_rgb))
    t = np.clip(de_map / 10.0, 0, 1)[..., None]
    heat = Image.fromarray((np.array([255, 255, 255]) * (1 - t) + np.array([220, 30, 30]) * t).astype(np.uint8))
    w, h = o.size
    sheet = Image.new("RGB", (w * 3 + 20, h + 30), "white")
    for k, im in enumerate((o, r, heat)):
        sheet.paste(im, (k * (w + 10), 30))
    ImageDraw.Draw(sheet).text((6, 8), label + "   original | vector render | dE2000 heatmap (red = 10+)", fill="black")
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


def contact(images, labels, out, cols=3, width=460, bg="#888888"):
    cells = []
    for im, lab in zip(images, labels):
        im = (im if isinstance(im, Image.Image) else Image.fromarray(np.clip(np.asarray(im), 0, 255).astype(np.uint8))).convert("RGB")
        h = int(im.height * width / im.width)
        c = Image.new("RGB", (width, h + 24), "white")
        c.paste(im.resize((width, h)), (0, 24))
        ImageDraw.Draw(c).text((6, 6), lab, fill=(200, 0, 0))
        cells.append(c)
    rows = [cells[i:i + cols] for i in range(0, len(cells), cols)]
    H = sum(max(c.height for c in r) for r in rows)
    sheet = Image.new("RGB", (width * cols, H), bg)
    y = 0
    for r in rows:
        for j, c in enumerate(r):
            sheet.paste(c, (j * width, y))
        y += max(c.height for c in r)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)


# ---------------------------------------------------------------- Montserrat (exported from Illustrator)

_GLYPHS = None


def glyphs():
    """Montserrat outlines exported from Illustrator by export_glyphs.jsx (size 100 pt, tracking 0,
    baseline y=0, y down). {'weights': {style: {'chars': {ch: {'d', 'left'}}, 'strings': {s: [[ch, idx, dx]]}}}}"""
    global _GLYPHS
    if _GLYPHS is None:
        _GLYPHS = json.loads((BUILD / "glyphs.json").read_text(encoding="utf-8"))
    return _GLYPHS


def text_paths(string, style="Bold", size=100.0, tracking=0.0, x=0.0, baseline=0.0):
    """Path d strings for `string` set in Montserrat `style` the way Illustrator sets it (Auto kerning),
    with Illustrator tracking (1/1000 em added after every character), left edge of the first glyph's
    origin at x and the baseline at y=baseline (y down). The string must be one exported by export_glyphs.jsx."""
    w = glyphs()["weights"][style]
    lay = w["strings"].get(string)
    if lay is None:
        raise KeyError(f"'{string}' was not exported for Montserrat {style}; add it to GLYPH_STRINGS and re-run export_glyphs")
    k = size / 100.0
    out = []
    for ch, idx, dx in lay:
        shift = dx * k + idx * tracking / 1000.0 * size
        out.append(transform_d(w["chars"][ch]["d"], k, x + shift, baseline))
    return out
