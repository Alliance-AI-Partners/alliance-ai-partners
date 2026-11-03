import sys, json, time, pickle, numpy as np
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'); import kit
from b_fit import Model
V, F = pickle.load(open(sys.argv[1], 'rb'))
img = kit.load('15')
M = Model(img, V, F, (258, 217, 768, 608), ss=4)
print('start err %.0f verts %d' % (M.error(), len(M.inc)))
rows = []
for v in sorted(M.inc):
    if M.removable(v):
        d = M.remove_delta(v)
        rows.append((d, M.chord_dev(v), v))
rows.sort()
for d, dev, v in rows:
    print('v%-4d dE %9.0f  dev %.2f  facets %s' % (v, d, dev, sorted(M.inc[v])))
