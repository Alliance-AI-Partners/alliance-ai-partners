"""Seeded watershed + region merging on the smoothed edge map of original 15."""
import sys, heapq, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'); import kit
from b_seg import label_cc

def watershed(edge, seeds, fg):
    lab = seeds.copy()
    H, W = edge.shape
    h = []
    ys, xs = np.where(seeds > 0)
    for y, x in zip(ys, xs):
        for dy, dx in ((0,1),(0,-1),(1,0),(-1,0)):
            yy, xx = y+dy, x+dx
            if 0 <= yy < H and 0 <= xx < W and fg[yy, xx] and lab[yy, xx] == 0:
                heapq.heappush(h, (edge[yy, xx], yy, xx, lab[y, x]))
    while h:
        v, y, x, l = heapq.heappop(h)
        if lab[y, x]: continue
        lab[y, x] = l
        for dy, dx in ((0,1),(0,-1),(1,0),(-1,0)):
            yy, xx = y+dy, x+dx
            if 0 <= yy < H and 0 <= xx < W and fg[yy, xx] and lab[yy, xx] == 0:
                heapq.heappush(h, (max(v, edge[yy, xx]) if False else edge[yy, xx], yy, xx, l))
    return lab

def boundary_stats(lab, edge):
    """{(a,b): [edge values along the a|b boundary]} for 4-adjacent labels a<b (both > 0)."""
    st = {}
    for dy, dx in ((0,1),(1,0)):
        a = lab[:lab.shape[0]-dy, :lab.shape[1]-dx]; b = lab[dy:, dx:]
        ea = edge[:lab.shape[0]-dy, :lab.shape[1]-dx]; eb = edge[dy:, dx:]
        m = (a != b) & (a > 0) & (b > 0)
        for p, q, v in zip(a[m], b[m], np.maximum(ea[m], eb[m])):
            k = (min(p, q), max(p, q))
            st.setdefault(k, []).append(v)
    return st

if __name__ == '__main__':
    T_low = float(sys.argv[1]); T_merge = float(sys.argv[2])
    e = np.load('edge_s.npy'); dw = np.load('dwhite.npy')
    fg = dw > 12
    core = kit.erode(fg & (e < T_low), 1)
    s = label_cc(core)
    sizes = np.bincount(s.ravel())
    keep = np.where(sizes >= 25)[0]; keep = keep[keep > 0]
    remap = np.zeros(s.max()+1, int); remap[keep] = np.arange(1, len(keep)+1)
    s = remap[s]
    print('seeds', s.max())
    lab = watershed(e, s, fg)
    # hierarchical merge of weak boundaries
    while True:
        st = boundary_stats(lab, e)
        best = None
        for k, v in st.items():
            if len(v) < 4: continue
            med = float(np.median(v))
            if med < T_merge and (best is None or med < best[0]):
                best = (med, k)
        if best is None: break
        a, b = best[1]
        lab[lab == b] = a
    u, inv = np.unique(lab, return_inverse=True); lab = inv.reshape(lab.shape)
    np.save('ws_lab.npy', lab)
    print('regions', lab.max())
    rng = np.random.default_rng(5)
    cols = rng.integers(40, 255, (lab.max()+1, 3)); cols[0] = 255
    im = Image.fromarray(cols[lab].astype(np.uint8)).crop((255, 215, 775, 615)).resize((1560, 1200), Image.NEAREST)
    d = ImageDraw.Draw(im)
    for k in range(1, lab.max()+1):
        ys, xs = np.where(lab == k)
        cx, cy = np.median(xs), np.median(ys)
        j = np.argmin((xs-cx)**2 + (ys-cy)**2)
        d.text(((xs[j]-255)*3, (ys[j]-215)*3), str(k), fill=(0,0,0))
    im.save('ws_labels.png')
