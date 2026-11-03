"""Write the UI and social icons (24 px grid; UI icons are 1.75 strokes with round caps, social glyphs are solid), the
currentColor sprite and icons.json. Run: python design-system/icons/build-icons.py"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
UI = {  # name: (svg body, description)
    "arrow-right": ('<path d="M5 12h14M13 6l6 6-6 6"/>', "Forward action, next step."),
    "arrow-left": ('<path d="M19 12H5M11 6l-6 6 6 6"/>', "Back."),
    "arrow-up-right": ('<path d="M7 17 17 7M8 7h9v9"/>', "Opens elsewhere in the site."),
    "chevron-down": ('<path d="m6 9 6 6 6-6"/>', "Disclosure, select."),
    "chevron-right": ('<path d="m9 6 6 6-6 6"/>', "Breadcrumb, list row."),
    "plus": ('<path d="M12 5v14M5 12h14"/>', "Add, expand."),
    "minus": ('<path d="M5 12h14"/>', "Remove, collapse."),
    "close": ('<path d="m6 6 12 12M18 6 6 18"/>', "Close, dismiss."),
    "menu": ('<path d="M4 7h16M4 12h16M4 17h16"/>', "Navigation menu."),
    "check": ('<path d="m5 12.5 4.5 4.5L19 7.5"/>', "Done, included."),
    "download": ('<path d="M12 4v11M7 10l5 5 5-5M5 20h14"/>', "Download a file."),
    "copy": ('<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M15 9V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v7a2 2 0 0 0 2 2h3"/>', "Copy a value."),
    "external-link": ('<path d="M14 4h6v6M20 4l-9 9M18 14v4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4"/>', "Opens another site."),
    "search": ('<circle cx="11" cy="11" r="6.5"/><path d="m20 20-4.3-4.3"/>', "Search."),
    "mail": ('<rect x="3" y="5.5" width="18" height="13" rx="2"/><path d="m3.5 7 8.5 6 8.5-6"/>', "Email."),
    "phone": ('<rect x="7" y="3" width="10" height="18" rx="2.5"/><path d="M11 17.5h2"/>', "Phone or mobile."),
    "calendar": ('<rect x="4" y="5.5" width="16" height="15" rx="2"/><path d="M4 10h16M8 3.5v4M16 3.5v4"/>', "Dates, booking."),
    "clock": ('<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>', "Times, working hours."),
    "globe": ('<circle cx="12" cy="12" r="8.5"/><path d="M3.5 12h17M12 3.5c2.5 2.6 3.7 5.4 3.7 8.5s-1.2 5.9-3.7 8.5c-2.5-2.6-3.7-5.4-3.7-8.5s1.2-5.9 3.7-8.5z"/>', "Website, regions."),
    "map-pin": ('<path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.4"/>', "Location."),
    "info": ('<circle cx="12" cy="12" r="8.5"/><path d="M12 11v5M12 7.75v.5"/>', "Information message."),
    "alert-triangle": ('<path d="M12 4.5 2.8 19.5h18.4L12 4.5z"/><path d="M12 10v4M12 16.75v.5"/>', "Warning message."),
    "check-circle": ('<circle cx="12" cy="12" r="8.5"/><path d="m8.5 12.2 2.4 2.4 4.6-4.8"/>', "Success message."),
    "x-circle": ('<circle cx="12" cy="12" r="8.5"/><path d="m9.5 9.5 5 5M14.5 9.5l-5 5"/>', "Error message."),
    "lock": ('<rect x="5" y="10.5" width="14" height="10" rx="2"/><path d="M8 10.5V8a4 4 0 0 1 8 0v2.5"/>', "Privacy, data stays with the partner."),
    "file": ('<path d="M14 3.5H7a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8.5l-5-5z"/><path d="M14 3.5v5h5"/>', "Document, quote, invoice."),
    "link": ('<path d="M10 14a4.2 4.2 0 0 0 6 0l3-3a4.2 4.2 0 0 0-6-6l-1 1M14 10a4.2 4.2 0 0 0-6 0l-3 3a4.2 4.2 0 0 0 6 6l1-1"/>', "Link, connected tools."),
    "play": ('<path d="M8 5.5v13l10.5-6.5L8 5.5z"/>', "Play a video."),
}
SOCIAL = {  # simplified glyphs for email and page footers; use each platform's official asset where exact marks are required
    "linkedin": ('<rect x="4.4" y="9.4" width="3.3" height="10.1" rx=".4"/><circle cx="6.05" cy="6.15" r="1.9"/><path d="M10 9.4h3.1V11c.6-1.1 1.9-1.9 3.6-1.9 3 0 3.9 2 3.9 4.8v5.6h-3.3v-5c0-1.4-.3-2.6-1.8-2.6-1.6 0-2.2 1.2-2.2 2.7v4.9H10z"/>', "LinkedIn"),
    "x": ('<path d="M3.6 3.5h5.1l11.7 17h-5.1z"/><path d="M19.4 3.5 13.6 10M10.4 13.8 4.6 20.5" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/>', "X"),
    "facebook": ('<path d="M13.6 21v-7.6h2.6l.4-3h-3V8.6c0-.9.3-1.5 1.5-1.5h1.6V4.4a21 21 0 0 0-2.3-.1c-2.3 0-3.9 1.4-3.9 4v2.1H7.9v3h2.6V21z"/>', "Facebook"),
    "instagram": ('<rect x="3.75" y="3.75" width="16.5" height="16.5" rx="5" fill="none" stroke="currentColor" stroke-width="1.9"/><circle cx="12" cy="12" r="3.9" fill="none" stroke="currentColor" stroke-width="1.9"/><circle cx="17.2" cy="6.8" r="1.2"/>', "Instagram"),
    "youtube": ('<path fill-rule="evenodd" d="M21.6 7.2a2.6 2.6 0 0 0-1.8-1.8C18.2 5 12 5 12 5s-6.2 0-7.8.4a2.6 2.6 0 0 0-1.8 1.8A27 27 0 0 0 2 12a27 27 0 0 0 .4 4.8 2.6 2.6 0 0 0 1.8 1.8c1.6.4 7.8.4 7.8.4s6.2 0 7.8-.4a2.6 2.6 0 0 0 1.8-1.8A27 27 0 0 0 22 12a27 27 0 0 0-.4-4.8zM10 15V9l5.2 3z"/>', "YouTube"),
}
STROKE = 'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round"'
files, symbols = [], []
for folder, icons, attrs in (("ui", UI, STROKE), ("social", SOCIAL, 'fill="currentColor"')):
    (HERE / folder).mkdir(exist_ok=True)
    for name, (body, desc) in icons.items():
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" {attrs} aria-hidden="true">{body}</svg>\n'
        (HERE / folder / f"{name}.svg").write_text(svg, encoding="utf-8")
        symbols.append(f'  <symbol id="icon-{name}" viewBox="0 0 24 24" {attrs}>{body}</symbol>')
        files.append({"path": f"icons/{folder}/{name}.svg", "category": folder, "name": name, "sprite_id": f"icon-{name}",
                      "description": desc if folder == "ui" else f"{desc} glyph, simplified; solid, inherits currentColor.",
                      "style": "24 px grid, 1.75 stroke, round caps and joins" if folder == "ui" else "24 px grid, solid",
                      "derived": True})
(HERE / "sprite.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" style="display:none">\n' + "\n".join(symbols) + "\n</svg>\n", encoding="utf-8")
brand = json.loads((HERE / "brand/brand-icons.json").read_text(encoding="utf-8"))["files"]
(HERE / "icons.json").write_text(json.dumps({"area": "icons", "retrieved": "2026-11-02",
    "rights": "UI and social icons authored for Alliance AI Partners (derived: true). Social glyphs are simplified versions of third-party marks for footers; use each platform's official asset where exact marks are required. Service icons in brand/ come from the logo kit.",
    "files": files + brand}, indent=1) + "\n", encoding="utf-8")
print(f"{len(UI)} ui + {len(SOCIAL)} social icons, sprite with {len(symbols)} symbols, {len(brand)} brand icon files listed")
