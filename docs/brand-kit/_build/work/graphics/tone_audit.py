"""Scratch: audit every colour used in my components: palette distance, and supporting-tone pairs closer than dE 3."""
import sys, re, glob, os
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import numpy as np
import kit
C = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\components'
use = {}
for f in sorted(glob.glob(C + r'\graphic-*.svg') + glob.glob(C + r'\pattern-*.svg')):
    for h in re.findall(r'(?:fill|stop-color|stroke)="(#[0-9A-Fa-f]{6})"', open(f, encoding='utf-8').read()):
        use.setdefault(h.upper(), set()).add(os.path.basename(f))
pal = set(kit.PALETTE.values())
sup = sorted([h for h in use if h not in pal], key=lambda h: kit.srgb_to_lab(kit.hexrgb(h))[0])
print('palette colours used:', sorted(h for h in use if h in pal))
print('supporting tones:', len(sup))
for h in sup:
    n, ph, de = kit.nearest_palette(h)
    print('  %s  nearest %-12s dE %5.2f  used in %s' % (h, n, de, ', '.join(sorted(use[h]))))
lab = {h: kit.srgb_to_lab(kit.hexrgb(h)) for h in sup}
close = [(a, b, float(kit.de2000(lab[a], lab[b]))) for i, a in enumerate(sup) for b in sup[i + 1:]]
close = [c for c in close if c[2] < 3]
print('pairs < 3:', [(a, b, round(d, 2)) for a, b, d in close])
