"""Fit the master bird onto originals 05 and 08 (similarity transform by mask IoU), measure IoU / dE there,
re-colour from the target's pixels when it is coloured differently, write fit/bird-placements.json,
components/bird-05.svg / bird-08.svg and verify/bird_05_diff.png / bird_08_diff.png.
Usage: python b_place_build.py mesh.pkl [--dry]"""
import sys, json
import numpy as np
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
from b_build import load_mesh, resolve_colors, svg_text, metrics, zoom_sheet, tone_doc, fill_doc, SEAM, WORKD
from b_colors import fit_facets, interior_samples
from b_export import extend_facets, boundary_loops
from b_place import fit_placement

# bird region in each target (keeps the wordmark out of the masks)
TARGETS = {'05': dict(region=(440, 100, 940, 480), recolor=dict(force_solid=True, allow_three=False, erode=2, robust=True, min_samples=40),
                      style='flat (one solid colour per facet, as drawn in 05)'),
           '08': dict(region=(100, 150, 585, 520), recolor=dict(force_solid=False, allow_three=True, erode=2, robust=True),
                      style='shaded (linear gradients fitted per facet, as drawn in 08)')}
RECOLOR_DE = 4.0   # master colours count as "noticeably different" above this mean dE2000


def bg_of(img):
    return kit.rgbhex(np.median(np.concatenate([img[:20].reshape(-1, 3), img[-20:].reshape(-1, 3)]), 0))


def render_in(img_shape, polys, fills, colors, A, t, bg):
    h, w = img_shape[:2]
    mat = (A[0, 0], A[1, 0], A[0, 1], A[1, 1], t[0], t[1])
    txt = svg_text(polys, fills, colors, w=w, h=h, transform=mat)
    return kit.over(kit.render_svg(txt, 1.0), bg), mat


def main(mesh_pkl, dry=False):
    V, F, names = load_mesh(mesh_pkl)
    master = kit.load('15')
    fills0 = fit_facets(V, F, master)
    colors0, tones0, snaps0 = resolve_colors(fills0)
    polys = extend_facets(V, F, SEAM)
    loops = [V[L] for L in boundary_loops(V, F)]
    out = {}
    pre = 'dry_' if dry else ''
    comp = WORKD if dry else kit.COMP
    ver = WORKD if dry else kit.VERIFY
    fitd = WORKD if dry else kit.FIT
    for oid, cfg in TARGETS.items():
        img = kit.load(oid)
        bg = bg_of(img)
        x0, y0, x1, y1 = cfg['region']
        region = np.zeros(img.shape[:2], bool); region[y0:y1, x0:x1] = True
        tmask = kit.bg_mask(img, bg, 18) & region
        p, iou_fit, (A, t), mc = fit_placement(loops, tmask, cfg['region'])
        rend, mat = render_in(img.shape, polys, fills0, colors0, A, t, bg)
        m0, de0, mo, mr = metrics(img.astype(float), rend, bg, region=region)
        rec = dict(source_file=kit.ORIGINALS[oid][0], background=bg,
                   matrix=[round(float(v), 6) for v in mat],
                   scale=round(float(p[0]), 6), rotation_deg=round(float(np.degrees(p[1])), 4),
                   translate=[round(float(mat[4]), 3), round(float(mat[5]), 3)],
                   note='SVG matrix(a b c d e f) maps the 1024 master space (components/bird.svg) onto this original\'s pixels',
                   iou_fit_coverage=round(float(iou_fit), 4), master_colors=m0)
        print(oid, 'scale %.4f rot %.3f deg' % (p[0], np.degrees(p[1])), 'master colours:', m0)
        bbox = np.nonzero(mo)
        box = (int(bbox[1].min()) - 8, int(bbox[0].min()) - 8, int(bbox[1].max()) + 9, int(bbox[0].max()) + 9)
        best = (rend, de0, m0, 'master colours (components/bird.svg)')
        if m0['de_mean'] > RECOLOR_DE:
            xf = lambda px, py, A=A, t=t: (A[0, 0] * px + A[0, 1] * py + t[0], A[1, 0] * px + A[1, 1] * py + t[1])
            fills = fit_facets(V, F, img, xform=xf, valid=kit.erode(tmask, 1), **cfg['recolor'])
            colors, tones, snaps = resolve_colors(fills)
            svg = comp / ('%sbird-%s.svg' % (pre, oid))
            svg.write_text(svg_text(polys, fills, colors, title='Alliance AI Partners faceted swallow, colours of original %s' % oid),
                           encoding='utf-8', newline='\n')
            rend2, _ = render_in(img.shape, polys, fills, colors, A, t, bg)
            m2, de2, _, _ = metrics(img.astype(float), rend2, bg, region=region)
            t_out, s_out = tone_doc(tones, snaps)
            rec['recolored'] = dict(file='components/bird-%s.svg' % oid, style=cfg['style'], metrics=m2,
                                    fills={'facet-%02d' % (i + 1): fill_doc(i, g, colors) for i, g in enumerate(fills)},
                                    supporting_tones=t_out, palette_snaps=s_out)
            print(oid, 'recoloured:', m2, 'tones', len(tones), 'solid', sum(g['kind'] == 'solid' for g in fills))
            best = (rend2, de2, m2, 'recoloured (components/bird-%s.svg)' % oid)
        else:
            rec['recolored'] = None
        rend_b, de_b, m_b, lab = best
        zoom_sheet(img, rend_b, de_b, box, ver / ('%sbird_%s_diff.png' % (pre, oid)),
                   'bird on %s, %s: IoU %.4f dE2000 mean %.2f p95 %.2f' % (oid, lab, m_b['iou'], m_b['de_mean'], m_b['de_p95']))
        if rec['recolored']:
            zoom_sheet(img, rend, de0, box, ver / ('%sbird_%s_master_colors_diff.png' % (pre, oid)),
                       'bird on %s, master colours: IoU %.4f dE2000 mean %.2f p95 %.2f' % (oid, m0['iou'], m0['de_mean'], m0['de_p95']))
        out[oid] = rec
    (fitd / ('%sbird-placements.json' % pre)).write_text(json.dumps(out, indent=1), encoding='utf-8', newline='\n')
    return out


if __name__ == '__main__':
    main(sys.argv[1], dry='--dry' in sys.argv)
