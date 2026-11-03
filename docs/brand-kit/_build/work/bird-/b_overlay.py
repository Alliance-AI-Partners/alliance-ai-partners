import sys, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'); import kit
def overlay(lab, x0, y0, x1, y1, z, out, img=None):
    img = kit.load('15') if img is None else img
    c = np.repeat(np.repeat(img[y0:y1, x0:x1], z, 0), z, 1).copy()
    L = np.repeat(np.repeat(lab[y0:y1, x0:x1], z, 0), z, 1)
    b = np.zeros(L.shape, bool)
    b[:-1] |= L[:-1] != L[1:]; b[:, :-1] |= L[:, :-1] != L[:, 1:]
    c[b] = (255, 0, 0)
    im = Image.fromarray(c)
    d = ImageDraw.Draw(im)
    for k in np.unique(lab[y0:y1, x0:x1]):
        if k == 0: continue
        ys, xs = np.where(lab == k)
        cx, cy = np.median(xs), np.median(ys)
        j = np.argmin((xs-cx)**2 + (ys-cy)**2)
        if x0 <= xs[j] < x1 and y0 <= ys[j] < y1:
            d.text(((xs[j]-x0)*z, (ys[j]-y0)*z), str(k), fill=(255, 255, 0))
    im.save(out)
if __name__ == '__main__':
    lab = np.load(sys.argv[1])
    x0, y0, x1, y1, z = map(int, sys.argv[2:7])
    overlay(lab, x0, y0, x1, y1, z, sys.argv[7])
