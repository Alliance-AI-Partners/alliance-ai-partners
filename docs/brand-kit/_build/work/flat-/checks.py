"""Sanity checks on the built SVGs: structure, winding (nonzero == evenodd), specks, white peeking (11),
text boxes drawn on the originals."""
import sys, os, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flatlib as F
from flatlib import kit, np
from PIL import Image, ImageDraw

IDS = ['12', '16', '09', '07', '10', '11', '03']
bad = re.compile(r'<(filter|mask|clipPath|image|pattern|style)\b|mix-blend|opacity=')
for oid in IDS:
    p = os.path.join(F.BUILD, 'components', 'flat-%s.svg' % oid)
    svg = open(p, encoding='utf-8').read()
    j = json.load(open(os.path.join(F.BUILD, 'fit', 'flat-%s.json' % oid), encoding='utf-8'))
    W, H = j['size']
    assert re.search(r'viewBox="0 0 %d %d"' % (W, H), svg), oid
    first = re.search(r'<(rect|path|g)\b[^>]*>', svg.split('</defs>')[-1]).group(0)
    assert 'id="bg"' in first and '#121B2A' in first, (oid, first)
    assert not bad.search(svg), (oid, bad.search(svg).group(0))
    fills = sorted(set(re.findall(r'fill="(#[0-9A-F]{6})"', svg)))
    ids = re.findall(r'\bid="([^"]+)"', svg)
    paths = [(m.group(1), m.group(2)) for m in re.finditer(r'<path id="([^"]+)"[^>]* d="([^"]+)"', svg)]
    worst = 0.0
    for pid, d in paths:
        # nonzero (our winding) vs evenodd must agree
        subs = kit.parse_d(d)
        cov_eo = kit.raster([d], W, H, ss=2)  # kit.raster = even-odd within a path
        # nonzero via winding: sum of signed per-subpath rasters
        acc = np.zeros((H, W))
        for s in subs:
            poly = np.array(kit.flatten([s], tol=0.2)[0])
            sgn = 1 if F.poly_area(poly) > 0 else -1
            acc += sgn * kit.raster([kit.format_d([s])], W, H, ss=2)
        cov_nz = np.clip(np.abs(acc), 0, 1)
        worst = max(worst, float(np.abs(cov_nz - cov_eo).max()))
    specks = [l.get('specks_dropped_area') for l in j['layers']]
    print(oid, 'fills', fills, 'ids', ids, 'nonzero-vs-evenodd max diff %.3f' % worst, 'specks dropped', specks)

# 11: does the white face show anywhere the original is not white?
a = kit.load('11').astype(float)
j = json.load(open(os.path.join(F.BUILD, 'fit', 'flat-11.json'), encoding='utf-8'))
bg, cy, wh = (kit.hexrgb(j['colors'][k]['measured']) for k in ('background', 'cyan', 'white'))
u0, v0 = F.cov3(a, bg, cy, wh)
r = np.asarray(Image.open(os.path.join(F.WORK, 'render_11.png')).convert('RGB'), float)
ur, vr = F.cov3(r, F.NAVY, F.CYAN, F.WHITE)
peek = (vr > 0.15) & (v0 < 0.05) & ~kit.dilate(v0 > 0.5, 1)
print('11 white-peek pixels (vector white >0.15 where original has no white, >1px from white):', int(peek.sum()))

# text boxes on originals
for oid in ['16', '09', '07', '10']:
    j = json.load(open(os.path.join(F.BUILD, 'fit', 'flat-%s.json' % oid), encoding='utf-8'))
    im = Image.open(kit.orig(oid)).convert('RGB')
    dr = ImageDraw.Draw(im)
    dr.rectangle(j['text_bbox'], outline=(255, 0, 0))
    for b in j['text_lines_bbox']:
        dr.rectangle(b, outline=(0, 255, 0))
    mb = j['mark_bbox']
    dr.rectangle(mb, outline=(255, 255, 0))
    im.save(os.path.join(F.WORK, 'boxes_%s.png' % oid))
    print(oid, 'text', j['text_bbox'], 'lines', j['text_lines_bbox'], 'mark', mb)
