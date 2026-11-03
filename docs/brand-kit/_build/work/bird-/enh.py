import sys, numpy as np
from PIL import Image, ImageFilter
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'); import kit
from b_gridcrop import gridcrop
rgb = kit.load('15').astype(float)
bl = np.asarray(Image.fromarray(rgb.astype(np.uint8)).filter(ImageFilter.GaussianBlur(6)), float)
sm = np.asarray(Image.fromarray(rgb.astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)), float)
enh = np.clip(128 + (sm - bl) * 4, 0, 255).astype(np.uint8)
x0, y0, x1, y1, z = map(int, sys.argv[1:6])
gridcrop(enh, x0, y0, x1, y1, z, sys.argv[6])
