"""Scratch: check VectorCraft support for dasharray, stroke widths, circles (board agent)."""
import sys, time
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
import numpy as np
from PIL import Image
body = '''<rect id="bg" x="0" y="0" width="200" height="100" fill="#F4F7FB"/>
<path id="d1" d="M10 20.5 H190" stroke="#844037" stroke-width="1.6" stroke-dasharray="6.8 2.5" fill="none"/>
<path id="l1" d="M10 40 H190" stroke="#121B2A" stroke-width="1.8" fill="none"/>
<circle id="c1" cx="50" cy="70" r="20" fill="#1B56FF"/>
<circle id="c2" cx="120" cy="70" r="20" fill="#FFFFFF" stroke="#161936" stroke-width="1.5"/>
<path id="t1" d="M150 60 L160 80 L140 80 Z" fill="#A64546"/>'''
svg = kit.svg_doc(200, 100, body)
t = time.time()
r = kit.render_svg(svg, 4)
print('render 4x', r.shape, round(time.time() - t, 2), 's')
Image.fromarray((kit.over(r, '#F4F7FB')).astype(np.uint8)).save(kit.WORK / 'board' / 'vctest.png')
r1 = kit.render_svg(svg, 1)
rgb = kit.over(r1, '#F4F7FB')
print('row 20/21 at x=10..30:', rgb[19:23, 10:30].mean(-1).round(0))
print('line rows 38..42 col 100:', rgb[37:43, 100].round(0))
