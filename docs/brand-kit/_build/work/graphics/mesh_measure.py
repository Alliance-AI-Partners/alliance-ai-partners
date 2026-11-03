"""Scratch: measure the data-mesh panel in original 02: panel bounds, background, bar column grid."""
import numpy as np
import kit

im = kit.load('02').astype(float)
lab = kit.srgb_to_lab(im)
L = lab[..., 0]

# panel bounds: rows/cols where the dark panel starts (L drops below 40)
for y in range(606, 620):
    print('row', y, ' '.join('%4.0f' % L[y, x] for x in range(1036, 1046)), ' | ', ' '.join('%4.0f' % L[y, x] for x in range(1312, 1322)))
for y in range(704, 718):
    print('row', y, ' '.join('%4.0f' % L[y, x] for x in range(1036, 1046)), ' | ', ' '.join('%4.0f' % L[y, x] for x in range(1312, 1322)))
