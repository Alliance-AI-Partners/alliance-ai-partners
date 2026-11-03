import sys; sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'); import kit
import numpy as np
from PIL import Image
from b_build import load_mesh
from b_export import extend_facets, path_d
from b_fit import cover
from b_poke import poke_report, sub_inside
V, F, names = load_mesh(sys.argv[1])
ext = extend_facets(V, F, float(sys.argv[2]) if len(sys.argv) > 2 else 1.0)
exact = [V[f] for f in F]
print('pokes:', [(names[i], round(mx, 3), n, at) for i, mx, n, at in poke_report(exact, ext)])
lost = 0
for P0, P1 in zip(exact, ext):
    lost += int((sub_inside(P0, 258, 217, 510, 391) & ~sub_inside(P1, 258, 217, 510, 391)).sum())
print('subpixels lost (exact not inside extended):', lost)
S = np.zeros((1024, 1024))
for P in exact: S[217:608, 258:768] += cover(P, 258, 217, 510, 391, 4)
inner = kit.erode(S >= 0.999, 2)
for nm, polys in (('exact', exact), ('extended', ext)):
    for sc in (1.0, 0.5, 0.25):
        body = '\n'.join('<path id="f%d" d="%s" fill="#000000"/>' % (i, path_d(P)) for i, P in enumerate(polys))
        a = kit.render_svg(kit.svg_doc(1024, 1024, body), sc)[..., 3]
        m = inner if sc == 1.0 else kit.erode(np.asarray(Image.fromarray(inner.astype(np.uint8) * 255).resize((int(1024 * sc),) * 2)) > 254, 1)
        leak = 1 - a[m]
        print('%-8s scale %.2f: interior pixels alpha<0.97: %d (max leak %.3f)' % (nm, sc, int((leak > 0.03).sum()), leak.max()))
