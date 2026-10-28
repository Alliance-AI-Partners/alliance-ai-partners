#!/usr/bin/env python3
"""Alliance AI Partners logo explorations: one folder per generation tool, one subfolder per direction.

    python generate_logos.py muapi              # 1  muapi-logo-creator skill (Ideogram v3), then a Gemini refine
    python generate_logos.py logocreator        # 2  logo-creator skill: 3 Nano Banana variations + preview.html
    python generate_logos.py recraft            # 3  Recraft V4.1 vector (SVG), top 5
    python generate_logos.py nanobanana         # 4  Nano Banana 2 (gemini-3.1-flash-image) lockups at 2K
    python generate_logos.py refine <png> <rank>  # Gemini touch-up of one image, saved beside it
    python generate_logos.py preview <folder> <title>  # rebuild a logo-creator preview.html
    python generate_logos.py trace <png> <rank>  # VectorCraft logo-mode trace -> .svg .ai .vectorcraft .png
    python generate_logos.py svg <svg>          # re-save a Recraft SVG as .ai .vectorcraft .png via VectorCraft
    python generate_logos.py board <track>      # Illustrator board: artboard per direction + real-font wordmark

Reads GEMINI_API_KEY, MUAPI_API_KEY and RECRAFT_API_KEY from the repo's .env and never prints them.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

LOGOS = Path(__file__).resolve().parents[1]
REPO = LOGOS.parents[1]
SKILLS = Path.home() / ".claude" / "skills"
NANO = SKILLS / "nanobanana" / "scripts"
BASH = r"C:\Program Files\Git\bin\bash.exe"
VECTORCRAFT = r"C:\Program Files\VectorCraft\vectorcraft-cli.exe"
TRACKS = {"muapi": "1-muapi-logo-creator", "logocreator": "2-logo-creator",
          "recraft": "3-recraft", "nanobanana": "4-nanobanana"}
SPEC = json.loads(Path(__file__).with_name("directions.json").read_text(encoding="utf-8"))
BRAND = SPEC["brand"]


def keys_env():
    env = dict(os.environ)
    for line in (REPO / ".env").read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*(?:export\s+)?(GEMINI_API_KEY|MUAPI_API_KEY|RECRAFT_API_KEY)\s*=\s*(.*?)\s*$", line)
        if m:
            env[m[1]] = m[2].strip("'\"")
    return env


def run(cmd, env):
    r = subprocess.run([str(c) for c in cmd], env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    print("   " + "\n   ".join((r.stdout + r.stderr).strip().splitlines()[-6:]), flush=True)
    return r.returncode == 0


def start_track(name, ranks):
    out = LOGOS / TRACKS[name]
    out.mkdir(parents=True, exist_ok=True)
    if not ranks:  # a full run starts a fresh prompt log; rerunning some directions appends to it
        (out / "prompts.md").write_text(f"# {TRACKS[name]}: prompts sent\n\n", encoding="utf-8")
    return out


def pick(count, ranks):
    return [d for d in SPEC["directions"][:count] if not ranks or d["rank"] in ranks]


def log_prompt(track_dir, d, model, prompt):
    with open(track_dir / "prompts.md", "a", encoding="utf-8") as f:
        f.write(f"## {d['rank']:02d} {d['name']}\n\nModel: {model}\n\n{prompt}\n\n")


def folder_for(out, d):
    folder = out / d["folder"]
    folder.mkdir(parents=True, exist_ok=True)
    print(f"[{out.name}] {d['folder']}", flush=True)
    return folder


def refine(src, d, env):
    dst = src.with_name(src.stem + "__gemini-refined.png")
    prompt = (f"Refine this logo into a clean, production-ready flat vector mark. Keep its idea: {d['mark']}. "
              f"Redraw it with crisp edges and exact geometry using only these flat colors: {d['palette_text']}, "
              "on a pure white background, perfectly centered with a generous margin. "
              "No text, no gradients, no shadows, no texture, no 3D.")
    ok = run([sys.executable, NANO / "generate.py", prompt, "-i", src, "-r", "1:1", "-o", dst], env)
    log_prompt(src.parents[1], d, f"gemini-3.1-flash-image, editing {src.name}" + ("" if ok else " (FAILED, no image)"), prompt)
    return ok


def write_preview(folder, title):
    html = (SKILLS / "logo-creator" / "templates" / "preview.html").read_text(encoding="utf-8")
    cards = "\n".join(
        f'    <div class="logo-card" data-src="{p.name}" onclick="showModal(this)">\n'
        f'      <img src="{p.name}" onerror="this.parentElement.style.display=\'none\'">\n'
        f'      <p>{p.stem.split("__", 1)[-1]}</p>\n'
        '    </div>'
        for p in sorted(folder.glob("*.png")))
    html = re.sub(r'(<div class="grid" id="grid">).*?(</div>\s*<div class="favorites-bar">)',
                  lambda m: m[1] + "\n" + cards + "\n  " + m[2], html, flags=re.S)
    html = html.replace("<h1>Logo Preview Gallery</h1>", f"<h1>{title}</h1>")
    (folder / "preview.html").write_text(html, encoding="utf-8")


def track_muapi(env, ranks):
    out = start_track("muapi", ranks)
    script = (SKILLS / "muapi-logo-creator" / "scripts" / "create-logo.sh").as_posix()
    model = os.environ.get("MUAPI_LOGO_MODEL", "ideogram")  # the skill takes any muapi image model
    label = "ideogram-v3" if model == "ideogram" else model
    for d in pick(8, ranks):
        folder = folder_for(out, d)
        before = set(folder.iterdir())
        log_prompt(out, d, f"{model} through muapi-logo-creator create-logo.sh",
                   f"--concept {d['mark']}\n\n--color {d['palette_text']}\n\n--style minimalist --type abstract mark")
        run([BASH, script, "--brand", BRAND, "--concept", d["mark"], "--style", "minimalist",
             "--color", d["palette_text"], "--type", "abstract mark", "--model", model,
             "--out", folder.as_posix()], env)
        new = [p for p in folder.iterdir()
               if p not in before and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
        if not new:
            print("   no image returned", flush=True)
            continue
        raw = new[0].rename(folder / f"{d['folder']}__muapi-{label}{new[0].suffix.lower()}")
        refine(raw, d, env)


def track_logocreator(env, ranks):
    out = start_track("logocreator", ranks)
    for d in pick(8, ranks):
        folder = folder_for(out, d)
        prompt = (f"Minimalist flat design logo for {BRAND}, an AI partner for small businesses: {d['mark']}. "
                  f"Colors: {d['palette_text']}, on a plain white background. "
                  "Clean lines, simple geometric shapes, centered, no text.")
        log_prompt(out, d, "gemini-3.1-flash-image through nanobanana batch_generate.py, 3 variations", prompt)
        run([sys.executable, NANO / "batch_generate.py", prompt, "-n", "3", "-r", "1:1", "-d", folder,
             "-p", f"{d['folder']}__logo-creator", "--delay", "2"], env)
        write_preview(folder, f"{d['rank']:02d} {d['name']} - logo-creator")


def rgb(hex_color):
    return [int(hex_color[i:i + 2], 16) for i in (1, 3, 5)]


def track_recraft(env, ranks):
    out = start_track("recraft", ranks)
    for d in pick(5, ranks):
        folder = folder_for(out, d)
        prompt = (f"Logo symbol for {BRAND}: {d['mark']}. Flat vector logo with solid flat colors only, "
                  "no gradients, no shadows, no text, centered on a plain white background with a generous margin.")
        log_prompt(out, d, "recraftv4_1_vector (Recraft V4.1, SVG)", prompt + "\n\nPalette control: " + ", ".join(d["colors"]))
        body = {"prompt": prompt, "model": "recraftv4_1_vector",
                "controls": {"colors": [{"rgb": rgb(c)} for c in d["colors"]],
                             "background_color": {"rgb": [255, 255, 255]}}}
        req = urllib.request.Request("https://external.api.recraft.ai/v1/images/generations/vector",
                                     data=json.dumps(body).encode(), method="POST",
                                     headers={"Authorization": f"Bearer {env['RECRAFT_API_KEY']}",
                                              "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                url = json.load(r)["data"][0]["url"]
            dst = folder / f"{d['folder']}__recraft-v4.1-vector.svg"
            urllib.request.urlretrieve(url, dst)
            print(f"   saved {dst.name}", flush=True)
        except Exception as e:  # one failure shouldn't stop the other directions
            detail = e.read().decode(errors="replace")[:300] if hasattr(e, "read") else e
            print(f"   failed: {detail}", flush=True)


def track_nanobanana(env, ranks):
    out = start_track("nanobanana", ranks)
    for d in pick(8, ranks):
        folder = folder_for(out, d)
        prompt = (f"Professional brand logo for {BRAND}: a symbol centered above a wordmark. Symbol: {d['mark']}. "
                  f"Wordmark below the symbol: {d['wordmark_desc']}. Colors: {d['palette_text']}. "
                  "Flat vector logo design, solid colors only, pure white background, centered with a generous "
                  "margin, no mockup, no gradients, no shadows, no texture, no other text.")
        log_prompt(out, d, "gemini-3.1-flash-image (Nano Banana 2) through nanobanana generate.py, 2K", prompt)
        run([sys.executable, NANO / "generate.py", prompt, "-r", "1:1", "-s", "2K",
             "-o", folder / f"{d['folder']}__nano-banana-2__lockup.png"], env)


def trace(src, d):
    """Trace a flat raster logo in VectorCraft's logo mode, snapped to the direction's exact palette.
    A non-white background (Ideogram often picks near-black) is keyed to white first, so it drops out too.
    Outputs keep the source's name (tool and model included) plus __vectorcraft-trace."""
    from PIL import Image
    stem = src.parent / f"{src.stem}__vectorcraft-trace"
    im = Image.open(src).convert("RGB")
    w, h = im.size
    edge = [im.getpixel((x, y)) for x in range(0, w, 8) for y in (0, h - 1)] + \
           [im.getpixel((x, y)) for y in range(0, h, 8) for x in (0, w - 1)]
    bg = tuple(sorted(c[i] for c in edge)[len(edge) // 2] for i in range(3))
    if min(bg) < 235:  # ponytail: plain per-pixel loop, ~2 s per 1K image; numpy if this ever gets slow
        px = im.load()
        for y in range(h):
            for x in range(w):
                if sum((a - b) ** 2 for a, b in zip(px[x, y], bg)) < 40 ** 2:
                    px[x, y] = (255, 255, 255)
        src = Path(tempfile.gettempdir()) / f"{stem.name}-keyed.png"
        im.save(src)
    # Lockups also carry the wordmark's gray secondary type, so allow the wordmark colors too.
    colors = d["colors"] + ([w["color"] for w in d["wordmark"]] if "__lockup" in src.name else [])
    params = {"mode": "logo", "logoColors": list(dict.fromkeys(colors)), "ignoreWhite": True}
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump([{"command": "select.all", "params": {}},
                   {"command": "imageTrace.makeAndExpand", "params": {"params": params}}], f)
    exports = [x for ext in (".svg", ".ai", ".vectorcraft", ".png") for x in ("--export", f"{stem}{ext}")]
    ok = run([VECTORCRAFT, "run", "--in", src, "--commands", f.name] + exports, os.environ)
    os.unlink(f.name)
    return ok


def vectorize_svg(svg):
    """Recraft already returns SVG; VectorCraft only re-saves it as .ai, .vectorcraft and a .png preview."""
    return all(run([VECTORCRAFT, "convert", svg, svg.with_suffix(ext)], os.environ)
               for ext in (".ai", ".vectorcraft", ".png"))


SOURCES = {"muapi": "muapi-logo-creator, traced in VectorCraft",
           "logocreator": "logo-creator with Nano Banana 2, traced in VectorCraft",
           "recraft": "Recraft V4.1 vector, native SVG",
           "nanobanana": "Nano Banana 2 lockup, traced in VectorCraft"}


def board(track):
    """One Illustrator document per track: an artboard per direction that has a vector, real-font wordmark."""
    out = LOGOS / TRACKS[track]
    items = []
    for d in pick(8, []):
        folder = out / d["folder"]
        art = next(iter(sorted(folder.glob("*__vectorcraft-trace.svg")) or sorted(folder.glob("*-vector.svg"))), None)
        if not art:
            continue
        items.append({"name": d["folder"], "art": art.as_posix(), "wordmark": d["wordmark"],
                      "caption": f"{TRACKS[track]}  |  {d['rank']:02d} {d['name']}  |  {art.name}  |  {SOURCES[track]}"})
    config = {"items": items, "lockup": track == "nanobanana",
              "out": (out / f"{TRACKS[track]}__illustrator-board.ai").as_posix(),
              "preview": (out / f"{TRACKS[track]}__illustrator-board.png").as_posix()}
    jsx = Path(tempfile.gettempdir()) / f"board-{track}.jsx"
    jsx.write_text("var BOARD = " + json.dumps(config) + ";\n"
                   + Path(__file__).with_name("build_board.jsx").read_text(encoding="utf-8"), encoding="utf-8")
    return run(["powershell", "-NoProfile", "-Command",
                f"$ai = New-Object -ComObject Illustrator.Application; $ai.DoJavaScriptFile('{jsx}')"], os.environ)


if __name__ == "__main__":
    env = keys_env()
    cmd = sys.argv[1]
    if cmd == "refine":
        ok = refine(Path(sys.argv[2]), SPEC["directions"][int(sys.argv[3]) - 1], env)
        sys.exit(0 if ok else 1)
    if cmd == "preview":
        write_preview(Path(sys.argv[2]), sys.argv[3])
        sys.exit(0)
    if cmd == "trace":
        sys.exit(0 if trace(Path(sys.argv[2]), SPEC["directions"][int(sys.argv[3]) - 1]) else 1)
    if cmd == "svg":
        sys.exit(0 if vectorize_svg(Path(sys.argv[2])) else 1)
    if cmd == "board":
        sys.exit(0 if board(sys.argv[2]) else 1)
    {"muapi": track_muapi, "logocreator": track_logocreator,
     "recraft": track_recraft, "nanobanana": track_nanobanana}[cmd](env, [int(r) for r in sys.argv[2:]])
