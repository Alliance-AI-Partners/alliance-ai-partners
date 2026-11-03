"""Scratch: internal edge map of the wave (|grad Lab| inside the eroded core), to see face boundaries."""
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import numpy as np
from PIL import Image
import kit

W = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\graphics'
X0, X1, Y0, Y1 = 1025, 1330, 495, 600
im = kit.load('02').astype(float)[Y0:Y1, X0:X1]
lab = kit.srgb_to_lab(im)
core = np.load(W + r'\core.npy')
inner = kit.erode(core, 1)
g = np.zeros(core.shape)
for ax in (0, 1):
    d = np.diff(lab, axis=ax)
    m = np.sqrt((d ** 2).sum(-1))
    if ax == 0:
        g[:-1] = np.maximum(g[:-1], m); g[1:] = np.maximum(g[1:], m)
    else:
        g[:, :-1] = np.maximum(g[:, :-1], m); g[:, 1:] = np.maximum(g[:, 1:], m)
g[~inner] = 0
base = (im * 0.35 + 255 * 0.65)
base[~core] = 255
t = np.clip(g / 12.0, 0, 1)[..., None]
out = base * (1 - t) + np.array([255, 0, 0]) * t
s = 6
Image.fromarray(out.astype(np.uint8)).resize((out.shape[1] * s, out.shape[0] * s), Image.NEAREST).save(W + r'\edges_x6.png')
