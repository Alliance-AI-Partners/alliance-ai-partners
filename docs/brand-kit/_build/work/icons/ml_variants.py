"""Scratch: A/B alternative machine-learning layouts against the current one."""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import build_icons as B  # noqa: E402
from build_icons import circle, dot, edge, line, SW  # noqa: E402


def net(layers, r=3.5, ro=5.0, skip=()):
    els, k = [], 0
    for li in range(len(layers) - 1):
        for a in layers[li]:
            for b in layers[li + 1]:
                if (a, b) in skip:
                    continue
                k += 1
                rb = ro - SW / 2 if li + 1 == len(layers) - 1 else r
                els.append(line("edge-%d" % k, *edge(a, b, r, rb)))
    n = 0
    for layer in layers[:-1]:
        for c in layer:
            n += 1
            els.append(circle("node-%d" % n, *c, r))
    els.append(dot("output", *layers[-1][0], ro))
    return els


def ml_131():
    return net([[(9.0, 24.0)], [(24.0, 9.5), (24.0, 24.0), (24.0, 38.5)], [(39.0, 24.0)]])


def ml_221_x():
    x2 = 9.5 + 29 / math.tan(math.radians(B.A_LEG))
    a, b, c, d = (9.5, 9.5), (9.5, 38.5), (x2, 9.5), (x2, 38.5)
    return net([[a, b], [c, d], [(38.5, 24.0)]], skip={(a, c), (b, d)})


def ml_31():
    return net([[(9.5, 9.5), (9.5, 24.0), (9.5, 38.5)], [(37.5, 24.0)]])


def ml_231():
    return net([[(8.5, 16.0), (8.5, 32.0)], [(22.0, 9.0), (22.0, 24.0), (22.0, 39.0)], [(38.5, 24.0)]], r=3.0)


B.ICONS = [("ml-current", "", B.machine_learning), ("ml-131", "", ml_131), ("ml-221-x", "", ml_221_x),
           ("ml-31", "", ml_31), ("ml-231", "", ml_231)]
B.VARIANTS = []
B.main("mlab")
