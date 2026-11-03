"""Compile tokens.json (W3C DTCG) into tokens.css (custom properties + @font-face), tailwind-theme.css (Tailwind v4
@theme) and tokens-manifest.json. Run from anywhere: python design-system/tokens/build-tokens.py"""
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
T = json.loads((HERE / "tokens.json").read_text(encoding="utf-8"))
PREFIX = "--aap"


def var(path):
    return f"{PREFIX}-{path.replace('.', '-')}"


def resolve(v):
    """A {group.token} reference becomes var(--aap-group-token); lists and numbers become CSS text."""
    if isinstance(v, str):
        return re.sub(r"\{([\w.-]+)\}", lambda m: f"var({var(m.group(1))})", v)
    if isinstance(v, list):
        if all(isinstance(x, (int, float)) for x in v):  # cubicBezier
            return f"cubic-bezier({', '.join(f'{x:g}' for x in v)})"
        return ", ".join(f'"{x}"' if " " in x else x for x in v)  # fontFamily
    return f"{v:g}" if isinstance(v, float) else str(v)


lines = []  # (custom property, value, description)


def walk(node, path, typ=None):
    typ = node.get("$type", typ)
    if "$value" in node:
        val = node["$value"]
        if typ == "typography":
            ext = node.get("$extensions", {})
            for k, prop in (("fontFamily", "family"), ("fontSize", "size"), ("fontWeight", "weight"), ("lineHeight", "line-height"), ("letterSpacing", "tracking")):
                lines.append((f"{var(path)}-{prop}", resolve(val[k]), node.get("$description", "") if prop == "size" else ""))
            lines.append((f"{var(path)}-stretch", f"{ext.get('aap.fontStretch', 100):g}%", ""))
        else:
            css = resolve(val)
            if path.startswith("font.stretch."):  # font-stretch only accepts percentages; the JSON keeps plain numbers
                css += "%"
            lines.append((var(path), css, node.get("$description", "")))
        return
    for k, v in node.items():
        if not k.startswith("$") and isinstance(v, dict):
            walk(v, f"{path}.{k}" if path else k, typ)


walk(T, "")

FONTS = """@font-face {
  font-family: "Mona Sans";
  src: url("../fonts/mona-sans/MonaSansVF-wdth-opsz-wght.ttf") format("truetype-variations"),
       url("../fonts/mona-sans/MonaSansVF-wdth-opsz-wght.ttf") format("truetype");
  font-weight: 200 900;
  font-stretch: 75% 125%;
  font-style: normal;
  font-display: swap;
}

@font-face {
  font-family: "Mona Sans";
  src: url("../fonts/mona-sans/MonaSansVF-Italic-wdth-opsz-wght.ttf") format("truetype-variations"),
       url("../fonts/mona-sans/MonaSansVF-Italic-wdth-opsz-wght.ttf") format("truetype");
  font-weight: 200 900;
  font-stretch: 75% 125%;
  font-style: italic;
  font-display: swap;
}

@font-face {
  font-family: "Mona Sans Mono";
  src: url("../fonts/mona-sans/MonaSansMonoVF-wght.ttf") format("truetype-variations"),
       url("../fonts/mona-sans/MonaSansMonoVF-wght.ttf") format("truetype");
  font-weight: 200 900;
  font-style: normal;
  font-display: swap;
}
"""

css = ["/*",
       " * Alliance AI Partners design tokens. Generated from tokens.json (W3C DTCG) by build-tokens.py; edit tokens.json, not this file.",
       " * Palette: the finalized logo kit (docs/brand-kit/_build/palette.json). Fonts: Mona Sans and Mona Sans Mono, SIL OFL 1.1",
       " * (../fonts/mona-sans/OFL.txt). Custom properties only, no utility classes; components live in ../css/components.css.",
       " * Typography roles are fluid: each -size is a clamp() from its 390 px value to its 1440 px value.",
       " */", "", FONTS, ":root {"]
group = None
for prop, val, desc in lines:
    g = prop.split("-")[3] if prop.startswith(f"{PREFIX}-color") else prop.split("-")[2]
    if g != group:
        css.append("")
        group = g
    css.append(f"  {prop}: {val};" + (f" /* {desc} */" if desc and len(desc) < 140 else ""))
css += ["}", "",
        "@media (prefers-reduced-motion: reduce) {",
        "  :root {",
        f"    {PREFIX}-duration-slow: 1ms;",
        f"    {PREFIX}-duration-ribbon: 1ms;",
        "  }",
        "}", ""]
(HERE / "tokens.css").write_text("\n".join(css), encoding="utf-8")

# Tailwind v4: the theme points at the custom properties, so tokens.css stays the one place values live.
TW = {
    "color": {  # utility name -> token path
        **{n: f"color.brand.{n}" for n in ("alliance-blue", "ribbon-cyan", "partner-navy", "daylight")},
        "white": "color.brand.pure-white", "black": "color.print.black",
        **{n: f"color.shading.{n}" for n in T["color"]["shading"]},
        **{f"neutral-{n}": f"color.neutral.{n}" for n in T["color"]["neutral"]},
        "page": "color.surface.page", "raised": "color.surface.raised", "sunken": "color.surface.sunken", "inverse": "color.surface.inverse",
        "inverse-raised": "color.surface.inverse-raised", "scrim": "color.surface.scrim",
        "ink": "color.text.primary", "ink-secondary": "color.text.secondary", "ink-tertiary": "color.text.tertiary", "ink-disabled": "color.text.disabled",
        "link": "color.text.link", "on-action": "color.text.on-action", "ink-inverse": "color.text.inverse",
        "ink-inverse-secondary": "color.text.inverse-secondary", "ink-inverse-tertiary": "color.text.inverse-tertiary",
        "ink-inverse-accent": "color.text.inverse-accent",
        "line-subtle": "color.border.subtle", "line": "color.border.default", "line-strong": "color.border.strong",
        "line-inverse": "color.border.inverse", "line-inverse-strong": "color.border.inverse-strong",
        "action": "color.action.primary", "action-hover": "color.action.primary-hover", "action-pressed": "color.action.primary-pressed",
        "focus": "color.focus.ring", "focus-inverse": "color.focus.ring-inverse",
        **{n: f"color.status.{n}" for n in T["color"]["status"]},
        **{f"chart-{n.split('-')[1]}": f"color.chart.{n}" for n in T["color"]["chart"]}},
}
tw = ["/* Tailwind CSS v4 theme for Alliance AI Partners. Generated by build-tokens.py from tokens.json.",
      "   Load after tokens.css:  @import \"tailwindcss\"; @import \"../design-system/tokens/tokens.css\"; @import \"../design-system/tokens/tailwind-theme.css\";",
      "   The default colour palette is cleared, so only brand colours exist as utilities (bg-page, text-ink, bg-action, border-line...). */",
      "", "@theme inline {", "  --color-*: initial;"]
tw += [f"  --color-{n}: var({var(p)});" for n, p in TW["color"].items()]
tw += ["", f"  --font-sans: var({PREFIX}-font-family-sans);", f"  --font-mono: var({PREFIX}-font-family-mono);", ""]
for name in T["typography"]:
    if name.startswith("$"):
        continue
    b = var(f"typography.{name}")
    tw += [f"  --text-{name}: var({b}-size);", f"  --text-{name}--line-height: var({b}-line-height);",
           f"  --text-{name}--letter-spacing: var({b}-tracking);", f"  --text-{name}--font-weight: var({b}-weight);"]
tw += [""] + [f"  --spacing-{k}: var({var('space.' + k)});" for k in ("section", "gutter")]
tw += [f"  --container-page: var({PREFIX}-size-container);", f"  --container-measure: var({PREFIX}-size-measure);", ""]
tw += [f"  --radius-{k}: var({var('radius.' + k)});" for k in T["radius"] if not k.startswith("$")]
tw += [f"  --shadow-{k}: var({var('shadow.' + k)});" for k in T["shadow"] if not k.startswith("$") and k != "facet-edge"]
tw += [f"  --inset-shadow-facet: var({PREFIX}-shadow-facet-edge);", ""]
tw += [f"  --ease-{k}: var({var('easing.' + k)});" for k in T["easing"] if not k.startswith("$")]
tw += [f"  --breakpoint-{k}: {T['breakpoint'][k]['$value']};" for k in T["breakpoint"] if not k.startswith("$")]
tw += ["}", "",
       "/* The two type widths of the system: display text is set Expanded, section headings Semi-expanded. */",
       "@utility font-display { font-stretch: var(--aap-font-stretch-expanded); }",
       "@utility font-heading { font-stretch: var(--aap-font-stretch-semi-expanded); }", ""]
(HERE / "tailwind-theme.css").write_text("\n".join(tw), encoding="utf-8")

manifest = {"area": "tokens", "retrieved": "2026-11-02", "files": [
    {"path": "tokens/tokens.json", "format": "W3C DTCG JSON", "description": "Source of truth: colour, gradient, font, typography, space, size, radius, border, shadow, opacity, zIndex, duration, easing, breakpoint.", "derived": False},
    {"path": "tokens/tokens.css", "format": "CSS custom properties", "description": f"{len(lines)} --aap-* properties on :root plus @font-face for Mona Sans and Mona Sans Mono.", "generated_from": "tokens/tokens.json"},
    {"path": "tokens/tailwind-theme.css", "format": "Tailwind CSS v4 @theme", "description": "Brand-only colour utilities, type roles, radii, shadows, easings and breakpoints mapped onto tokens.css.", "generated_from": "tokens/tokens.json"},
    {"path": "tokens/build-tokens.py", "format": "Python 3", "description": "The compiler that writes the three generated files."}]}
(HERE / "tokens-manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
print(f"tokens.css: {len(lines)} properties; tailwind-theme.css: {sum(1 for l in tw if l.strip().startswith('--'))} theme variables")
