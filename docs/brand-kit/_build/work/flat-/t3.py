import sys, os
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
import numpy as np

W = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\flat-'
res = eval(open(os.path.join(W, 't1.txt')).read())
cyan_d = [p for p, f in res if f == '#00D5FF'][0]
subs = kit.parse_d(cyan_d)


def unit(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


for s in subs:
    pts = [np.array(s['start'])]
    segs = s['segs']
    cur = np.array(s['start'])
    tin, tout, ends = [], [], []
    for g in segs:
        if g[0] == 'L':
            e = np.array(g[1:3]); t0 = t1 = unit(e - cur)
        else:
            p1, p2, e = np.array(g[1:3]), np.array(g[3:5]), np.array(g[5:7])
            t0 = unit(p1 - cur) if np.linalg.norm(p1 - cur) > 1e-6 else unit(p2 - cur)
            t1 = unit(e - p2) if np.linalg.norm(e - p2) > 1e-6 else unit(e - p1)
        tin.append(t1); tout.append(t0); ends.append(e); cur = e
    n = len(segs)
    out = []
    for k in range(n):
        a_in, a_out = tin[k], tout[(k + 1) % n]
        ang = np.degrees(np.arccos(np.clip(a_in @ a_out, -1, 1)))
        out.append((round(float(ang), 1), tuple(np.round(ends[k], 1))))
    print('subpath segs', n)
    print(sorted([o[0] for o in out])[::-1][:30])
    print([o for o in out if o[0] > 8])
