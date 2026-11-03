"""Mesh pickle -> components/bird.svg, bird-mono.svg, bird.json, verify/bird_diff.png (master = original 15).
Usage: python b_build.py mesh.pkl [--dry]   (--dry writes dry_* files into work/bird-/ only)"""
import sys, json, pickle
import numpy as np
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
from b_colors import fit_facets, snap, family, cluster_tones, interior_samples
from b_export import extend_facets, boundary_loops, path_d

WORKD = kit.WORK / 'bird-'
SEAM = 1.0   # px (master space) that a lower facet runs under every facet painted above it
TITLE = 'Alliance AI Partners faceted swallow'


def load_mesh(p):
    d = pickle.load(open(p, 'rb'))
    return np.asarray(d[0], float), [list(f) for f in d[1]], list(d[2])


def resolve_colors(fills, tone_thresh=3.0):
    """Snap every stop within dE2000 4 of a core palette colour to it; merge the rest into
    supporting tones (agglomerative, dE2000 <= tone_thresh). Returns ({(facet, stop): (hex, palette)}, tones, snaps)."""
    keys, cols = [], []
    for i, g in enumerate(fills):
        for j, (off, c) in enumerate(g['stops']):
            keys.append((i, j)); cols.append(np.clip(c, 0, 255))
    out, snaps, free = {}, [], []
    for k, (key, c) in enumerate(zip(keys, cols)):
        hx, pname, de = snap(c)
        if pname:
            out[key] = (hx, pname)
            snaps.append(dict(facet=key[0], stop=key[1], measured=kit.rgbhex(c), palette=pname, hex=hx, de=round(de, 2)))
        else:
            free.append(k)
    labels, centers = cluster_tones([cols[k] for k in free], tone_thresh) if free else ([], [])
    tones = [dict(hex=kit.rgbhex(c), lab=kit.srgb_to_lab(c), members=[]) for c in centers]
    for k, t in zip(free, labels):
        tones[t]['members'].append(keys[k])
        out[keys[k]] = (tones[t]['hex'], None)
    tones.sort(key=lambda d: (family(d['lab']), d['lab'][0]))
    count = {}
    for d in tones:
        fam = family(d['lab']); count[fam] = count.get(fam, 0) + 1
        d['name'] = 'Bird %s %d' % (fam, count[fam])
    return out, tones, snaps


def clean_stops(stops):
    """Drop end stops that repeat their neighbour's colour (SVG pads with the end colour anyway)."""
    s = list(stops)
    while len(s) > 2 and s[-1][1] == s[-2][1]:
        s.pop()
    while len(s) > 2 and s[0][1] == s[1][1]:
        s.pop(0)
    return s


def simplify_loop(P, tol=0.25):
    """Remove loop vertices lying within `tol` px of the chord of their neighbours (fewest anchors)."""
    P = [np.asarray(p, float) for p in P]
    changed = True
    while changed and len(P) > 3:
        changed = False
        best = None
        for k in range(len(P)):
            a, b, c = P[k - 1], P[k], P[(k + 1) % len(P)]
            ac = c - a
            d = abs(ac[0] * (b[1] - a[1]) - ac[1] * (b[0] - a[0])) / max(np.hypot(*ac), 1e-9)
            if d < tol and (best is None or d < best[0]):
                best = (d, k)
        if best is not None:
            P.pop(best[1]); changed = True
    return np.array(P)


def svg_text(polys, fills, colors, title=TITLE, w=1024, h=1024, transform=None):
    defs, body = [], []
    for i, (P, g) in enumerate(zip(polys, fills)):
        fid = 'facet-%02d' % (i + 1)
        if g['kind'] == 'solid':
            fill = colors[(i, 0)][0]
        else:
            gid = 'grad-%02d' % (i + 1)
            stops = clean_stops([(off, colors[(i, j)][0]) for j, (off, c) in enumerate(g['stops'])])
            defs.append(kit.lin_grad(gid, g['p1'][0], g['p1'][1], g['p2'][0], g['p2'][1], stops))
            fill = 'url(#%s)' % gid
        body.append('<path id="%s" d="%s" fill="%s"/>' % (fid, path_d(P), fill))
    tr = ' transform="matrix(%s)"' % ' '.join('%.6f' % v for v in transform) if transform is not None else ''
    body = '<title>%s</title>\n<g id="bird"%s>\n%s\n</g>' % (title, tr, '\n'.join(body))
    return kit.svg_doc(w, h, body, '\n'.join(defs))


def mono_text(V, F, color='#000000', w=1024, h=1024, transform=None):
    loops = [simplify_loop(V[L]) for L in boundary_loops(V, F)]
    d = ' '.join(path_d(L) for L in loops)
    tr = ' transform="matrix(%s)"' % ' '.join('%.6f' % v for v in transform) if transform is not None else ''
    body = ('<title>Alliance AI Partners swallow, one colour</title>\n'
            '<path id="bird-mono" d="%s" fill="%s" fill-rule="evenodd"%s/>' % (d, color, tr))
    return kit.svg_doc(w, h, body), loops


def metrics(orig, rend, bg='#FFFFFF', thresh=18, region=None):
    mo = kit.bg_mask(orig, bg, thresh)
    mr = kit.bg_mask(rend, bg, thresh)
    if region is not None:
        mo &= region; mr &= region
    c = kit.compare(orig, rend, region=mo)
    ce = kit.compare(orig, rend, region=kit.erode(mo, 1))
    return dict(iou=round(kit.iou(mo, mr), 4), de_mean=c['de_mean'], de_p95=c['de_p95'],
                de_mean_eroded1=ce['de_mean'], de_p95_eroded1=ce['de_p95']), c['de_map'], mo, mr


def zoom_sheet(orig, rend, de_map, box, out, label, z=2):
    x0, y0, x1, y1 = box
    up = lambda a: np.repeat(np.repeat(np.asarray(a)[y0:y1, x0:x1], z, 0), z, 1)
    kit.diff_sheet(up(orig), up(rend), out, up(de_map), label)


def fill_doc(i, g, colors):
    if g['kind'] == 'solid':
        hx, pn = colors[(i, 0)]
        return dict(type='solid', color=hx, measured=kit.rgbhex(g['stops'][0][1]), palette=pn)
    return dict(type='linearGradient', id='grad-%02d' % (i + 1), gradientUnits='userSpaceOnUse',
                x1=round(float(g['p1'][0]), 3), y1=round(float(g['p1'][1]), 3),
                x2=round(float(g['p2'][0]), 3), y2=round(float(g['p2'][1]), 3),
                stops=[dict(offset=round(float(off), 4), color=colors[(i, j)][0], measured=kit.rgbhex(c),
                            palette=colors[(i, j)][1]) for j, (off, c) in enumerate(g['stops'])],
                svg_stops=[[round(float(o), 4), hx] for o, hx in
                           clean_stops([(off, colors[(i, j)][0]) for j, (off, c) in enumerate(g['stops'])])])


def tone_doc(tones, snaps):
    t_out = [dict(name=t['name'], hex=t['hex'],
                  used_in=sorted({'facet-%02d' % (i + 1) for i, j in t['members']}),
                  stops=['facet-%02d/%d' % (i + 1, j) for i, j in t['members']]) for t in tones]
    s_out = [dict(s, facet='facet-%02d' % (s['facet'] + 1)) for s in snaps]
    return t_out, s_out


def main(mesh_pkl, dry=False):
    V, F, names = load_mesh(mesh_pkl)
    img = kit.load('15')
    fills = fit_facets(V, F, img)
    colors, tones, snaps = resolve_colors(fills)
    polys = extend_facets(V, F, SEAM)
    comp = WORKD if dry else kit.COMP
    ver = WORKD if dry else kit.VERIFY
    pre = 'dry_' if dry else ''
    svg = comp / (pre + 'bird.svg')
    svg.write_text(svg_text(polys, fills, colors), encoding='utf-8', newline='\n')
    mono = comp / (pre + 'bird-mono.svg')
    mtxt, loops = mono_text(V, F)
    mono.write_text(mtxt, encoding='utf-8', newline='\n')
    rend = kit.over(kit.render_svg(svg, 1.0), '#FFFFFF')
    m, de_map, mo, mr = metrics(img.astype(float), rend)
    rend_m = kit.over(kit.render_svg(mono, 1.0), '#FFFFFF')
    mm = kit.bg_mask(rend_m, '#FFFFFF', 18)
    m['mono_iou_vs_original'] = round(kit.iou(mo, mm), 4)
    m['mono_iou_vs_color_render'] = round(kit.iou(mr, mm), 4)
    # coverage-weighted silhouette IoU (alpha >= 0.5) of the colour render vs the original's 50 % coverage
    ys, xs = np.nonzero(mo)
    bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]
    box = (bbox[0] - 8, bbox[1] - 8, bbox[2] + 8, bbox[3] + 8)
    zoom_sheet(img, rend, de_map, box, ver / (pre + 'bird_diff.png'),
               'bird master (15) IoU %.4f  dE2000 mean %.2f p95 %.2f' % (m['iou'], m['de_mean'], m['de_p95']))
    per = []
    for i, f in enumerate(F):
        px, py, _ = interior_samples(V[f], img)
        per.append(round(float(de_map[(py - 0.5).astype(int), (px - 0.5).astype(int)].mean()), 2))
    used = sorted({v for f in F for v in f})
    vb = V[used]
    t_out, s_out = tone_doc(tones, snaps)
    doc = dict(
        component='faceted origami swallow (brand mascot / secondary mark)',
        source='15', source_file=kit.ORIGINALS['15'][0], viewBox=[0, 0, 1024, 1024],
        bbox=[round(float(vb[:, 0].min()), 2), round(float(vb[:, 1].min()), 2),
              round(float(vb[:, 0].max()), 2), round(float(vb[:, 1].max()), 2)],
        files=dict(color='components/bird.svg', mono='components/bird-mono.svg',
                   recolored_05='components/bird-05.svg', recolored_08='components/bird-08.svg',
                   placements='fit/bird-placements.json', diff='verify/bird_diff.png'),
        paint_order='facet-01 first; each facet runs %.1f px under every facet painted above it (seam cover); '
                    'vertices are shared, so the visible edges meet exactly' % SEAM,
        vertex_count=len(used), facet_count=len(F),
        mono=dict(path_id='bird-mono', fill='#000000', fill_rule='evenodd', subpaths=len(loops),
                  anchors=int(sum(len(L) for L in loops))),
        facets=[], palette_snaps=s_out, supporting_tones=t_out, metrics=m)
    for i, (f, g, P) in enumerate(zip(F, fills, polys)):
        doc['facets'].append(dict(
            id='facet-%02d' % (i + 1), name=names[i],
            vertices=[[round(float(x), 2), round(float(y), 2)] for x, y in V[f]],
            path_vertices=[[round(float(x), 2), round(float(y), 2)] for x, y in P],
            fill=fill_doc(i, g, colors),
            fit=dict(rms_rgb=round(g['rms'], 2), rms_rgb_solid=round(g['rms_solid'], 2), samples=g['n'],
                     de2000_mean_interior=per[i])))
    (comp / (pre + 'bird.json')).write_text(json.dumps(doc, indent=1), encoding='utf-8', newline='\n')
    print(json.dumps(m))
    print('tones', len(tones), 'snaps', len(snaps), 'facets', len(F), 'verts', len(used))
    for i, g in enumerate(fills):
        print('%2d %-16s n=%5d %-6s stops=%d rms %.1f (solid %.1f) dE %.2f' % (
            i + 1, names[i], g['n'], g['kind'], len(g['stops']), g['rms'], g['rms_solid'], per[i]))
    return dict(V=V, F=F, names=names, fills=fills, colors=colors, tones=tones, polys=polys, metrics=m)


if __name__ == '__main__':
    main(sys.argv[1], dry='--dry' in sys.argv)
