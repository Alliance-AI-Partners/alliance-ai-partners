"""Write components/ap-mono.svg/.json (one compound #000000 shape) and verify/ap-mono_preview.png;
IoU against original 12's mark after a similarity fit (a different drawing of the same design)."""
import json
import sys
import numpy as np
from PIL import Image

sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
from build_hero import W, lines_dict
from make_dark import fit_similarity, wrap_svg
from make_mono import H12, GAP12
from finalize import bbox_of

COMP, VER = kit.COMP, kit.VERIFY

if __name__ == '__main__':
    src = sys.argv[1] if len(sys.argv) > 1 else 'mono_v5.json'
    hero_src = sys.argv[2] if len(sys.argv) > 2 else 'hero_v7.json'
    m = json.load(open(W / src))
    d = m['d']
    ln = lines_dict()
    svg = kit.svg_doc(1024, 1024, f'<path id="ap-mono" d="{d}" fill="#000000" fill-rule="evenodd"/>')
    (COMP / 'ap-mono.svg').write_text(svg, encoding='utf-8')
    # silhouette agreement with the hero (outside the cuts the mono is the hero silhouette)
    hero = json.load(open(W / hero_src))
    a_h = kit.raster(hero['silhouette'], 1024, 1024) > 0.5
    a_m = kit.raster(d, 1024, 1024) > 0.5
    cut_area = float((a_h & ~a_m).sum())
    # similarity fit onto 12's flat mark (alpha by 2-colour unmixing, gaps12.py)
    alpha12 = np.load(W / 'alpha12.npy')
    mask12 = alpha12 > 0.5
    box = (180, 280, 860, 700)
    m12 = np.zeros_like(mask12); m12[box[1]:box[3], box[0]:box[2]] = mask12[box[1]:box[3], box[0]:box[2]]
    alpha_m = kit.raster(d, 1024, 1024)
    v, (s, tx, ty) = fit_similarity(alpha_m, m12, box, s_range=(0.86, 1.01))
    placed = kit.raster(kit.transform_d(d, s, tx, ty), 1024, 1024) > 0.5
    iou12 = kit.iou(placed, m12)
    k = (ln['base'] - ln['top']) / H12
    info = {'component': 'ap-mono', 'viewBox': [0, 0, 1024, 1024], 'fill': '#000000', 'fill_rule': 'evenodd',
            'construction': 'hero silhouette (one shared outline of all faces) minus two tapered interlace cuts (VectorCraft Pathfinder Minus Front)',
            'bbox': bbox_of(d), 'baseline_y': ln['base'], 'apex_top_y': ln['top'], 'mark_height': round(ln['base'] - ln['top'], 2),
            'subpaths': len(kit.parse_d(d)), 'anchors': sum(len(q['segs']) for q in kit.parse_d(d)),
            'gap': {'width_px': round(GAP12['a']['w'] * k, 3), 'width_rel_mark_height': round(GAP12['a']['w'] / H12, 5),
                    'measured_in_12': {'width_px': GAP12['a']['w'], 'mark_height_px': H12,
                                       'profile': 'constant from the open end for 40 % (left-leg cut) / 60 % (right-leg cut) of its length, then a straight taper to a point'},
                    'cuts': {'a_left_leg': dict(m['info']['a'], along='ribbon top edge over the A left leg, open at the leg outer edge'),
                             'b_right_leg_p_stem': dict(m['info']['b'], along='ribbon outer edge over the A right leg and the P stem/bowl, open into the lower counter, closing at the P counter')}},
            'cut_area_px2': round(cut_area, 1),
            'vs_12': {'similarity': {'scale': round(float(s), 5), 'tx': round(float(tx), 3), 'ty': round(float(ty), 3),
                                     'note': 'p12 = scale * p_master + (tx, ty)'},
                      'iou': round(float(iou12), 4),
                      'note': '12 is a separate flat drawing of the design (different proportions and P), so this is reported, not forced'}}
    json.dump(info, open(COMP / 'ap-mono.json', 'w'), indent=1)
    print({k_: v_ for k_, v_ in info.items() if k_ not in ('gap',)}, info['gap']['width_px'])
    # preview: originals 06 / 12 next to the mono black on white and white on Deep Navy
    rb = kit.render_svg(COMP / 'ap-mono.svg')
    black_on_white = kit.over(np.concatenate([np.zeros_like(rb[..., :3]), rb[..., 3:4]], -1), '#FFFFFF')
    white_on_navy = kit.over(np.concatenate([np.ones_like(rb[..., :3]), rb[..., 3:4]], -1), '#121B2A')
    crop = lambda im: np.asarray(im)[260:760, 110:910]
    o06, o12 = kit.load('06'), kit.load('12')
    # 12 placed in its own frame: crop around its mark
    c12 = o12[240:740, 115:915]
    over12 = o12.astype(float).copy()
    edge = placed ^ kit.erode(placed, 1)
    over12[edge] = [255, 60, 60]
    kit.contact([crop(o06), crop(black_on_white), c12, crop(white_on_navy), over12[240:740, 115:915]],
                ['original 06', 'ap-mono #000000 on white', 'original 12', 'ap-mono #FFFFFF on Deep Navy #121B2A',
                 'ap-mono outline (red) on 12 after similarity fit, IoU %.3f' % iou12],
                VER / 'ap-mono_preview.png', cols=2, width=640)
    print('wrote', COMP / 'ap-mono.svg', COMP / 'ap-mono.json', VER / 'ap-mono_preview.png')
