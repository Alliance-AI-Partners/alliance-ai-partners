"""Re-fit the master bird (p3.pkl topology: 33 facets, 73 shared vertices) to original 08 / 05 in that
original's own pixel space.

  python b_source.py opt 08     similarity placement (fit/bird-placements.json) -> vertex coordinate descent on
                                08's pixels (ss 4: steps 4 .. 0.25 px, again 1 .. 0.25 px; then ss 8: 0.25, 0.125 px)
                                -> src08.pkl
  python b_source.py build 08   fills from 08's pixels -> components/bird-08.svg, fit/bird-08.json,
                                verify/bird_08_diff.png, 'source_space' entry in fit/bird-placements.json
"""
import sys, re, json, pickle, time
import numpy as np
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
import b_fit
from b_fit import Model, cover
from b_build import load_mesh, metrics, zoom_sheet, svg_text, fill_doc, WORKD
from b_colors import fit_facets, family, interior_samples, THREE_GAIN, THREE_ABS
from b_export import extend_facets, fit_gradient_k
from b_place_build import bg_of, TARGETS

SEAM = 1.0      # px (source space) a lower facet runs under every later facet it shares an edge with
SNAP_DE = 2.0   # snap a fitted colour to a core palette colour only this close (fidelity first)
MERGE_DE = 2.0  # near-identical fitted colours (every member within this of the merged tone) share one hex
MIN_SAMPLES = 40  # a facet with fewer reliable interior pixels (a sliver whose mean is edge blur) borrows the fill
                  # of the neighbour it shares the longest edge with
CFG = {'08': dict(solid=False, style='shaded: one linear gradient (1-3 stops, userSpaceOnUse) per facet, '
                                     'least-squares fitted to the eroded facet interior of 08; 1 stop = solid'),
       '05': dict(solid=True, style='flat: one solid colour per facet (mean of the eroded facet interior of 05)')}


def log(*a):
    print(*a, flush=True)


def placed_master(oid):
    V, F, names = load_mesh(WORKD / 'p3.pkl')
    a, b, c, d, e, f = json.load(open(kit.FIT / 'bird-placements.json'))[oid]['matrix']
    return V @ np.array([[a, c], [b, d]]).T + np.array([e, f]), F, names


def bird_box(img, bg, oid, pad=6):
    """Bird bbox (+pad) inside the TARGETS region, which keeps the wordmark out."""
    x0, y0, x1, y1 = TARGETS[oid]['region']
    reg = np.zeros(img.shape[:2], bool); reg[y0:y1, x0:x1] = True
    ys, xs = np.nonzero(kit.bg_mask(img, bg, 18) & reg)
    return (max(x0, int(xs.min()) - pad), max(y0, int(ys.min()) - pad),
            min(x1, int(xs.max()) + 1 + pad), min(y1, int(ys.max()) + 1 + pad))


def max_cover(V, F, box, ss=4):
    x0, y0, x1, y1 = box
    S = np.zeros((y1 - y0, x1 - x0))
    for f in F:
        S += cover(V[f], x0, y0, x1 - x0, y1 - y0, ss)
    return float(S.max())


def optimise(oid):
    img = kit.load(oid)
    bg = bg_of(img)
    b_fit.WHITE = kit.hexrgb(bg)   # unpainted pixels of the render model = this original's background
    V, F, names = placed_master(oid)
    box = bird_box(img, bg, oid)
    t = time.time()
    M = Model(img, V, F, box, ss=4)
    log('%s box %s bg %s start err %.0f' % (oid, box, bg, M.error()))
    M.optimize(steps=(4.0, 2.0, 1.0, 0.5, 0.25), sweeps=8, log=log)
    M.optimize(steps=(1.0, 0.5, 0.25), sweeps=8, log=log)   # second pass on refreshed colour fields
    M8 = Model(img, M.V, M.F, box, ss=8)
    log('ss8 err %.0f' % M8.error())
    M8.optimize(steps=(0.25, 0.125), sweeps=10, log=log)
    mc = max_cover(M8.V, M8.F, box)
    log('max coverage sum %.3f' % mc)
    assert mc <= 1.001, 'facets overlap'
    move = np.hypot(*(M8.V - V).T)
    log('vertex moves px: mean %.2f max %.2f (v%d)' % (move.mean(), move.max(), int(move.argmax())))
    pickle.dump((M8.V, M8.F, names), open(WORKD / ('src%s.pkl' % oid), 'wb'))
    log('final err %.0f time %.0f s' % (M8.error(), time.time() - t))


def resolve(fills, oid):
    """Fidelity-first colours. Every fitted stop keeps its measured colour unless a core palette colour is
    within SNAP_DE; the rest are merged cheapest-first, a merged tone being the sample-weighted mean of its
    members (big facets keep their colour, slivers join them), and only while every member stays within
    MERGE_DE of the merged hex. Returns ({(facet, stop): (hex, palette name | None)}, tones)."""
    out, tones, free = {}, {}, []
    for i, g in enumerate(fills):
        for j, (off, c) in enumerate(g['stops']):
            c = np.clip(np.asarray(c, float), 0, 255)
            name, hx, de = kit.nearest_palette(c)
            if de <= SNAP_DE:
                out[(i, j)] = (hx, name)
                tones.setdefault(hx, dict(name=name, hex=hx, palette=True, members=[]))['members'].append(((i, j), c))
            else:
                free.append(((i, j), c, max(g.get('n', 0), 1)))
    labs = np.array([kit.srgb_to_lab(c) for _, c, _ in free]).reshape(-1, 3)
    hexof = lambda g: kit.rgbhex(np.average([free[k][1] for k in g], axis=0, weights=[free[k][2] for k in g]))
    worst = lambda g: float(kit.de2000(kit.srgb_to_lab(kit.hexrgb(hexof(g))), labs[g]).max())
    groups, cost = [[k] for k in range(len(free))], {}
    while True:   # ponytail: O(n^3) agglomeration with a pair cache; n is ~100 stops
        best = None
        for a in range(len(groups)):
            for b in range(a + 1, len(groups)):
                ck = (tuple(groups[a]), tuple(groups[b]))
                if ck not in cost:
                    cost[ck] = worst(groups[a] + groups[b])
                if cost[ck] <= MERGE_DE and (best is None or cost[ck] < best[0]):
                    best = (cost[ck], a, b)
        if best is None:
            break
        groups[best[1]] += groups[best[2]]; groups.pop(best[2])
    for g in groups:
        hx = hexof(g)
        t = tones.setdefault(hx, dict(name=None, hex=hx, palette=False, members=[]))
        for k in g:
            out[free[k][0]] = (hx, None); t['members'].append(free[k][:2])
    tl = sorted(tones.values(), key=lambda t: (not t['palette'], family(kit.srgb_to_lab(kit.hexrgb(t['hex']))),
                                               kit.srgb_to_lab(kit.hexrgb(t['hex']))[0]))
    count = {}
    for t in tl:
        lab = kit.srgb_to_lab(kit.hexrgb(t['hex']))
        t['max_de_to_measured'] = round(max(float(kit.de2000(lab, kit.srgb_to_lab(c))) for _, c in t['members']), 2)
        if not t['palette']:
            fam = family(lab); count[fam] = count.get(fam, 0) + 1
            t['name'] = 'Bird %s %s %d' % (oid, fam, count[fam])
    return out, tl


def widen(fills, V, F, img, erode):
    """fit_facets searches 3-stop directions only +-30 deg around the 2-stop one; search every direction and keep
    the 3-stop gradient where it fits better (same acceptance rule as fit_facets)."""
    for i, g in enumerate(fills):
        if g['kind'] != 'linear' or g.get('borrowed_from') is not None or g['n'] < 30:
            continue
        px, py, rgb = interior_samples(V[F[i]], img, erode=erode)
        g3 = fit_gradient_k(px, py, rgb, V[F[i]], 3, th0=None)
        if (g3['rms'] < g['rms'] - 1e-6) if len(g['stops']) == 3 else                 (g3['rms'] < THREE_GAIN * g['rms2'] and g['rms2'] - g3['rms'] > THREE_ABS):
            lo, hi = rgb.min(0), rgb.max(0)
            fills[i] = dict(g, p1=g3['p1'], p2=g3['p2'], rms=float(g3['rms']), rms3=float(g3['rms']),
                            stops=[(o, np.clip(c, lo, hi)) for o, c in zip(g3['offsets'], g3['colors'])])


def solidify(fills, colors):
    """A gradient whose stops all resolved to one hex is written as that solid colour."""
    for i, g in enumerate(fills):
        if g['kind'] != 'solid' and len({colors[(i, j)][0] for j in range(len(g['stops']))}) == 1:
            hx, pn = colors[(i, 0)]
            for j in range(1, len(g['stops'])):
                del colors[(i, j)]
            fills[i] = dict(g, kind='solid', stops=[(0.0, np.mean([c for _, c in g['stops']], 0))], solidified=True)
            colors[(i, 0)] = (hx, pn)


def facet_de(V, F, img, de_map):
    out = []
    for f in F:
        px, py, _ = interior_samples(V[f], img)
        out.append(round(float(de_map[(py - 0.5).astype(int), (px - 0.5).astype(int)].mean()), 2) if len(px) else None)
    return out


def build(oid, erode=1, robust=False):
    cfg = CFG[oid]
    img = kit.load(oid)
    bg = bg_of(img)
    H, W = img.shape[:2]
    V, F, names = load_mesh(WORKD / ('src%s.pkl' % oid))
    fills = fit_facets(V, F, img, allow_three=not cfg['solid'], force_solid=cfg['solid'], erode=erode, robust=robust,
                       min_samples=MIN_SAMPLES)
    if not cfg['solid']:
        widen(fills, V, F, img, erode)
    colors, tones = resolve(fills, oid)
    for (i, j), (hx, _) in colors.items():   # colour rule holds: no written colour strays > 2 dE from its measurement
        assert float(kit.de2000(kit.srgb_to_lab(kit.hexrgb(hx)), kit.srgb_to_lab(fills[i]['stops'][j][1]))) <= max(SNAP_DE, MERGE_DE) + 0.01
    solidify(fills, colors)
    polys = extend_facets(V, F, SEAM)
    title = 'Alliance AI Partners faceted swallow, as drawn in original %s' % oid
    svg = kit.COMP / ('bird-%s.svg' % oid)
    txt = svg_text(polys, fills, colors, title=title, w=W, h=H)
    assert not re.search(r'transform|filter|mask|clip|opacity|<text|<rect|<image', txt)
    assert txt.count('<path ') == txt.count('<path id="facet-') == len(F)
    svg.write_text(txt, encoding='utf-8', newline='\n')
    rend = kit.over(kit.render_svg(svg, 1.0), bg)
    x0, y0, x1, y1 = TARGETS[oid]['region']
    region = np.zeros((H, W), bool); region[y0:y1, x0:x1] = True
    m, de_map, mo, mr = metrics(img.astype(float), rend, bg, region=region)
    ys, xs = np.nonzero(mo)
    box = (int(xs.min()) - 8, int(ys.min()) - 8, int(xs.max()) + 9, int(ys.max()) + 9)
    zoom_sheet(img, rend, de_map, box, kit.VERIFY / ('bird_%s_diff.png' % oid),
               'bird %s in source space (components/bird-%s.svg): IoU %.4f  dE2000 mean %.2f p95 %.2f'
               % (oid, oid, m['iou'], m['de_mean'], m['de_p95']))
    pl_path = kit.FIT / 'bird-placements.json'
    pl = json.load(open(pl_path))
    before = pl[oid]['recolored']['metrics']
    per = facet_de(V, F, img, de_map)
    used = sorted({v for f in F for v in f})
    doc = dict(
        component='faceted origami swallow, recreated 1:1 from original %s' % oid,
        source=oid, source_file=kit.ORIGINALS[oid][0], viewBox=[0, 0, W, H], background=bg,
        files=dict(svg='components/bird-%s.svg' % oid, diff='verify/bird_%s_diff.png' % oid,
                   mesh='work/bird-/src%s.pkl' % oid, pipeline='work/bird-/b_source.py'),
        space="original %s pixels, identity placement (no transform); bird only, no wordmark or background" % oid,
        topology='master facets of components/bird.json (same ids, names and vertex sharing): %d facets on %d shared vertices'
                 % (len(F), len(used)),
        geometry='start: similarity placement of the master (fit/bird-placements.json "%s".matrix); every vertex re-placed by '
                 'coordinate descent on the squared RGB error of an exact centre-sampled rasterisation against %s '
                 '(4x4 supersampling: steps 4, 2, 1, 0.5, 0.25 px, then 1, 0.5, 0.25 px again; 8x8: steps 0.25, 0.125 px), '
                 'per-facet affine colour fields refitted after every step size' % (oid, oid),
        fill_style=cfg['style'],
        colour_rule='fidelity first: measured colours kept; snapped to a kit.PALETTE colour only when within dE2000 %.1f; '
                    'near-identical tones merged when every member is within dE2000 %.1f of the merged hex' % (SNAP_DE, MERGE_DE),
        paint_order='facet-01 first; each facet runs %.1f px under every later facet it shares an edge with (seam cover); '
                    'no paint outside the silhouette; white gaps and the white A are unpainted' % SEAM,
        fit_options=dict(erode=erode, robust=robust, min_samples=MIN_SAMPLES),
        metrics=dict(before=dict(before, note='master geometry placed by the similarity fit, recoloured from %s' % oid),
                     after=m, verify='VectorCraft render of components/bird-%s.svg over %s vs the original; silhouette '
                                     'IoU of kit.bg_mask(thresh 18) inside region %s; dE2000 inside the original\'s mask'
                                     % (oid, bg, list(TARGETS[oid]['region']))),
        tones=[dict(name=t['name'], hex=t['hex'], palette=t['palette'],
                    facets=sorted({'facet-%02d' % (k[0] + 1) for k, _ in t['members'] if k in colors}),
                    max_de_to_measured=t['max_de_to_measured']) for t in tones],
        facets=[])
    doc['tones'] = [t for t in doc['tones'] if t['facets']]
    for i, (f, g, P) in enumerate(zip(F, fills, polys)):
        doc['facets'].append(dict(
            id='facet-%02d' % (i + 1), name=names[i],
            vertices=[[round(float(x), 2), round(float(y), 2)] for x, y in V[f]],
            path_vertices=[[round(float(x), 2), round(float(y), 2)] for x, y in P],
            fill=fill_doc(i, g, colors),
            fit=dict(rms_rgb=round(g['rms'], 2), rms_rgb_solid=round(g['rms_solid'], 2), samples=g['n'],
                     de2000_mean_interior=per[i],
                     **({'borrowed_from': 'facet-%02d' % (g['borrowed_from'] + 1)} if g.get('borrowed_from') is not None else {}))))
    (kit.FIT / ('bird-%s.json' % oid)).write_text(json.dumps(doc, indent=1), encoding='utf-8', newline='\n')
    ss = pl.setdefault('source_space', dict(
        note='components/bird-05.svg and components/bird-08.svg are now authored in their original\'s own pixel space '
             '(viewBox 0 0 W H, identity placement, geometry re-optimised against that original). The "05" / "08" '
             'matrices above are only the similarity placement the re-optimisation started from; their "recolored" '
             'entries describe the superseded master-space recolours.'))
    ss[oid] = dict(file='components/bird-%s.svg' % oid, fit='fit/bird-%s.json' % oid, viewBox=[0, 0, W, H],
                   transform=None, metrics=m)
    pl_path.write_text(json.dumps(pl, indent=1), encoding='utf-8', newline='\n')
    log(oid, json.dumps(m), 'tones', len(doc['tones']), 'solid', sum(g['kind'] == 'solid' for g in fills),
        'snapped', sum(t['palette'] for t in doc['tones']))
    for i, g in enumerate(fills):
        log('%2d %-16s n=%5d %-6s stops=%d rms %.1f (solid %.1f) dE %s %s' % (
            i + 1, names[i], g['n'], g['kind'], len(g['stops']), g['rms'], g['rms_solid'], per[i],
            'borrowed from facet-%02d' % (g['borrowed_from'] + 1) if g.get('borrowed_from') is not None else ''))
    return m


if __name__ == '__main__':
    {'opt': optimise, 'build': build}[sys.argv[1]](sys.argv[2])
