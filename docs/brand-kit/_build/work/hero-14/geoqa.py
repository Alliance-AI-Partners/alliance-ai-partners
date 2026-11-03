"""Geometry QA of a hero-14 build: anchors, micro segments, and joins that are neither smooth (G1) nor a
clear corner. usage: python geoqa.py hero14_vN.json|file.svg"""
import sys
import numpy as np
from common import kit
from ov import load_geo


def tangents(start, g):
    p0 = np.asarray(start, float)
    if g[0] == 'L':
        p1 = np.asarray(g[1:3], float)
        return p1 - p0, p1 - p0, p1
    c1, c2, p1 = (np.asarray(g[i:i + 2], float) for i in (1, 3, 5))
    t0 = c1 - p0 if np.hypot(*(c1 - p0)) > 1e-6 else (c2 - p0)
    t1 = p1 - c2 if np.hypot(*(p1 - c2)) > 1e-6 else (p1 - c1)
    return t0, t1, p1


def ang(a, b):
    na, nb = np.hypot(*a), np.hypot(*b)
    if na < 1e-9 or nb < 1e-9:
        return 0.0
    return float(np.degrees(np.arccos(np.clip(a @ b / na / nb, -1, 1))))


def qa(name, d, micro=1.0, soft=(1.5, 20.0)):
    issues = []
    nseg = 0
    for sp in kit.parse_d(d):
        segs = sp['segs']
        pts = [np.asarray(sp['start'], float)]
        tin, tout = [], []
        cur = sp['start']
        for g in segs:
            t0, t1, p1 = tangents(cur, g)
            tout.append(t0); tin.append(t1)
            pts.append(p1)
            cur = tuple(p1)
        nseg += len(segs)
        m = len(segs)
        closed = sp['closed'] and np.hypot(*(pts[-1] - pts[0])) < 1e-3
        for k in range(m):
            L = np.hypot(*(pts[k + 1] - pts[k]))
            if L < micro:
                issues.append(f'micro segment {L:.2f}px at ({pts[k][0]:.1f},{pts[k][1]:.1f})')
        for k in range(1, m + (1 if closed else 0)):
            a = ang(tin[k - 1], tout[k % m])
            if soft[0] < a < soft[1]:
                p = pts[k % m] if k < m else pts[0]
                issues.append(f'kinked join {a:.1f} deg at ({p[0]:.1f},{p[1]:.1f}) [{segs[k - 1][0]}->{segs[k % m][0]}]')
    return nseg, issues


if __name__ == '__main__':
    geo = load_geo(sys.argv[1])
    for n, d in geo.items():
        if not isinstance(d, str):
            continue
        nseg, iss = qa(n, d)
        print(f'{n:18s} segments {nseg:3d}  issues {len(iss)}')
        for s in iss:
            print('    ', s)
