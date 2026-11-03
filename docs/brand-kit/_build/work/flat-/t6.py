import sys, os
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\flat-')
import flatlib as F
from flatlib import kit, np
from PIL import Image
import build_flat as B

a = kit.load('03').astype(float)
bg = np.median(a[F.frame_mask(1024, 1024)], 0)
L, C = F.lab_chroma(a)
fg = kit.bg_mask(a, kit.rgbhex(bg), 18)
core = kit.erode(fg, 3)
cy = np.median(a[core & (C >= 25)], 0)
al = F.cov2(a, bg, cy)
r = np.asarray(Image.open(os.path.join(F.WORK, 'render_03.png')).convert('RGB'), float)
ar = F.cov2(r, F.NAVY, F.CYAN)
ro = B.measure_ring(al)
rr = B.measure_ring(ar)
for k in ('outer_box', 'inner_box', 'r_outer', 'r_inner'):
    print(k, np.round(ro[k], 3), np.round(rr[k], 3))
mo, mr = al > 0.5, ar > 0.5
ap = np.zeros((1024, 1024), bool); ap[160:870, 160:870] = True
ring_o, ring_r = mo & ~ap, mr & ~ap
print('ring px orig', ring_o.sum(), 'render', ring_r.sum(), 'iou', kit.iou(ring_o, ring_r))
err = np.zeros((1024, 1024, 3), np.uint8)
err[ring_o & ~ring_r] = (255, 0, 0); err[ring_r & ~ring_o] = (0, 255, 0); err[ring_o & ring_r] = (60, 60, 60)
Image.fromarray(err).save(os.path.join(F.WORK, 'e03_ring.png'))
# profile across the left edge at row 512
print('orig  al row512 x115..150', np.round(al[512, 115:150], 2))
print('render al row512 x115..150', np.round(ar[512, 115:150], 2))
