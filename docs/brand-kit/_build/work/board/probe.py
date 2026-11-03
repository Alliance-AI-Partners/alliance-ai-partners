"""Scratch probes of original 02: line profiles and colors (board agent)."""
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
import numpy as np

a = kit.load('02').astype(float)
BG = np.array([245.2, 249.2, 252.6])


def rowprof(y0, y1, x0, x1):
    """mean RGB per row in [y0,y1) over columns [x0,x1)."""
    return a[y0:y1, x0:x1].mean(1)


def colprof(x0, x1, y0, y1):
    return a[y0:y1, x0:x1].mean(0)


def show(label, prof, start):
    print(label)
    for i, p in enumerate(prof):
        d = BG - p
        print('  %4d  %6.1f %6.1f %6.1f   dsum=%6.1f' % (start + i, p[0], p[1], p[2], d.sum()))


if __name__ == '__main__':
    cmd = sys.argv[1]
    v = list(map(int, sys.argv[2:]))
    if cmd == 'row':
        show('rows', rowprof(*v), v[0])
    elif cmd == 'col':
        show('cols', colprof(*v), v[0])
