import sys, numpy as np
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'); import kit
from b_seg import label_cc

def mode_filter(lab, it=2):
    for _ in range(it):
        H, W = lab.shape
        stack = np.stack([np.roll(np.roll(lab, dy, 0), dx, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1)])
        n = lab.max() + 1
        best = lab.copy(); bestc = np.zeros(lab.shape, int)
        for k in range(n):
            c = (stack == k).sum(0)
            m = c > bestc
            best[m] = k; bestc[m] = c[m]
        lab = np.where(bestc >= 5, best, lab)
    return lab

def keep_largest(lab):
    out = lab.copy()
    for k in range(1, lab.max() + 1):
        m = lab == k
        if not m.any(): continue
        cc = label_cc(m)
        sizes = np.bincount(cc.ravel()); sizes[0] = 0
        big = sizes.argmax()
        out[(cc > 0) & (cc != big)] = -1
    # fill -1 from neighbours
    for _ in range(50):
        un = out == -1
        if not un.any(): break
        for dy, dx in ((0,1),(0,-1),(1,0),(-1,0)):
            nb = np.roll(np.roll(out, dy, 0), dx, 1)
            t = un & (nb >= 0) & (out == -1)
            out[t] = nb[t]
    return out

if __name__ == '__main__':
    lab = np.load(sys.argv[1])
    lab = mode_filter(lab, 2)
    lab = keep_largest(lab)
    # background islands inside the bird are allowed (white gaps), but tiny ones (< 6 px) are noise
    bg = lab == 0
    cc = label_cc(bg)
    sizes = np.bincount(cc.ravel())
    for k in np.nonzero((sizes < 6) & (np.arange(len(sizes)) > 0))[0]:
        lab[cc == k] = -1
    lab = keep_largest(np.where(lab == -1, -1, lab)) if (lab == -1).any() else lab
    np.save(sys.argv[2], lab)
    print('labels', np.unique(lab).size - 1)
