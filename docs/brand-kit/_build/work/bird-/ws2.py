"""Over-segment (seeded watershed) then merge regions whose boundary shows no colour step."""
import sys, numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'); import kit
from b_seg import label_cc
from b_ws import watershed

def step_stats(lab, labimg, r=3):
    """For each 4-adjacent pair (a,b): dE2000 between mean Lab of a-pixels and b-pixels within r px of the a|b boundary,
    plus the boundary length."""
    H, W = lab.shape
    pairs = {}
    for dy, dx in ((0,1),(1,0)):
        a = lab[:H-dy, :W-dx]; b = lab[dy:, dx:]
        m = (a != b) & (a > 0) & (b > 0)
        ys, xs = np.where(m)
        for y, x in zip(ys, xs):
            p, q = lab[y, x], lab[y+dy, x+dx]
            k = (min(p, q), max(p, q))
            pairs.setdefault(k, []).append((y, x))
    out = {}
    for (p, q), pts in pairs.items():
        if len(pts) < 6: 
            out[(p, q)] = (0.0, len(pts)); continue
        pts = np.array(pts)
        y0, x0 = pts.min(0) - r - 1; y1, x1 = pts.max(0) + r + 2
        y0, x0 = max(0, y0), max(0, x0)
        sub = lab[y0:y1, x0:x1]
        near = np.zeros(sub.shape, bool)
        near[pts[:, 0]-y0, pts[:, 1]-x0] = True
        near = kit.dilate(near, r)
        # exclude the 1-px boundary itself
        core = kit.dilate(np.isin(sub, [p]) & ~np.isin(sub, [p]), 0)
        A = near & (sub == p) & ~kit.dilate(sub == q, 1)
        B = near & (sub == q) & ~kit.dilate(sub == p, 1)
        L = labimg[y0:y1, x0:x1]
        if A.sum() < 5 or B.sum() < 5:
            out[(p, q)] = (0.0, len(pts)); continue
        out[(p, q)] = (float(kit.de2000(L[A].mean(0), L[B].mean(0))), len(pts))
    return out

if __name__ == '__main__':
    T_low = float(sys.argv[1]); T_step = float(sys.argv[2]); tag = sys.argv[3]
    e = np.load('edge_s.npy'); dw = np.load('dwhite.npy')
    fg = dw > 12
    rgb = kit.load('15')
    labimg = kit.srgb_to_lab(np.asarray(Image.fromarray(rgb).filter(ImageFilter.GaussianBlur(0.7)), float))
    core = kit.erode(fg & (e < T_low), 1)
    s = label_cc(core)
    sizes = np.bincount(s.ravel())
    keep = np.where(sizes >= 12)[0]; keep = keep[keep > 0]
    remap = np.zeros(s.max()+1, int); remap[keep] = np.arange(1, len(keep)+1)
    s = remap[s]
    print('seeds', s.max())
    lab = watershed(e, s, fg)
    np.save(f'ws_over_{tag}.npy', lab)
    it = 0
    while True:
        st = step_stats(lab, labimg)
        cand = [(v[0], k) for k, v in st.items() if v[0] < T_step]
        if not cand: break
        cand.sort()
        used = set()
        for v, (a, b) in cand:   # merge a batch of disjoint pairs per pass
            if a in used or b in used: continue
            lab[lab == b] = a; used.add(a); used.add(b)
        it += 1
        print('pass', it, 'merged', len(used)//2, 'regions', len(np.unique(lab))-1)
    u, inv = np.unique(lab, return_inverse=True); lab = inv.reshape(lab.shape)
    np.save(f'ws_{tag}.npy', lab)
    print('regions', lab.max())
