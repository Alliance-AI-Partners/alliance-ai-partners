import sys, json, numpy as np
sys.path.insert(0, '.')
from b_mesh import build, facet_cycles
from b_drawmesh import draw
from b_seeds import SEEDS
lab = np.load('lab_clean.npy')
verts, edges = build(lab, tol=float(sys.argv[1]), cluster=float(sys.argv[2]))
cyc = facet_cycles(edges, lab.max())
names = list(SEEDS)
bad = 0
for f, (c, left) in cyc.items():
    if left: print('facet', f, names[f-1], 'unclosed, leftover', left); bad += 1
print('verts', len(verts), 'edges', len(edges), 'bad', bad)
print('vertex counts', {names[f-1]: len(c) for f, (c, l) in cyc.items()})
json.dump({'verts': verts.tolist(), 'cycles': {str(f): c for f, (c, l) in cyc.items()}}, open('mesh0.json', 'w'))
cy = {f: c for f, (c, l) in cyc.items()}
draw(verts, cy, 255, 215, 775, 615, 3, 'mesh0.png', labels=False)
draw(verts, cy, 480, 290, 680, 470, 5, 'mesh0_c.png')
