"""Scratch: summary table of text fits (board agent)."""
import json, sys
sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build\work\board')
from runs import RUNS
files = sys.argv[1:] or ['tf_A.json', 'tf_B.json', 'tf_C.json', 'tf_D.json']
R = {}
for f in files:
    R.update(json.load(open(f)))
for rid, s, *_ in RUNS:
    if rid not in R:
        print('%-15s MISSING' % rid); continue
    b = R[rid]['best']
    g = max(R[rid]['global'], key=lambda r: r['iou_soft'])
    gb = max(R[rid]['global'], key=lambda r: r['iou'])
    print('%-15s %-9s size=%6.2f trk=%6.1f  kerned bin=%.3f soft=%.3f | global best %s bin=%.3f | best-bin global %s %.3f' % (
        rid, b['style'], b['size'], b['tracking'], b['iou'], b['iou_soft'], g['style'], g['iou'], gb['style'], gb['iou']))
