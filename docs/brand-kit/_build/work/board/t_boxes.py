"""Scratch: tight bboxes (alpha>=0.5) of each run's search box + edge-touch check (board agent)."""
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\board')
import numpy as np
import textfit as tf
from runs import RUNS, INK0
import kit
img = kit.load('02')
for rid, s, box, ink, gi in RUNS:
    inks = [INK0[ink]] + [INK0[v] for v in sorted(set(gi.values()))]
    x0, y0, x1, y1 = box
    a, w = tf.unmix(img[y0:y1, x0:x1].astype(float), inks)
    m = a >= 0.5
    if not m.any():
        print(rid, 'EMPTY'); continue
    bx0, by0, bx1, by1 = tf.bbox_of(m)
    touch = []
    if bx0 == 0: touch.append('L')
    if by0 == 0: touch.append('T')
    if bx1 == x1 - x0: touch.append('R')
    if by1 == y1 - y0: touch.append('B')
    # edge rows/cols alpha sums to detect spill from neighbours
    edge = [round(float(a[0].sum()), 1), round(float(a[-1].sum()), 1), round(float(a[:, 0].sum()), 1), round(float(a[:, -1].sum()), 1)]
    print('%-15s tight=(%d,%d,%d,%d) h=%d w=%d touch=%s edge(T,B,L,R)=%s' % (rid, x0 + bx0, y0 + by0, x0 + bx1, y0 + by1, by1 - by0, bx1 - bx0, ''.join(touch), edge))
