import sys, os, re, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flatlib as F
from flatlib import kit, np
from PIL import Image

for oid in ['12', '16', '09', '07', '10', '03']:
    a = kit.load(oid).astype(float)
    H, W, _ = a.shape
    j = json.load(open(os.path.join(F.BUILD, 'fit', 'flat-%s.json' % oid)))
    bg = kit.hexrgb(j['colors']['background']['measured'])
    cy = kit.hexrgb(j['colors']['cyan']['measured'])
    r = np.asarray(Image.open(os.path.join(F.WORK, 'render_%s.png' % oid)).convert('RGB'), float)
    ao = F.cov2(a, bg, cy)
    ar = F.cov2(r, F.NAVY, F.CYAN)
    reg = np.ones((H, W), bool)
    if j.get('text_bbox'):
        x0, y0, x1, y1 = j['text_bbox']
        reg[y0 - 10:y1 + 10, x0 - 10:x1 + 10] = False
    band = kit.dilate((ao > 0.5) | (ar > 0.5), 4) & reg
    ao, ar = np.where(band, ao, 0), np.where(band, ar, 0)
    svg = open(os.path.join(F.BUILD, 'components', 'flat-%s.svg' % oid)).read()
    ds = [m.group(1) for m in re.finditer(r'<path id="[^"]+"[^>]* d="([^"]+)"', svg)]
    per = 0
    for d in ds:
        for poly in kit.flatten(kit.parse_d(d), tol=0.1):
            p = np.array(poly + [poly[0]])
            per += np.linalg.norm(np.diff(p, axis=0), axis=1).sum()
    soft = np.minimum(ao, ar).sum() / np.maximum(ao, ar).sum()
    print(oid, 'area orig %.0f vec %.0f  perimeter %.0f  mean outward offset %.3f px  soft IoU %.4f' % (
        ao.sum(), ar.sum(), per, (ar.sum() - ao.sum()) / per, soft))
