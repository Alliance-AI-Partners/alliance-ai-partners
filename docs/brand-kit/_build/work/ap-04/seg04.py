"""hero-04, stage 1: seeded watershed segmentation of original 04's AP mark into the master's face labels.
Seeds = the master faces placed into 04 by the similarity fit (ap-hero-dark.json), visible part eroded so
they sit well inside 04's own faces, plus the background far from the mark. Writes labels04.npy."""
import json
import sys
import numpy as np
from PIL import Image

B = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'
sys.path[:0] = [B, B + r'\work\ap-']
import kit
from seg import watershed

W4 = kit.WORK / 'ap-04'
BG04 = '#132031'
S, TX, TY = 0.6045, 73.321, 74.123           # ap-hero-dark.json transform_to_04
BOX = (150, 230, 620, 540)                   # x0 y0 x1 y1, mark only (the wordmark starts at x ~ 625)
# watershed labels (seg.py names); faces split by straight cuts inside one band share a label
NAMES = ['bg', 'a-left-outer', 'a-left-bevel', 'a-right-inner', 'a-right-outer', 'ribbon-upper', 'ribbon-lower',
         'p-bowl-fold', 'p-bowl']
FACE_LABEL = {'p-bowl-lower': 'p-bowl', 'p-bowl-under': 'p-bowl', 'a-right-outer': 'a-right-outer',
              'a-right-inner': 'a-right-inner', 'a-left-bevel': 'a-left-bevel', 'a-left-outer': 'a-left-outer',
              'p-bowl-top': 'ribbon-upper', 'p-bowl-fold': 'p-bowl-fold', 'ribbon-front-stem': 'ribbon-upper',
              'ribbon-front': 'ribbon-upper', 'ribbon-back': 'ribbon-lower'}


def master_faces():
    t = (kit.COMP / 'ap-hero.svg').read_text(encoding='utf-8')
    return [(a['id'][5:], d) for d, a in kit.parse_svg_paths(t)]


def placed_labels(h, w):
    lab = np.full((h, w), -1, int)
    for n, d in master_faces():   # bottom -> top
        lab[kit.raster(kit.transform_d(d, S, TX, TY), w, h) > 0.5] = NAMES.index(FACE_LABEL[n])
    return lab


def lab_gradient(rgb):
    lab3 = kit.srgb_to_lab(rgb)
    H, Wd = lab3.shape[:2]
    pad = np.pad(lab3, ((1, 1), (1, 1), (0, 0)), mode='edge')
    sm = sum(pad[dy:dy + H, dx:dx + Wd] for dy in range(3) for dx in range(3)) / 9.0
    gx = np.zeros((H, Wd)); gy = np.zeros((H, Wd))
    gx[:, 1:-1] = np.linalg.norm(sm[:, 2:] - sm[:, :-2], axis=-1)
    gy[1:-1] = np.linalg.norm(sm[2:] - sm[:-2], axis=-1)
    return np.hypot(gx, gy)


def seeds(h, w, mask04, erode_px=3, extra=None):
    pl = placed_labels(h, w)
    sd = np.full((h, w), -1, int)
    inner = kit.erode(mask04, 2)
    for k in range(1, len(NAMES)):
        sd[kit.erode(pl == k, erode_px) & inner] = k
    sd[~kit.dilate(mask04, 4)] = 0
    for k, pts in (extra or {}).items():     # manual seed corrections: label -> [(x, y), ...]
        for x, y in pts:
            sd[y, x] = NAMES.index(k)
    return sd


BAND, LEG = np.array([37, 88, 179.]), np.array([38, 71, 154.])   # ribbon lower band / left leg outer face at the tip
TIP_X = (187, 240)


def tip_edge(rgb):
    """The ribbon's lower band and the left leg's outer face are nearly the same blue near the tip (the
    watershed wanders there). Per column, the band's bottom edge is the step of the colour projection on the
    band -> leg axis below the cyan upper band (area method). Returns points and a cubic y(x) fit."""
    pts = []
    d = LEG - BAND
    for x in range(*TIP_X):
        s = (rgb[440:500, x] - BAND) @ d / (d @ d)
        cy = np.nonzero(s < -1.5)[0]
        start = cy.max() + 2 if len(cy) else 15
        for k in range(start, len(s) - 3):
            if s[k] < 1.0 <= s[k + 1] or s[k - 1] < 1.0 <= s[k + 2]:
                w0, w1 = max(start, k - 3), min(len(s), k + 5)
                a, b = np.median(s[w0:w0 + 2]), np.median(s[w1 - 2:w1])
                if b - a < 0.5:
                    continue
                t = np.clip((s[w0:w1] - a) / (b - a), 0, 1)
                pts.append((x + 0.5, 440 + w0 + (w1 - w0) - t.sum()))
                break
    p = np.asarray(pts)
    c = np.polyfit(p[:, 0], p[:, 1], 3)
    r = p[:, 1] - np.polyval(c, p[:, 0])
    keep = np.abs(r) < 3 * max(0.1, 1.4826 * np.median(np.abs(r)))
    c = np.polyfit(p[keep, 0], p[keep, 1], 3)
    r = p[keep, 1] - np.polyval(c, p[keep, 0])
    return p, c, float(np.sqrt(np.mean(r ** 2)))


def fix_tip_labels(rgb, lab, c, ll_crease):
    """Relabel the tip region from colour: cyan -> ribbon-upper; above the band edge -> ribbon-lower; below ->
    the leg face on its side of the crease."""
    U, Lo, lo, lb = (NAMES.index(n) for n in ('ribbon-upper', 'ribbon-lower', 'a-left-outer', 'a-left-bevel'))
    out = lab.copy()
    d = LEG - BAND
    for x in range(TIP_X[0] - 1, TIP_X[1]):
        for y in range(440, 500):
            if out[y, x] not in (U, Lo, lo, lb):
                continue
            s = (rgb[y, x] - BAND) @ d / (d @ d)
            above = (y + 0.5) < np.polyval(c, x + 0.5)
            if above and s < -1.5:
                out[y, x] = U
            elif above:
                out[y, x] = Lo
            else:
                out[y, x] = lo if (x + 0.5) < ll_crease['a'] * (y + 0.5) + ll_crease['b'] else lb
    return out


def preview(rgb, lab, out, box=BOX, k=3):
    x0, y0, x1, y1 = box
    prev = rgb.copy()
    edge = np.zeros(lab.shape, bool)
    edge[:, 1:] |= lab[:, 1:] != lab[:, :-1]
    edge[1:] |= lab[1:] != lab[:-1]
    prev[edge] = [255, 0, 0]
    Image.fromarray(prev[y0:y1, x0:x1].astype(np.uint8)).resize(((x1 - x0) * k, (y1 - y0) * k), Image.NEAREST).save(out)


if __name__ == '__main__':
    rgb = kit.load('04').astype(float)
    h, w = rgb.shape[:2]
    mask04 = np.load(kit.WORK / 'ap-' / 'mask04.npy')
    grad = lab_gradient(rgb)
    sd = seeds(h, w, mask04)
    x0, y0, x1, y1 = BOX
    sub = watershed(grad[y0:y1, x0:x1], sd[y0:y1, x0:x1])
    lab = np.zeros((h, w), np.int32)
    lab[y0:y1, x0:x1] = sub
    pts, c, rms = tip_edge(rgb)
    print('tip band edge: %d columns, cubic rms %.3f px' % (len(pts), rms))
    crease = {'a': -0.44929, 'b': 434.995}   # LL_crease from lines04 (only picks the leg label below the band)
    lab = fix_tip_labels(rgb, lab, c, crease)
    json.dump({'coef': c.tolist(), 'x_range': TIP_X, 'rms': rms, 'points': pts.tolist()}, open(W4 / 'tip04.json', 'w'), indent=1)
    np.save(W4 / 'labels04.npy', lab)
    preview(rgb, lab, W4 / 'seg04_preview.png')
    for k, n in enumerate(NAMES):
        print(k, n, int((lab == k).sum()), 'seed', int((sd == k).sum()))
