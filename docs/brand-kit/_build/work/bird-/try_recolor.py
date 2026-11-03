import sys, json; sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'); import kit
import numpy as np
from b_build import load_mesh, resolve_colors, metrics
from b_colors import fit_facets
from b_export import extend_facets
from b_place_build import render_in, bg_of, TARGETS
V, F, names = load_mesh('p3.pkl')
polys = extend_facets(V, F, 1.0)
pl = json.load(open('dry_bird-placements.json'))
for oid in sys.argv[1:]:
    a, b, c, d, e, f = pl[oid]['matrix']
    A = np.array([[a, c], [b, d]]); t = np.array([e, f])
    xf = lambda px, py: (a * px + c * py + e, b * px + d * py + f)
    img = kit.load(oid); bg = bg_of(img)
    x0, y0, x1, y1 = TARGETS[oid]['region']
    region = np.zeros(img.shape[:2], bool); region[y0:y1, x0:x1] = True
    for er, three, solid, rob in ((2, True, False, False), (2, True, False, True), (1, True, False, True), (2, False, True, True)):
        fills = fit_facets(V, F, img, xform=xf, allow_three=three, force_solid=solid, erode=er, robust=rob)
        colors, tones, snaps = resolve_colors(fills)
        rend, _ = render_in(img.shape, polys, fills, colors, A, t, bg)
        np.save('rend_%s_%d%d%d%d.npy' % (oid, er, three, solid, rob), rend)
        m, _, _, _ = metrics(img.astype(float), rend, bg, region=region)
        print(oid, 'robust', rob, 'erode %d three %-5s solid %-5s -> dE %.2f p95 %.2f eroded %.2f | tones %d snaps %d solids %d' % (
            er, three, solid, m['de_mean'], m['de_p95'], m['de_mean_eroded1'], len(tones), len(snaps), sum(g['kind'] == 'solid' for g in fills)))
