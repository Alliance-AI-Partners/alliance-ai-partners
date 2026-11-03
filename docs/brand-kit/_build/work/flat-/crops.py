import sys, os
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
from PIL import Image

W = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\flat-'


def crop(i, box, z, name, src=None):
    im = (Image.open(kit.orig(i)) if src is None else Image.open(src)).convert('RGB').crop(box)
    im = im.resize((im.width * z, im.height * z), Image.NEAREST)
    im.save(os.path.join(W, name))


if __name__ == '__main__':
    i, x0, y0, x1, y1, z, name = sys.argv[1:8]
    src = sys.argv[8] if len(sys.argv) > 8 else None
    crop(i, (int(x0), int(y0), int(x1), int(y1)), int(z), name, src)
