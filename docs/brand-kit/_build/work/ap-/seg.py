"""Seeded watershed segmentation of the hero AP mark (original 06) into its 3D faces.
Writes work/ap-/labels06.npy (int label map) and a colored preview."""
import heapq
import sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit

W = kit.WORK / 'ap-'

# face name -> seed polylines (orig 06 pixel coords). Label 0 = background.
SEEDS = {
    'bg': [[(170, 300), (520, 300)], [(160, 720), (860, 720)], [(380, 470), (420, 500)], [(400, 640), (480, 640)],
           [(660, 420), (700, 460)], [(700, 650), (800, 650)], [(160, 400), (250, 400)], [(525, 445), (532, 445)],
           [(870, 400), (870, 600)], [(640, 640), (700, 640)]],
    'a-left-outer': [[(380, 330), (290, 520)], [(200, 695), (212, 680)]],
    'a-left-bevel': [[(425, 330), (340, 500)], [(255, 690), (268, 665)]],
    'a-right-inner': [[(440, 400), (478, 500)], [(570, 690), (555, 665)]],
    'a-right-outer': [[(470, 360), (505, 470)], [(620, 690), (597, 645)]],
    'ribbon-upper': [[(300, 572), (470, 566)], [(520, 530), (550, 470)], [(560, 450), (560, 335)],
                     [(600, 330), (780, 340)], [(830, 380), (845, 430), (832, 505)]],
    'ribbon-lower': [[(250, 615), (460, 610)], [(505, 590), (560, 540), (598, 470), (600, 380)]],
    'p-bowl-fold': [[(640, 370), (760, 385), (795, 405)]],
    'p-bowl-lower': [[(650, 515), (750, 512)], [(800, 470), (805, 500)]],
    'p-bowl-under': [[(650, 560), (770, 558)]],
    'p-stem': [[(605, 600), (612, 615)]],
}
NAMES = list(SEEDS)


def seeds_mask(shape):
    lab = np.full(shape, -1, np.int32)
    for k, name in enumerate(NAMES):
        im = Image.new('L', (shape[1], shape[0]), 0)
        d = ImageDraw.Draw(im)
        for pl in SEEDS[name]:
            d.line(pl, fill=255, width=3)
        lab[np.asarray(im) > 0] = k
    return lab


def watershed(grad, lab):
    H, Wd = grad.shape
    out = lab.copy()
    heap = []
    ys, xs = np.nonzero(out >= 0)
    for y, x in zip(ys, xs):
        heapq.heappush(heap, (0.0, int(y), int(x)))
    g = grad
    while heap:
        p, y, x = heapq.heappop(heap)
        l = out[y, x]
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yy, xx = y + dy, x + dx
            if 0 <= yy < H and 0 <= xx < Wd and out[yy, xx] < 0:
                out[yy, xx] = l
                heapq.heappush(heap, (max(p, float(g[yy, xx])), yy, xx))
    return out


if __name__ == '__main__':
    rgb = kit.load('06').astype(float)
    lab3 = kit.srgb_to_lab(rgb)
    # gradient magnitude on a lightly smoothed Lab image (3x3 box) to tame JPEG noise
    pad = np.pad(lab3, ((1, 1), (1, 1), (0, 0)), mode='edge')
    sm = sum(pad[dy:dy + 1024, dx:dx + 1024] for dy in range(3) for dx in range(3)) / 9.0
    gx = np.zeros(sm.shape[:2]); gy = np.zeros(sm.shape[:2])
    gx[:, 1:-1] = np.linalg.norm(sm[:, 2:] - sm[:, :-2], axis=-1)
    gy[1:-1] = np.linalg.norm(sm[2:] - sm[:-2], axis=-1)
    grad = np.hypot(gx, gy)
    lab = seeds_mask(grad.shape)
    # restrict the flood to a crop around the mark for speed
    y0, y1, x0, x1 = 290, 730, 150, 880
    sub = watershed(grad[y0:y1, x0:x1], lab[y0:y1, x0:x1])
    full = np.zeros((1024, 1024), np.int32)
    full[y0:y1, x0:x1] = sub
    np.save(W / 'labels06.npy', full)
    # preview: mean color per label + boundaries
    prev = np.zeros_like(rgb)
    for k in range(len(NAMES)):
        m = full == k
        if m.any():
            prev[m] = np.median(rgb[m], 0)
    edge = np.zeros(full.shape, bool)
    edge[:, 1:] |= full[:, 1:] != full[:, :-1]
    edge[1:] |= full[1:] != full[:-1]
    prev[edge] = [255, 0, 0]
    Image.fromarray(prev.astype(np.uint8)).crop((160, 300, 870, 720)).resize((1420, 840), Image.NEAREST).save(W / 'seg_preview.png')
    for k, n in enumerate(NAMES):
        print(k, n, int((full == k).sum()))
