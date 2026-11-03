"""Scratch: segment the wave in original 02 into its colour bands (k-means in Lab) and save a
false-colour label map, to read off the ribbon's face topology."""
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import numpy as np
from PIL import Image
import kit

W = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\graphics'
X0, X1, Y0, Y1 = 1025, 1330, 495, 600

im = kit.load('02').astype(float)[Y0:Y1, X0:X1]
lab = kit.srgb_to_lab(im)
L, C = lab[..., 0], np.hypot(lab[..., 1], lab[..., 2])
h = np.degrees(np.arctan2(lab[..., 2], lab[..., 1])) % 360
core = (L < 72) | ((C > 38) & (h < 225))
np.save(W + r'\core.npy', core)

pts = lab[core]
K = int(sys.argv[1]) if len(sys.argv) > 1 else 7
rng = np.random.default_rng(0)
cent = pts[rng.choice(len(pts), K, replace=False)]
for _ in range(60):
    d = ((pts[:, None, :] - cent[None]) ** 2).sum(-1)
    lab_id = d.argmin(1)
    cent = np.array([pts[lab_id == k].mean(0) if (lab_id == k).any() else cent[k] for k in range(K)])
order = np.argsort(cent[:, 0])
cent = cent[order]
d = ((pts[:, None, :] - cent[None]) ** 2).sum(-1)
lab_id = d.argmin(1)
lbl = np.full(core.shape, -1)
lbl[core] = lab_id
np.save(W + r'\labels.npy', lbl)

false = np.array([[230, 25, 75], [60, 180, 75], [255, 225, 25], [0, 130, 200], [245, 130, 48],
                  [145, 30, 180], [70, 240, 240], [240, 50, 230], [210, 245, 60], [128, 128, 0]])
out = np.full(core.shape + (3,), 255, np.uint8)
for k in range(K):
    out[lbl == k] = false[k]
s = 6
Image.fromarray(out).resize((out.shape[1] * s, out.shape[0] * s), Image.NEAREST).save(W + r'\labels_x6.png')
for k in range(K):
    rgb = np.clip(np.round(np.asarray(kit.srgb_to_lab(np.zeros(3)), float)), 0, 0)
    print(k, 'false', false[k], 'Lab', np.round(cent[k], 1), 'count', int((lbl == k).sum()))
