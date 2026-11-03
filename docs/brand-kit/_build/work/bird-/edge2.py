import sys, numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'); import kit
rgb = kit.load('15')
sm = np.asarray(Image.fromarray(rgb).filter(ImageFilter.GaussianBlur(1.2)), float)
lab = kit.srgb_to_lab(sm)
H, Wd = lab.shape[:2]
def shift(arr, dy, dx):
    out = arr.copy()
    ys = slice(max(0, dy), H + min(0, dy)); yd = slice(max(0, -dy), H + min(0, -dy))
    xs = slice(max(0, dx), Wd + min(0, dx)); xd = slice(max(0, -dx), Wd + min(0, -dx))
    out[yd, xd] = arr[ys, xs]
    return out
e = np.zeros((H, Wd))
for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
    e = np.maximum(e, kit.de2000(shift(lab, -dy, -dx), shift(lab, dy, dx)))
np.save('edge_s.npy', e)
dw = np.load('dwhite.npy'); fg = dw > 12
inner = kit.erode(fg, 3)
print(np.percentile(e[inner], [10, 50, 75, 90, 95]))
v = np.where(fg, e, 0)
vis = np.clip(v / 4 * 255, 0, 255).astype(np.uint8)
Image.fromarray(vis).crop((255, 215, 775, 615)).resize((1560, 1200), Image.NEAREST).save('edge_s.png')
