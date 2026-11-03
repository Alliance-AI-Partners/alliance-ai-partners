"""Scratch: draw slot bboxes over the original (board agent)."""
import sys, json
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit
from PIL import Image, ImageDraw
S = json.load(open(kit.WORK / 'board' / 'slots_raw.json'))
im = Image.fromarray(kit.load('02')).resize((1376 * 2, 768 * 2), Image.LANCZOS)
d = ImageDraw.Draw(im)
for k, v in S.items():
    x0, y0, x1, y1 = [c * 2 for c in v['bbox']]
    d.rectangle([x0, y0, x1, y1], outline=(255, 0, 255) if 'glow' not in k else (255, 160, 0), width=1)
im.crop((180, 360, 1340, 900)).save(kit.WORK / 'board' / 'v_slots1.png')
im.crop((1440, 900, 2752, 1500)).save(kit.WORK / 'board' / 'v_slots2.png')
im.crop((2000, 940, 2752, 1460)).save(kit.WORK / 'board' / 'v_slots3.png')
