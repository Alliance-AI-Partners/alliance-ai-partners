import sys, pickle, time, numpy as np
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'); import kit
from b_export import boundary_loops
from b_place import fit_placement
V, F = pickle.load(open(sys.argv[1], 'rb'))
loops = [V[L] for L in boundary_loops(V, F)]
print('loops', len(loops), [len(L) for L in loops])
for oid, region, bg in (('05', (440, 100, 940, 480), '#FFFFFF'), ('08', (100, 150, 585, 520), '#F5F8FD')):
    img = kit.load(oid)
    m = kit.bg_mask(img, bg, 18)
    t = time.time()
    p, iou, (A, tt), mc = fit_placement(loops, m, region)
    print(oid, 'params s=%.4f th=%.3fdeg tx=%.2f ty=%.2f' % (p[0], np.degrees(p[1]), p[2], p[3]), 'IoU %.4f' % iou, 'time %.0f' % (time.time() - t))
