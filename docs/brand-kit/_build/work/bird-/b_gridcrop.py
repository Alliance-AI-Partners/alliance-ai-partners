import sys, numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'); import kit
def gridcrop(img, x0, y0, x1, y1, z, out, step=10):
    im = Image.fromarray(img) if not isinstance(img, Image.Image) else img
    c = im.crop((x0, y0, x1, y1)).resize(((x1-x0)*z, (y1-y0)*z), Image.NEAREST).convert('RGB')
    d = ImageDraw.Draw(c)
    for x in range((x0//step+1)*step, x1, step):
        col = (255,0,0) if x % 50 == 0 else (255,160,160)
        d.line([((x-x0)*z, 0), ((x-x0)*z, c.height)], fill=col, width=1)
        if x % 50 == 0: d.text(((x-x0)*z+2, 2), str(x), fill=(255,0,0))
    for y in range((y0//step+1)*step, y1, step):
        col = (255,0,0) if y % 50 == 0 else (255,160,160)
        d.line([(0, (y-y0)*z), (c.width, (y-y0)*z)], fill=col, width=1)
        if y % 50 == 0: d.text((2, (y-y0)*z+2), str(y), fill=(255,0,0))
    c.save(out)
if __name__ == '__main__':
    src = sys.argv[1]; x0, y0, x1, y1, z = map(int, sys.argv[2:7]); out = sys.argv[7]
    if src == 'orig': img = kit.load('15')
    elif src == 'edge':
        e = np.load('edge_s.npy'); img = np.clip(e/4*255, 0, 255).astype(np.uint8)
    elif src.endswith('.png'): img = np.asarray(Image.open(src).convert('RGB'))
    gridcrop(img, x0, y0, x1, y1, z, out)
