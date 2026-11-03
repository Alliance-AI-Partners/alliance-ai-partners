"""Scratch: contrast-enhanced crop to reveal faint guides (board agent)."""
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
import numpy as np
from PIL import Image
a = kit.load('02').astype(float)
BG = np.array([245.2, 249.2, 252.6])
name, x0, y0, x1, y1, s, gain = sys.argv[1], *map(int, sys.argv[2:7]), float(sys.argv[7])
d = np.clip(BG - a, -255, 255).mean(-1)          # darkness vs bg
v = np.clip(255 - d * gain, 0, 255).astype(np.uint8)
Image.fromarray(v[y0:y1, x0:x1]).resize(((x1 - x0) * s, (y1 - y0) * s), Image.NEAREST).save(kit.WORK / 'board' / (name + '.png'))
