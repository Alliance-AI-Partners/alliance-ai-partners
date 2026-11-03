"""Scratch: VectorCraft anti-aliasing check at 1x vs 4x-downsampled (board agent)."""
import sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
import numpy as np
body = '''<rect id="bg" x="0" y="0" width="100" height="60" fill="#FFFFFF"/>
<path id="l1" d="M10 10.3 H90" stroke="#000000" stroke-width="1.8" fill="none"/>
<path id="l2" d="M10 20.5 H90" stroke="#000000" stroke-width="1.0" fill="none"/>
<path id="l3" d="M10 30.25 H90" stroke="#000000" stroke-width="1.6" fill="none"/>
<rect id="r1" x="10" y="40.3" width="80" height="1.8" fill="#000000"/>
<path id="l4" d="M10 50 H90" stroke="#000000" stroke-width="0.6" fill="none"/>'''
svg = kit.svg_doc(100, 60, body)
r1 = kit.over(kit.render_svg(svg, 1), '#FFFFFF').mean(-1)
r4 = kit.over(kit.render_svg(svg, 4), '#FFFFFF').mean(-1)
r4d = r4.reshape(60, 4, 100, 4).mean((1, 3))
for name, y0, y1 in (('l1 10.3 w1.8 [9.4,11.2]', 8, 13), ('l2 20.5 w1 [20,21]', 18, 23), ('l3 30.25 w1.6 [29.45,31.05]', 28, 33), ('r1 rect [40.3,42.1]', 38, 44), ('l4 50 w0.6 [49.7,50.3]', 48, 52)):
    print(name)
    print('   1x  :', (255 - r1[y0:y1, 50]).round(0))
    print('   4x/4:', (255 - r4d[y0:y1, 50]).round(0))
