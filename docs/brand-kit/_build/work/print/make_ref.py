"""Build pantone_ref.json: PANTONE Solid Coated / Uncoated reference values from published sources.

    python -I make_ref.py <download dir outside the repo>

Each source is downloaded (once, cached) into its own subfolder of the given directory and only parsed as
data: Adobe Color Book (.acb) files hold Pantone's CIELAB D50 values (8-bit: L step 0.39, a/b step 1);
pantonecolors.net mirrors Pantone's published sRGB hex for Solid Coated; pantone.com colour-finder slab
images (lossy WebP) give Pantone's on-screen sRGB for the contenders near the core palette.
"""
import io
import json
import re
import struct
import sys
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import match  # noqa: E402  (lab50, de, kit)

kit = match.kit
GH = "https://raw.githubusercontent.com/"
ACB = {  # set: (description, repository, {side: raw url})
    "pcm": ("Pantone Color Manager export, Nov 2021: 'PANTONE Solid Coated-V4' / 'Solid Uncoated-V4' (.acb, Lab D50; "
            "identical to the V3 export of Aug 2019 for all 1,846 shared colours)",
            "https://github.com/AZ-597/PANTONE-ColorLibraries",
            {"C": GH + "AZ-597/PANTONE-ColorLibraries/main/PANTONE%20Solid%20Coated-V4.acb",
             "U": GH + "AZ-597/PANTONE-ColorLibraries/main/PANTONE%20Solid%20Uncoated-V4.acb"}),
    "plus": ("PANTONE+ Solid Coated / Uncoated colour books as shipped in Adobe CC until 2023 "
             "(.acb, Lab D50, header 'Copyright Pantone LLC, 2010')",
             "https://github.com/Aurorion/Pantone-ACB",
             {"C": GH + "Aurorion/Pantone-ACB/main/PANTONE%2B%20Solid%20Coated.acb",
              "U": GH + "Aurorion/Pantone-ACB/main/PANTONE%2B%20Solid%20Uncoated.acb"}),
    "ok2pan": ("ok2pan compilation, Oct 2026: PANTONE Solid Coated / Uncoated (2,593 colours, Lab D50; per its README "
               "2,140 from Pantone Lab data, the newer colours derived from Pantone Connect sRGB)",
               "https://github.com/blas0/PANTONE-C-U-ACB-Books",
               {"C": GH + "blas0/PANTONE-C-U-ACB-Books/main/PANTONE%20Solid%20Coated.acb",
                "U": GH + "blas0/PANTONE-C-U-ACB-Books/main/PANTONE%20Solid%20Uncoated.acb"}),
    "ok2pan_pn": ("ok2pan compilation: PANTONE Pastels & Neons Coated / Uncoated (210 colours, Lab D50)",
                  "https://github.com/blas0/PANTONE-C-U-ACB-Books",
                  {"C": GH + "blas0/PANTONE-C-U-ACB-Books/main/PANTONE%20Pastels%20%26%20Neons%20Coated.acb",
                   "U": GH + "blas0/PANTONE-C-U-ACB-Books/main/PANTONE%20Pastels%20%26%20Neons%20Uncoated.acb"}),
}
OK2PAN_README = GH + "blas0/PANTONE-C-U-ACB-Books/main/README.md"
WEB = "https://pantonecolors.net/"
SLAB = "https://pantone-web-assets-dev.s3.us-east-2.amazonaws.com/magento/media/color-finder/img/slabs/pantone-color-slab-%s.webp"


def fetch(url, path):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        path.write_bytes(urllib.request.urlopen(req, timeout=60).read())
    return path.read_bytes()


def read_acb(b):
    """Adobe Color Book -> (suffix, [(name, [L, a, b])]). Lab books only (colour space 7)."""
    def ustr(i):
        n, = struct.unpack_from(">I", b, i)
        return b[i + 4:i + 4 + 2 * n].decode("utf-16-be"), i + 4 + 2 * n
    assert b[:4] == b"8BCB"
    i = 8
    _, i = ustr(i)          # title
    _, i = ustr(i)          # prefix
    suffix, i = ustr(i)
    _, i = ustr(i)          # description
    count, _, _, space = struct.unpack_from(">HHHH", b, i)
    i += 8
    assert space == 7, "not a Lab book"
    suffix = re.sub(r"^\$\$\$/[^=]*=", "", suffix)
    out = []
    for _ in range(count):
        name, i = ustr(i)
        L, a, bb = b[i + 6:i + 9]
        i += 9
        name = re.sub(r"^\$\$\$/[^=]*=", "", name).strip()
        if name:
            out.append((name if re.search(r" [CU]$", name) else name + suffix, [round(L * 100 / 255, 2), a - 128, bb - 128]))
    return out


def slab_hex(name, cache):
    if name not in cache:
        try:
            req = urllib.request.Request(SLAB % name.lower().replace(" ", "-"), headers={"User-Agent": "Mozilla/5.0"})
            px = np.asarray(Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=30).read())).convert("RGB")).reshape(-1, 3)
            u, c = np.unique(px, axis=0, return_counts=True)
            cache[name] = kit.rgbhex(u[np.argmax(c)])
        except Exception as e:  # missing slab: record it, keep going
            cache[name] = "error: " + str(e)[:60]
    return cache[name]


def main(dl):
    dl = Path(dl)
    books = {k: {s: dict(read_acb(fetch(u, dl / k / f"{s}.acb"))) for s, u in v[2].items()} for k, v in ACB.items()}
    readme = fetch(OK2PAN_README, dl / "ok2pan_readme" / "README.md").decode("utf-8")
    clipped = set(re.findall(r"^\| ([^|]+? [CU]) \| \d+, \d+, \d+ \|", readme, re.M))
    html = fetch(WEB, dl / "pantonecolors_net" / "index.html").decode("utf-8").replace('\\"', '"')
    web = {}
    for n, h in re.findall(r'\{"id":\d+,"name":"([^"]+)","hex":"(#[0-9A-Fa-f]{6})"', html):
        web.setdefault(n, h.upper())

    ref = {"C": {}, "U": {}}
    for s in "CU":
        names = set(books["pcm"][s]) | set(books["ok2pan"][s]) | set(books["ok2pan_pn"][s]) | set(books["plus"][s])
        for n in sorted(names):
            r = {}
            if n in books["pcm"][s] or n in books["ok2pan"][s]:
                r["guide"] = "Formula Guide"
            elif n in books["ok2pan_pn"][s]:
                r["guide"] = "Pastels & Neons"
            else:
                r["guide"] = "PANTONE+ 2010 only"
            if n in books["pcm"][s]:
                r["pcm"] = books["pcm"][s][n]
            if n in books["plus"][s]:
                r["plus"] = books["plus"][s][n]
            else:
                ok = books["ok2pan"][s].get(n) or books["ok2pan_pn"][s].get(n)
                if ok:
                    r["ok2pan"] = ok
                    if "pcm" not in r and r["guide"] == "Formula Guide":
                        r["note"] = "Lab derived from Pantone Connect sRGB (ok2pan)" + (", sRGB clipped: unreliable" if n in clipped else "")
            if s == "C" and n in web:
                r["web"] = web[n]
            ref[s][n] = r

    # pantone.com slabs for the contenders near each core colour (cached)
    cache_p = dl / "pantone_com_slabs.json"
    cache = json.loads(cache_p.read_text()) if cache_p.exists() else {}
    for s in "CU":
        names = list(ref[s])
        for h in kit.PALETTE.values():
            L = match.lab50(h)
            best = {n: min(match.de(L, ref[s][n][k]) for k in ("pcm", "plus", "ok2pan") if k in ref[s][n]) for n in names}
            lo = min(best.values())
            for n in sorted(best, key=best.get)[:12]:
                if best[n] <= lo + 2.5:
                    hx = slab_hex(n, cache)
                    if hx.startswith("#"):
                        ref[s][n]["slab"] = hx
    cache_p.write_text(json.dumps(cache, indent=1))

    # cross-source agreement, for the record
    def stats(s, a, b):
        d = [match.de(ref[s][n][a] if a != "slab" else match.lab50(ref[s][n][a]),
                      ref[s][n][b] if b not in ("web", "slab") else match.lab50(ref[s][n][b]))
             for n in ref[s] if a in ref[s][n] and b in ref[s][n]]
        return {"n": len(d), "mean": round(float(np.mean(d)), 2), "p95": round(float(np.percentile(d, 95)), 2)}

    web_slab = [int(np.abs(kit.hexrgb(r["web"]) - kit.hexrgb(r["slab"])).max()) for r in ref["C"].values()
                if "web" in r and "slab" in r]
    meta = {
        "lab": "CIELAB D50, 2 deg observer (ICC PCS), as stored in Adobe .acb books: 8-bit, L step 0.39, a/b step 1.",
        "hex": "sRGB as published by Pantone for on-screen use; 'web' = pantonecolors.net mirror of Pantone's Solid Coated "
               "sRGB, 'slab' = dominant pixel of the pantone.com colour-finder slab (lossy WebP, +-1-2 levels).",
        "sets": {k: {"desc": v[0], "url": v[1], "files": v[2]} for k, v in ACB.items()},
        "web": {"desc": "Pantone's published sRGB hex for 2,369 Solid Coated colours as mirrored by pantonecolors.net "
                        "(embedded in its home page; the site calls them screen approximations, and they match the "
                        "pantone.com slabs within %d levels per channel for all %d colours sampled)" % (
                            max(web_slab), len(web_slab)), "url": WEB},
        "slab": {"desc": "pantone.com colour finder slab image, e.g. https://www.pantone.com/color-finder/2726-c", "url": SLAB},
        "not_available": "Pantone Connect (current V5 Lab with decimals) needs a paid account and was not used.",
        "agreement_de2000": {f"{s}: {a} vs {b}": stats(s, a, b) for s in "CU" for a, b in
                             (("pcm", "plus"), ("pcm", "web"), ("pcm", "slab")) if not (s == "U" and b == "web")},
        "counts": {s: {g: sum(r["guide"] == g for r in ref[s].values()) for g in
                       ("Formula Guide", "Pastels & Neons", "PANTONE+ 2010 only")} for s in "CU"},
    }
    out = HERE / "pantone_ref.json"
    out.write_text(json.dumps({"meta": meta, **ref}, indent=0, ensure_ascii=False), encoding="utf-8")
    print(out, json.dumps(meta["counts"]), json.dumps(meta["agreement_de2000"]))


if __name__ == "__main__":
    main(sys.argv[1])
