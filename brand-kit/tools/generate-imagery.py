"""Generate the brand kit's photographic imagery with Gemini (the gemini-image-generator skill's model): nature backgrounds in
the logo kit's language, and merchandise mockups conditioned on the real logo files. Each image ships with a JSON sidecar
holding its exact prompt, model, aspect ratio and references (its provenance). Existing images are skipped, so a rerun
only fills gaps; pass names to regenerate just those.

    <skill venv python> brand-kit/tools/generate-imagery.py [name ...]   # key: GEMINI_API_KEY in the environment or the repo's .env
"""
import datetime
import io
import json
import os
import sys
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
DS, BK = ROOT / "design-system", ROOT / "brand-kit"
MODEL = "gemini-3-pro-image-preview"
LOGO = DS / "logos"
STYLE = ("Colour palette strictly limited to deep navy #121B2A, electric blue #1B56FF, luminous cyan #00D5FF and pale daylight #F4F7FB, "
         "with their in-between shades. Premium, calm editorial brand imagery with generous negative space and soft light from the upper left. "
         "No text, letters, numbers, logos, people, robots, circuit patterns, sparkles, purple or pink.")
BACKGROUNDS = {  # name: (aspect, prompt, description)
    "daybreak-swallows": ("16:9", "Five swallows in flight across a daybreak sky that grades from deep navy at the lower left through electric blue to luminous cyan at the upper right. "
                          "The swallows are faceted like cut glass, their flat planes catching the light in the same blues, and one glossy satin ribbon in the same gradient trails "
                          "through the flock like a flight path. Wide, airy composition with open sky on the left two thirds.",
                          "Faceted swallows and a satin ribbon crossing a Daybreak sky; open sky on the left for a headline."),
    "ribbon-blossoms": ("16:9", "Five flowers made from folded glossy satin ribbon: each blossom's petals are loops of ribbon in electric blue and luminous cyan, with deep navy stems, "
                        "arranged in a loose diagonal from the lower right on a pale daylight ground. Studio product photography, crisp soft shadows falling to the lower right, "
                        "the left half left almost empty.",
                        "Blossoms folded from blue and cyan satin ribbon on Daylight; the left half stays clear for text."),
    "faceted-leaves": ("16:9", "A close crop of large, simple oval leaves built from flat faceted planes in navy and blue shades, lit from the upper left so the facet "
                       "edges glow cyan, against a deep navy ground that falls into darkness on the right. Quiet, rich and dark, made to sit behind white text.",
                       "Faceted leaves in navy and blue on deep navy; a dark ground for white text."),
    "faceted-swallow": ("1:1", "A single swallow in flight with its wings fully spread, rendered as a faceted low-poly sculpture in deep navy, electric blue and luminous cyan, "
                        "centred on a pale daylight background with a soft contact shadow below it. Elegant, minimal, museum-object lighting.",
                        "The swallow as a faceted sculpture on Daylight, centred."),
    "ribbon-river": ("16:9", "An aerial view at daybreak of a river winding like a ribbon through gentle faceted hills. The river reflects a gradient from electric blue to "
                     "luminous cyan, the hills are layered deep navy and slate-blue planes, and soft mist lies in the valleys. Calm and vast, with the top third open sky.",
                     "A river winding like the ribbon through faceted hills at daybreak; open sky at the top."),
    "paper-garden": ("16:9", "A garden of folded-paper flowers and leaves in daylight white and pale blue-grey, with a few accents in electric blue and luminous cyan, "
                     "softly lit with a shallow depth of field, a light and airy ground that dark text can sit on.",
                     "Folded-paper flowers in Daylight and pale blue with blue and cyan accents; light enough for dark text."),
    "dawn-wave": ("16:9", "A single ocean wave curling like a glossy satin ribbon at dawn: deep navy water rising through electric blue to a luminous cyan crest of light, "
                  "under a dark navy sky, with a low horizon. Minimal, still and calm.",
                  "One wave curling like a satin ribbon at dawn, navy to cyan; dark sky above."),
    "meadow-first-light": ("9:16", "A meadow of wildflowers at first light seen from low down: the flower heads are faceted glass in electric blue and luminous cyan on deep navy "
                           "stems, the sky grades from pale daylight to soft blue, and two swallows fly far off. Vertical composition with open sky in the upper half.",
                           "Faceted glass wildflowers at first light with distant swallows; vertical, for stories."),
}
MERCH = {  # name: (aspect, references, prompt)
    "cap": ("1:1", [LOGO / "marks/alliance-ai-partners-logomark-flat-dark.png"],
            "Product photograph of a structured six-panel baseball cap in deep navy (#121B2A), three-quarter front view, on a pale daylight-grey studio backdrop. "
            "The front panel carries exactly the logo in the reference image as flat embroidery in a single cyan thread (#00D5FF), centred and about 6 cm wide, with "
            "realistic satin-stitch texture. Soft light from the upper left, gentle shadow. No other text or logos anywhere."),
    "tumbler": ("1:1", [LOGO / "marks/alliance-ai-partners-logomark-full-color-dark.png"],
                "Product photograph of a 20 oz insulated stainless tumbler with a clear slide lid, powder-coated in deep navy (#121B2A), standing on a pale daylight-grey "
                "surface. The front shows exactly the logo in the reference image, printed in full colour about 5 cm wide, and a thin flowing ribbon line in a blue-to-cyan "
                "gradient wraps around the tumbler behind it. Soft studio light from the upper left. No other text or logos."),
    "tee": ("1:1", [LOGO / "marks/alliance-ai-partners-logomark-flat-dark.png"],
            "Flat-lay product photograph of a deep navy (#121B2A) cotton t-shirt, neatly folded, on a pale daylight-grey surface. The left chest carries exactly the logo "
            "in the reference image, screen printed small in a single cyan ink (#00D5FF). Soft daylight from the upper left. No other text or logos."),
    "hoodie": ("1:1", [LOGO / "marks/alliance-ai-partners-logomark-flat-dark.png"],
               "Product photograph of a heavyweight deep navy (#121B2A) hoodie hanging on a light wooden hanger against a pale daylight-grey wall. The centre chest carries "
               "exactly the logo in the reference image as flat embroidery in a single cyan thread (#00D5FF), about 10 cm wide. Soft light from the upper left. No other text."),
    "tote": ("1:1", [BK / "merch/previews/tote-front-artwork.png"],
             "Product photograph of a natural off-white canvas tote bag hanging from a hook against a pale daylight wall. The front is screen printed with exactly the "
             "artwork in the reference image (the logo lockup and the flowing ribbon line beneath it) in deep navy and electric blue inks. "
             "Soft light from the upper left. No other text or logos."),
    "notebook": ("1:1", [LOGO / "marks/alliance-ai-partners-logomark-mono-black.png"],
                 "Product photograph of an A5 hardcover notebook bound in deep navy (#121B2A) linen, lying at a slight angle on a pale daylight-grey desk. Exactly the logo in "
                 "the reference image is blind-debossed (pressed in, no ink) in the centre of the cover, and a luminous cyan (#00D5FF) satin ribbon bookmark hangs out of "
                 "the bottom. Soft light from the upper left. No other text or logos."),
    "mug": ("1:1", [LOGO / "marks/alliance-ai-partners-logomark-full-color-light.png"],
            "Product photograph of a white glossy ceramic mug on a pale daylight-grey surface, handle to the right. The side facing the camera shows exactly the logo in the "
            "reference image printed in full colour about 5 cm wide, with a thin flowing ribbon line in a navy-to-cyan gradient beneath it. Soft light from the upper left. "
            "No other text or logos."),
    "stickers": ("1:1", [BK / "merch/previews/sticker-sheet-a5-artwork.png"],
                 "Product photograph of the die-cut vinyl stickers shown in the reference image, peeled off the sheet and stuck on the lid of a silver laptop that rests on a "
                 "pale daylight-grey desk: the pill-shaped navy logo sticker, the round navy logo sticker and the blue sticker reading 'Put AI to work.'. Reproduce the "
                 "stickers' artwork exactly. Soft light from the upper left."),
    "lanyard-badge": ("1:1", [BK / "merch/previews/id-badge-cr80-artwork.png", BK / "merch/previews/lanyard-20mm-artwork.png"],
                      "Product photograph of a white PVC ID badge exactly like the first reference image, hanging from a flat 20 mm lanyard printed with the gradient strap in "
                      "the second reference image (deep navy through electric blue to cyan), lying on a pale daylight-grey surface. Keep the badge's placeholder text as "
                      "shown. Soft light from the upper left."),
}


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


def generate(client, prompt, aspect, refs, size="2K"):
    contents = [prompt] + [Image.open(r) for r in refs]
    r = client.models.generate_content(model=MODEL, contents=contents, config=types.GenerateContentConfig(
        response_modalities=["IMAGE"], image_config=types.ImageConfig(aspect_ratio=aspect, image_size=size)))
    for part in r.candidates[0].content.parts:
        if getattr(part, "inline_data", None) and part.inline_data.data:
            return Image.open(io.BytesIO(part.inline_data.data)).convert("RGB")
    raise RuntimeError("no image in the response")


def save(img, base, meta, web_width):
    """Master as JPEG q92, a web WebP at web_width, and the provenance sidecar."""
    base.parent.mkdir(parents=True, exist_ok=True)
    img.save(base.with_suffix(".jpg"), quality=92, optimize=True, progressive=True)
    w = img.resize((web_width, round(img.height * web_width / img.width)), Image.LANCZOS) if img.width > web_width else img
    w.save(base.with_suffix(".webp"), quality=82, method=6)
    base.with_suffix(".json").write_text(json.dumps(meta, indent=1) + "\n", encoding="utf-8")


def main():
    only = set(sys.argv[1:])
    client = genai.Client(api_key=key())
    today = datetime.date.today().isoformat()
    made = []
    jobs = [("background", n, a, p + " " + STYLE, [], DS / "imagery/backgrounds" / n, d) for n, (a, p, d) in BACKGROUNDS.items()] + \
           [("mockup", n, a, p, refs, BK / "merch/mockups" / n, f"{n} mockup") for n, (a, refs, p) in MERCH.items()]
    for kind, name, aspect, prompt, refs, base, desc in jobs:
        if (only and name not in only) or (not only and base.with_suffix(".jpg").exists()):
            continue
        print(f"generating {kind} {name} ({aspect})", flush=True)
        try:
            img = generate(client, prompt, aspect, refs)
        except Exception as e:  # one failed image never stops the batch
            print(f"  failed: {e}", flush=True)
            continue
        meta = {"name": name, "kind": kind, "description": desc, "prompt": prompt, "model": MODEL, "aspect_ratio": aspect, "size": "2K",
                "references": [r.relative_to(ROOT).as_posix() for r in refs], "generated": today, "tool": "brand-kit/tools/generate-imagery.py"}
        save(img, base, meta, 1920 if kind == "background" else 1200)
        made.append((kind, name, base))
        print(f"  saved {base.with_suffix('.jpg').relative_to(ROOT)} {img.size}", flush=True)
    # register backgrounds in the imagery manifest
    man_path = DS / "imagery/imagery.json"
    man = json.loads(man_path.read_text(encoding="utf-8"))
    man["files"] = [f for f in man["files"] if f.get("category") != "background"]
    for side in sorted((DS / "imagery/backgrounds").glob("*.json")):
        m = json.loads(side.read_text(encoding="utf-8"))
        man["files"].append({"path": f"imagery/backgrounds/{side.stem}.webp", "master": f"imagery/backgrounds/{side.stem}.jpg", "category": "background",
                             "name": side.stem, "description": m["description"], "aspect_ratio": m["aspect_ratio"], "prompt": m["prompt"],
                             "provenance": f"imagery/backgrounds/{side.name}", "source": f"Generated with {m['model']} on {m['generated']}", "derived": True})
    man_path.write_text(json.dumps(man, indent=1) + "\n", encoding="utf-8")
    print(f"{len(made)} images generated this run")


if __name__ == "__main__":
    main()
