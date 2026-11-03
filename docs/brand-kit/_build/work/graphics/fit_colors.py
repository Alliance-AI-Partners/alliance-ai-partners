"""Scratch: per-face gradient fit for the wave (pixels well inside each face region of original 02)."""
import sys
import numpy as np
import kit
import wavegeom as g
from gradfit import fit_gradient


def poly_d(q):
    return "M" + " L".join("%.3f %.3f" % (x, y) for x, y in q) + " Z"


def face_pixels(M, name, erode=1):
    F = g.faces(M)
    q = g.outline(F[name])
    cov = kit.raster(poly_d(q), 1376, 768)
    inner = kit.erode(cov > 0.999, erode) if erode else cov > 0.999
    ys, xs = np.nonzero(inner)
    return np.stack([xs + 0.5, ys + 0.5], -1), ys, xs, cov


if __name__ == '__main__':
    M = g.load()
    im = kit.load('02').astype(float)
    Ks = [int(a) for a in sys.argv[1:]] or [4, 6, 8, 10, 12]
    for name in "ABCD":
        xy, ys, xs, _ = face_pixels(M, name)
        rgb = im[ys, xs]
        for K in Ks:
            r = fit_gradient(xy, rgb, K)
            print(name, len(xy), 'K', K, 'ang %.1f' % r["angle_deg"], 'dE mean %.2f p95 %.2f' % (r["de_mean"], r["de_p95"]))
