"""Scratch: 4x zooms of the pattern tiles."""
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import os
import kit
C = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\components'
imgs = []
for f, crop in (('pattern-ap-monogram-tile.svg', (0, 0, 120, 80)), ('pattern-halftone-tile.svg', (180, 180, 240, 240)),
                ('pattern-datamesh-tile.svg', (0, 0, 80, 80)), ('pattern-ribbon-lines-tile.svg', (0, 0, 80, 80)),
                ('pattern-facets-tile.svg', (0, 0, 120, 120))):
    r = kit.over(kit.render_svg(os.path.join(C, f), scale=4), '#FFFFFF')
    x0, y0, x1, y1 = [v * 4 for v in crop]
    imgs.append(r[y0:y1, x0:x1])
kit.contact(imgs, ['monogram x4', 'halftone corner x4', 'datamesh x4', 'ribbon lines x4', 'facets x4'], 'tiles_zoom.png', cols=3, width=420)
