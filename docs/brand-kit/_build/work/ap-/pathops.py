"""VectorCraft Pathfinder on SVG path data (headless CLI)."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build')
import kit


def vc_pathfinder(paths, op, out_svg):
    """paths: [(id, d)] back -> front; returns the result path d strings (VectorCraft Pathfinder)."""
    body = '\n'.join(f'<path id="{i}" d="{d}" fill="#000000" fill-rule="evenodd"/>' for i, d in paths)
    with tempfile.TemporaryDirectory(dir=kit.WORK) as td:
        src = Path(td) / 'in.svg'
        src.write_text(kit.svg_doc(1024, 1024, body), encoding='utf-8')
        cmds = Path(td) / 'c.json'
        cmds.write_text(json.dumps([{'command': 'select.all', 'params': {}},
                                    {'command': f'object.pathfinder.{op}', 'params': {'precision': 0.01, 'removeRedundantPoints': True}}]))
        kit._vc(['run', '--in', src, '--commands', cmds, '--export', out_svg])
    return [d for d, a in kit.parse_svg_paths(Path(out_svg).read_text(encoding='utf-8'))]


