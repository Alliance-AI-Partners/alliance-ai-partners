"""Scratch: draw the fitted wave model curves over a zoom of original 02."""
import json
import numpy as np
from PIL import Image, ImageDraw
import kit
from wavefit import evaluate, W

M = json.load(open(W + r'\wave_model.json'))
ek = np.array(M["edge_knots"])
X0, X1, Y0, Y1, s = 1025, 1330, 495, 600, 6
im = kit.load('02')
base = Image.fromarray(im[Y0:Y1, X0:X1]).resize(((X1 - X0) * s, (Y1 - Y0) * s), Image.BICUBIC)
d = ImageDraw.Draw(base)


def poly(xs, ys, col):
    d.line([((x - X0) * s, (y - Y0) * s) for x, y in zip(xs, ys)], fill=col, width=2)


xs = np.linspace(M["XL"], M["XR"], 600)
poly(xs, evaluate(ek, np.array(M["top"]), xs), (255, 0, 0))
poly(xs, evaluate(ek, np.array(M["bot"]), xs), (255, 0, 0))
for name, b in M["bounds"].items():
    k = np.array(b["knots"])
    xb = np.linspace(k[0], k[-1], 400)
    poly(xb, evaluate(k, np.array(b["vals"]), xb, clamp=tuple(b["clamp"])), (255, 255, 0))
base.save(W + r'\model_overlay_x6.png')
