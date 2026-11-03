"""Scratch: segment original 15 (the faceted bird) into facets. Writes label maps + previews into work/bird-/."""
import sys
import numpy as np
from PIL import Image

sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit

W = kit.WORK / 'bird-'


def label_cc(mask, conn=4):
    """Connected components of a bool mask via min-label propagation with pointer jumping. 0 = background."""
    H, Wd = mask.shape
    lab = np.where(mask, np.arange(1, H * Wd + 1).reshape(H, Wd), 0).astype(np.int64)
    big = H * Wd + 10
    while True:
        cur = np.where(mask, lab, big)
        nb = cur.copy()
        nb[1:, :] = np.minimum(nb[1:, :], cur[:-1, :])
        nb[:-1, :] = np.minimum(nb[:-1, :], cur[1:, :])
        nb[:, 1:] = np.minimum(nb[:, 1:], cur[:, :-1])
        nb[:, :-1] = np.minimum(nb[:, :-1], cur[:, 1:])
        if conn == 8:
            nb[1:, 1:] = np.minimum(nb[1:, 1:], cur[:-1, :-1])
            nb[:-1, :-1] = np.minimum(nb[:-1, :-1], cur[1:, 1:])
            nb[1:, :-1] = np.minimum(nb[1:, :-1], cur[:-1, 1:])
            nb[:-1, 1:] = np.minimum(nb[:-1, 1:], cur[1:, :-1])
        new = np.where(mask, nb, 0)
        # pointer jumping: lab -> lab[lab]
        flat = new.ravel()
        idx = flat[flat > 0] - 1
        jump = flat.copy()
        jump[flat > 0] = np.minimum(flat[flat > 0], new.ravel()[idx])
        new = jump.reshape(H, Wd)
        if np.array_equal(new, lab):
            break
        lab = new
    # relabel 1..n
    u, inv = np.unique(lab, return_inverse=True)
    return inv.reshape(H, Wd)


if __name__ == '__main__':
    rgb = kit.load('15').astype(float)
    lab = kit.srgb_to_lab(rgb)
    dw = kit.de2000(lab, kit.srgb_to_lab(np.array([255., 255, 255])))
    np.save(W / 'dwhite.npy', dw)
    fg = dw > 12
    # color edges: dE2000 between pixel and its neighbor two steps away (both axes)
    e = np.zeros(dw.shape)
    for dy, dx in ((0, 2), (2, 0), (2, 2), (2, -2)):
        a = lab[max(0, -dy):lab.shape[0] - max(0, dy), max(0, -dx):lab.shape[1] - max(0, dx)] if False else None
    H, Wd = dw.shape
    def shift(arr, dy, dx):
        out = np.empty_like(arr)
        out[...] = arr
        ys = slice(max(0, dy), H + min(0, dy)); yd = slice(max(0, -dy), H + min(0, -dy))
        xs = slice(max(0, dx), Wd + min(0, dx)); xd = slice(max(0, -dx), Wd + min(0, -dx))
        out[yd, xd] = arr[ys, xs]
        return out
    for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
        d = kit.de2000(shift(lab, -dy, -dx), shift(lab, dy, dx))
        e = np.maximum(e, d)
    np.save(W / 'edge.npy', e)
    vis = np.clip(e / 15 * 255, 0, 255).astype(np.uint8)
    Image.fromarray(vis).crop((255, 215, 775, 615)).resize((1040, 800), Image.NEAREST).save(W / 'edge.png')
    print('edge stats inside fg', np.percentile(e[fg], [10, 50, 75, 90, 95, 99]))
