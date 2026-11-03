"""Merge supporting tones across all my components (graphic-*, pattern-*): any two closer than dE2000 3
become one (usage-weighted mean); palette colours are kept exactly. Rewrites the SVGs and patterns.json,
and records the registry in fit/graphic-tones.json (name, hex, where used)."""
import glob
import json
import os
import re
import sys
import numpy as np
import kit
from tones import merge_tones

B = r'C:\Users\dalig\Desktop\AllianceAIPartners\Organization\alliance-ai-partners\docs\brand-kit\_build'
C = B + r'\components'
REG = B + r'\fit\graphic-tones.json'
PAL = {v: k for k, v in kit.PALETTE.items()}
ROLE_HINT = {"#17BEF2": "Glow Cyan (wave halo)"}


def files():
    return sorted(glob.glob(C + r'\graphic-*.svg') + glob.glob(C + r'\pattern-*.svg'))


def usage():
    use, cnt = {}, {}
    for f in files():
        for h in re.findall(r'(?:fill|stop-color|stroke)="(#[0-9A-Fa-f]{6})"', open(f, encoding='utf-8').read()):
            h = h.upper()
            use.setdefault(h, set()).add(os.path.basename(f))
            cnt[h] = cnt.get(h, 0) + 1
    return use, cnt


def name_of(h):
    L, a, b = kit.srgb_to_lab(kit.hexrgb(h))
    hue, C = np.degrees(np.arctan2(b, a)) % 360, float(np.hypot(a, b))
    fam = ("Royal Blue" if hue >= 285 else "Blue" if hue >= 265 else "Steel Blue" if hue >= 245 else
           "Ocean" if hue >= 225 else "Teal" if hue >= 205 else "Aqua")
    if C < 28:
        fam = "Slate" if hue >= 245 else "Muted " + fam
    if L < 20:
        fam = "Ink " + fam
    return f"{fam} {int(round(L))}"


def main():
    use, cnt = usage()
    sup = [h for h in use if h not in PAL]
    mapping = merge_tones(sup, [cnt[h] for h in sup], limit=3.0)
    changed = {k: v for k, v in mapping.items() if k != v}
    for f in files():
        s = open(f, encoding='utf-8').read()
        s2 = re.sub(r'((?:fill|stop-color|stroke)=")(#[0-9A-Fa-f]{6})(")', lambda m: m.group(1) + mapping.get(m.group(2).upper(), m.group(2).upper()) + m.group(3), s)
        if s2 != s:
            open(f, 'w', encoding='utf-8').write(s2)
    pj = C + r'\patterns.json'
    P = json.load(open(pj))
    for t in P["tiles"]:
        t["background"] = mapping.get(t["background"].upper(), t["background"])
        if "background_gradient" in t:
            t["background_gradient"]["stops"] = [[o, mapping.get(c.upper(), c)] for o, c in t["background_gradient"]["stops"]]
        t["colors"] = list(dict.fromkeys(mapping.get(c.upper(), c) for c in t["colors"]))
        if "ramp" in t:
            t["ramp"] = [mapping.get(c.upper(), c) for c in t["ramp"]]
    json.dump(P, open(pj, 'w'), indent=1)
    use, cnt = usage()
    tones, seen = [], set()
    for h in sorted(use, key=lambda h: kit.srgb_to_lab(kit.hexrgb(h))[0]):
        n, ph, de = kit.nearest_palette(h)
        nm = PAL.get(h) or ROLE_HINT.get(h) or name_of(h)
        while nm in seen:  # keep names unique
            nm += "+"
        seen.add(nm)
        tones.append({"hex": h, "name": nm, "palette": h in PAL,
                      "nearest_palette": n, "de_to_nearest": round(de, 2), "uses": cnt[h], "used_in": sorted(use[h])})
    reg = {"rule": "palette colours exact; supporting tones merged when closer than dE2000 3 (usage-weighted)",
           "merged": changed, "tones": tones}
    json.dump(reg, open(REG, 'w'), indent=1)
    labs = [kit.srgb_to_lab(kit.hexrgb(t["hex"])) for t in tones if not t["palette"]]
    dmin = min(float(kit.de2000(labs[i], labs[j])) for i in range(len(labs)) for j in range(i + 1, len(labs)))
    print('merged', len(changed), 'colours; supporting tones now', sum(not t["palette"] for t in tones), 'min separation %.2f' % dmin)
    for t in tones:
        print('  %s %-22s %-5s uses %4d  %s' % (t["hex"], t["name"], 'PAL' if t["palette"] else '', t["uses"], ', '.join(t["used_in"])))


if __name__ == '__main__':
    main()
