import sys; sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'); import kit
import numpy as np
for i in ['12','16','09','07','10','11','03']:
    a = kit.load(i).astype(float); H, W, _ = a.shape
    frame = np.zeros((H, W), bool); frame[:30] = frame[-30:] = True; frame[:, :30] = frame[:, -30:] = True
    bg = np.median(a[frame], 0)
    fg = kit.bg_mask(a, kit.rgbhex(bg), 18)
    core = kit.erode(fg, 3)
    lab = kit.srgb_to_lab(a)
    # split fg core: white-ish (L>85 & chroma<15) vs cyan
    chroma = np.hypot(lab[..., 1], lab[..., 2])
    wh = core & (chroma < 15) & (lab[..., 0] > 80)
    cy = core & (chroma >= 25)
    ys, xs = np.nonzero(fg)
    print(i, 'bg', kit.rgbhex(bg), kit.nearest_palette(kit.rgbhex(bg)), 'bg std', a[frame].std(0).round(2))
    if cy.any():
        c = np.median(a[cy], 0); print('   cyan', kit.rgbhex(c), kit.nearest_palette(kit.rgbhex(c)), 'n', cy.sum(), 'std', a[cy].std(0).round(1))
    if wh.any():
        c = np.median(a[wh], 0); print('   white', kit.rgbhex(c), kit.nearest_palette(kit.rgbhex(c)), 'n', wh.sum())
    print('   fg bbox', xs.min(), ys.min(), xs.max(), ys.max())
