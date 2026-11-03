"""Generate the website's new images with Gemini, from the image manifest of the Figma website mock.

Each "new" entry in design-system/imagery/website/manifest.json holds a full prompt (palette, light, exclusions and
where text will sit). This script generates every missing image at the nearest aspect ratio Gemini supports, then
saves a JPEG master, a web WebP and a JSON sidecar with the exact prompt and model (its provenance), the same way
brand-kit/tools/generate-imagery.py does for the backgrounds. Existing images are skipped; pass ids to regenerate.

    python brand-kit/tools/generate-website-images.py [IMG-01-1 ...]   # key: GEMINI_API_KEY in the environment or .env

Needs the google-genai and Pillow packages (the gemini-image-generator skill's venv has both). In a cloud session the
environment must allow generativelanguage.googleapis.com.

After generating, review every image by eye (palette only, no text, the calm area where the manifest says), then
place them in the Figma file's image slots (the manifest lists each slot's node ids).
"""
import datetime
import io
import json
import os
import re
import sys
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "design-system/imagery/website"
MANIFEST = OUT / "manifest.json"
MODEL = "gemini-3-pro-image-preview"
RATIOS = {"1:1": 1, "4:5": 0.8, "5:4": 1.25, "3:4": 0.75, "4:3": 4 / 3, "2:3": 2 / 3, "3:2": 1.5, "9:16": 9 / 16, "16:9": 16 / 9, "21:9": 21 / 9}


def key():
    """GEMINI_API_KEY from the environment, else from the repo's gitignored .env. Never printed."""
    k = os.environ.get("GEMINI_API_KEY")
    env = ROOT / ".env"
    if not k and env.exists():
        for line in env.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            name, _, value = (line[7:] if line.startswith("export ") else line).partition("=")
            if name.strip() == "GEMINI_API_KEY":
                k = value.strip().strip("\"'")
                break
    if not k:
        sys.exit("GEMINI_API_KEY is not set (environment or .env)")
    return k


def aspect_of(text):
    """Nearest supported ratio to an aspect written as '640x760', '4:5' or '640x760 (about 4:5)'."""
    text = text or "16:9"
    m = re.search(r"(\d+(?:\.\d+)?)\s*[x:×]\s*(\d+(?:\.\d+)?)", text)
    r = float(m.group(1)) / float(m.group(2)) if m else 16 / 9
    return min(RATIOS, key=lambda k: abs(RATIOS[k] - r))


def generate(client, prompt, aspect, size="2K"):
    r = client.models.generate_content(model=MODEL, contents=[prompt], config=types.GenerateContentConfig(
        response_modalities=["IMAGE"], image_config=types.ImageConfig(aspect_ratio=aspect, image_size=size)))
    for part in r.candidates[0].content.parts:
        if getattr(part, "inline_data", None) and part.inline_data.data:
            return Image.open(io.BytesIO(part.inline_data.data)).convert("RGB")
    raise RuntimeError("no image in the response")


def main():
    only = set(sys.argv[1:])
    entries = [e for e in json.loads(MANIFEST.read_text(encoding="utf-8")) if e.get("kind") == "new"]
    client = genai.Client(api_key=key())
    today = datetime.date.today().isoformat()
    made = 0
    for e in entries:
        base = OUT / e["id"]
        if (only and e["id"] not in only) or (not only and base.with_suffix(".jpg").exists()):
            continue
        aspect = aspect_of(e.get("aspectDesktop") or e.get("aspectMobile"))
        print(f"generating {e['id']} ({aspect})", flush=True)
        try:
            img = generate(client, e.get("prompt") or e["source"], aspect)
        except Exception as ex:  # one failed image never stops the batch
            print(f"  failed: {ex}", flush=True)
            continue
        OUT.mkdir(parents=True, exist_ok=True)
        img.save(base.with_suffix(".jpg"), quality=92, optimize=True, progressive=True)
        web = img.resize((1920, round(img.height * 1920 / img.width)), Image.LANCZOS) if img.width > 1920 else img
        web.save(base.with_suffix(".webp"), quality=82, method=6)
        meta = {"id": e["id"], "slot": e.get("slotName"), "alt": e.get("alt"), "prompt": e.get("prompt") or e["source"], "model": MODEL, "aspect_ratio": aspect,
                "size": "2K", "uses": e.get("uses"), "generated": today, "tool": "brand-kit/tools/generate-website-images.py"}
        base.with_suffix(".json").write_text(json.dumps(meta, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
        made += 1
        print(f"  saved {base.with_suffix('.jpg').relative_to(ROOT)} {img.size}", flush=True)
    print(f"{made} images generated this run")


if __name__ == "__main__":
    main()
