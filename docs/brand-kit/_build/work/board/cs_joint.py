"""Clear-space diagram, joint fit (board agent): one shared red for the dashed grid, arrows and corner
crosses (they are one guide colour); per-element geometry re-fitted with that colour fixed, colour
re-solved jointly through the JPEG 4:2:0 model, alternated three times. Writes cs_joint.json."""
import json
import sys

sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\board')
import numpy as np
import kit
import jpegsim as J
import textfit as tf
import thin
from cs_fit import arrow_polys, cross_polys

W = kit.WORK / 'board'
IMG = thin.IMG
BG = thin.BG
F = json.loads((W / 'cs_fit.json').read_text())
HN = ['cs-h1', 'cs-h2', 'cs-h3', 'cs-h4']
VN = ['cs-v1', 'cs-v2', 'cs-v3', 'cs-v4']

# pixels that belong to something else: the gradient mark (bluish) and the small 'x' labels
reg = IMG
other = (reg[..., 2] - reg[..., 0]) > 25
other = kit.dilate(other, 2)
for (x0, y0, x1, y1) in [(862, 516, 879, 533), (862, 683, 879, 700), (726, 582, 743, 598), (960, 581, 977, 598)]:
    other[y0:y1, x0:x1] = True


def dash_polys(e, ext):
    """Dashes of dashed line e across extent ext=(a, b) along the line."""
    o, c, w = e["orient"], e["center"], e["width"]
    s0, P, D = e["s0"], e["period"], e["dash"]
    out = []
    for k in range(-3, 40):
        a, b = s0 + k * P, s0 + k * P + D
        if b < ext[0] - 1 or a > ext[1] + 1:
            continue
        a, b = max(a, ext[0]), min(b, ext[1])
        out.append(thin.rect(a, c - w / 2, b, c + w / 2) if o == 'h' else thin.rect(c - w / 2, a, c + w / 2, b))
    return out


def element_specs():
    """(name, box, mask, build(params) -> polys, p0, steps, unpack) for every red element."""
    specs = []
    for n in HN + VN:
        e = F[n]
        c = e["center"]
        if e["orient"] == 'h':
            ext = (714.0, 989.0)
            box = (713, int(np.floor(c)) - 4, 990, int(np.floor(c)) + 5)
        else:
            ext = (503.5, 711.5)
            box = (int(np.floor(c)) - 4, 503, int(np.floor(c)) + 5, 712)
        x0, y0, x1, y1 = box
        mask = ~other[y0:y1, x0:x1]
        # keep the crossings with perpendicular lines out of the residual (both lines claim them)
        cross = HN if e["orient"] == 'v' else VN
        for m in cross:
            cc = F[m]["center"]
            if e["orient"] == 'h':
                i = int(np.floor(cc)) - x0
                mask[:, max(0, i - 2):i + 3] = False
            else:
                i = int(np.floor(cc)) - y0
                mask[max(0, i - 2):i + 3, :] = False

        def build(p, e=e, ext=ext):
            q = dict(e, center=p[0], width=p[1], s0=p[2], period=p[3], dash=p[4])
            return dash_polys(q, ext)
        specs.append((n, box, mask, build, [c, e["width"], e["s0"], e["period"], e["dash"]], [0.15, 0.15, 0.25, 0.01, 0.2]))
    arrows = {'cs-arrow-top': (850, 500, 866, 542), 'cs-arrow-bottom': (850, 674, 866, 714),
              'cs-arrow-left': (711, 596, 757, 609), 'cs-arrow-right': (946, 596, 992, 609)}
    for n, box in arrows.items():
        a = F[n]
        x0, y0, x1, y1 = box
        mask = ~other[y0:y1, x0:x1]
        for m in (HN if a["vertical"] else VN):
            cc = F[m]["center"]
            if a["vertical"]:
                i = int(np.floor(cc)) - y0
                mask[max(0, i - 1):i + 2, :] = False
            else:
                i = int(np.floor(cc)) - x0
                mask[:, max(0, i - 1):i + 2] = False
        p0 = [a["axis"], a["tip_a"], a["tip_b"], a["shaft_width"], a["head_length"], a["head_half_width"]]
        specs.append((n, box, mask, lambda p, v=a["vertical"]: arrow_polys(p, v), p0, [0.2, 0.3, 0.3, 0.15, 0.4, 0.3]))
    for n in ['cs-cross-tl', 'cs-cross-tr', 'cs-cross-bl', 'cs-cross-br']:
        c = F[n]
        box = (int(c["cx"]) - 13, int(c["cy"]) - 13, int(c["cx"]) + 14, int(c["cy"]) + 14)
        x0, y0, x1, y1 = box
        specs.append((n, box, ~other[y0:y1, x0:x1], cross_polys, [c["cx"], c["cy"], c["half"], c["width"]], [0.2, 0.2, 0.3, 0.15]))
    return specs


def rms_fixed(cov, box, ink, mask):
    x0, y0, x1, y1 = box
    pred = J.jpeg420(BG + cov[..., None] * (np.asarray(ink) - BG), x0, y0)
    d = (pred - IMG[y0:y1, x0:x1])[mask]
    return float(np.sqrt((d ** 2).mean()))


def ls_rows(cov, box, mask):
    x0, y0, x1, y1 = box
    base = J.jpeg420(np.broadcast_to(BG, cov.shape + (3,)), x0, y0, clip=False)
    B = []
    for k in range(3):
        e = np.zeros(3); e[k] = 1.0
        B.append(J.jpeg420(BG + cov[..., None] * e, x0, y0, clip=False) - base)
    m3 = np.repeat(mask[..., None], 3, -1)
    return np.stack([b[m3] for b in B], 1), (IMG[y0:y1, x0:x1] - base)[m3]


if __name__ == '__main__':
    specs = element_specs()
    geo = {n: np.array(p0, float) for n, box, mask, build, p0, steps in specs}
    inks0 = [F[n]["ink"] for n in F]
    ink = np.median(np.array(inks0), 0)
    print('start ink', ink.round(1), kit.rgbhex(ink))
    for it in range(3):
        for n, box, mask, build, p0, steps in specs:
            f = lambda p, box=box, mask=mask, build=build: rms_fixed(thin.cover_polys(build(p), box, 8), box, ink, mask)
            p, v = tf.nelder_mead(f, geo[n], steps, 160)
            geo[n] = p
        As, ys = [], []
        for n, box, mask, build, p0, steps in specs:
            A, y = ls_rows(thin.cover_polys(build(geo[n]), box, 8), box, mask)
            As.append(A); ys.append(y)
        d, *_ = np.linalg.lstsq(np.concatenate(As), np.concatenate(ys), rcond=None)
        ink = BG + d
        tot = [rms_fixed(thin.cover_polys(build(geo[n]), box, 8), box, ink, mask) for n, box, mask, build, p0, steps in specs]
        print('iter %d ink=%s %s  mean rms=%.2f' % (it, ink.round(1), kit.rgbhex(ink), np.mean(tot)), flush=True)
    out = {"ink": ink.tolist(), "elements": {}}
    for (n, box, mask, build, p0, steps), r in zip(specs, tot):
        out["elements"][n] = {"params": geo[n].tolist(), "rms": r, "box": list(box)}
        print('  %-16s %s rms=%.2f' % (n, np.round(geo[n], 3).tolist(), r))
    (W / 'cs_joint.json').write_text(json.dumps(out, indent=1))
