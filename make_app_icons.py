"""Builds themed app icons: appicons/<theme>/<app>.ico for every theme.

Logos: Simple Icons (CC0), appicons/src/<slug>.svg. Apps without a logo get
their first letter. Each icon is a solid rounded square in a theme color with
the logo cut out in the theme background. Chrome (headless) draws
the SVGs; Pillow cuts the sheet into .ico files.

HUD themes instead get a dark HUD panel (outline, corner brackets) with the
logo glowing in the accent color. Line logos come from the LineX pack I bought
(linex-src, personal use on this PC only, never publish them); apps it lacks
get their Simple Icons logo, filled.

  py -P make_app_icons.py            build all themes
  py -P make_app_icons.py --preview  also write appicons/preview.png
"""
import re
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).parent
LINEX = ROOT / "linex-src" / "LineX IconPack 1.0"
# icon id -> LineX "<folder>/<name>" (lines on black); others use Simple Icons
LINEX_ICONS = {
    "chrome": "Google/Google Chrome", "spotify": "Apps/Spotify", "steam": "Apps/Steam",
    "telegram": "Apps/Telegram", "notion": "Apps/Notion", "zoom": "Apps/zoom",
    "itunes": "System/Music", "firefox": "Apps/Firefox", "epic": "Apps/Game Launch",
    "playnite": "Extra/Gamepad", "obsidian": "Extra/Diamond", "krita": "Extra/brush",
    "malwarebytes": "Extra/Shield", "nomachine": "System/Remote", "sumatrapdf": "Extra/Books",
    "windhawk": "Extra/Gear", "cheatengine": "Extra/Target", "wemod": "Extra/Rocket",
    "explorer": "System/Files",
}
# --release: no LineX logos (their license forbids publishing), output under release/appicons.
RELEASE = "--release" in sys.argv
OUT = ROOT / ("release/appicons" if RELEASE else "appicons")
SRC = ROOT / "appicons" / "src"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
THEMES = ["tokyo-night", "catppuccin", "gruvbox", "nord", "everforest", "catppuccin-latte", "amber-lab",
          "hud-red", "hud-orange", "hud-amber", "hud-cyan",
          "hud-neongrid", "hud-synth", "hud-pulse", "hud-irondeck", "hud-acid"]
CELL = 256

# icon id -> (Simple Icons slug or one letter, Omarchy color key)
APPS = {
    "chrome": ("googlechrome", "blue"), "spotify": ("spotify", "green"),
    "steam": ("steam", "blue"), "epic": ("epicgames", "foreground"),
    "ubisoft": ("ubisoft", "cyan"), "telegram": ("telegram", "cyan"),
    "notion": ("notion", "foreground"), "obsidian": ("obsidian", "magenta"),
    "zoom": ("zoom", "blue"), "obs": ("obsstudio", "foreground"),
    "blender": ("blender", "orange"), "krita": ("krita", "magenta"),
    "nvidia": ("nvidia", "green"), "itunes": ("itunes", "magenta"),
    "malwarebytes": ("malwarebytes", "blue"), "python": ("python", "yellow"),
    "firefox": ("firefoxbrowser", "orange"),
    "playnite": ("P", "accent"), "nomachine": ("N", "orange"),
    "sumatrapdf": ("S", "yellow"), "windhawk": ("W", "accent"),
    "cheatengine": ("C", "red"), "wemod": ("W", "red"),
    "explorer": ("E", "yellow"), "terminal": (">_", "green"),  # HUD pins (make_hud_pins.ps1)
}


def svg_path(slug):
    return re.search(r'<path d="([^"]+)"', (SRC / f"{slug}.svg").read_text()).group(1)


def cell_html(glyph, panel, color, rx):
    """Solid tile: filled with the theme color, logo in the theme background."""
    if len(glyph) <= 2:  # one or two characters drawn as text, longer = Simple Icons slug
        inner = (f'<text x="12" y="12" text-anchor="middle" dominant-baseline="central" '
                 f'font-family="Segoe UI" font-weight="700" font-size="15" fill="{color}">{glyph}</text>')
    else:
        inner = f'<path d="{svg_path(glyph)}" fill="{color}"/>'
    return (f'<div class="c"><svg viewBox="0 0 24 24" width="{CELL}" height="{CELL}">'
            f'<rect x="0.5" y="0.5" width="23" height="23" rx="{rx}" fill="{panel}"/>'
            f'<g transform="translate(5.2 5.2) scale(0.566)">{inner}</g></svg></div>')


def rgb(h):
    return tuple(int(h.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))


def linex_logo(app, color):
    """LineX logo as an RGBA layer, trimmed and scaled to the Simple Icons logo size.

    color=None: the pack's gradient colors ("LineX" set). Otherwise the white
    "LineX Dark" lines, painted in that color.
    """
    folder, name = LINEX_ICONS[app].split("/")
    sub = f"LineX Dark/LineX Dark {folder}" if color else f"LineX/LineX {folder}"
    src = Image.open(LINEX / sub / f"{name}.png").convert("RGB")
    src = src.resize((CELL, CELL), Image.LANCZOS).crop((22, 22, CELL - 22, CELL - 22))
    inner = int(CELL * 0.62)
    src = src.resize((inner, inner), Image.LANCZOS)
    if color:
        layer = tint(src.convert("L"), color)
    else:  # lines on black: brightest channel = coverage; divide it out so edges keep their hue
        a = np.asarray(src, dtype=np.float32)
        cover = a.max(axis=2, keepdims=True)
        rgb_ = np.clip(a * 255 / np.maximum(cover, 1), 0, 255)
        layer = Image.fromarray(np.concatenate([rgb_, cover], axis=2).astype(np.uint8), "RGBA")
    full = Image.new("RGBA", (CELL, CELL), (0, 0, 0, 0))
    full.paste(layer, ((CELL - inner) // 2,) * 2)
    return full


def tint(mask, color):
    """A one-color RGBA layer shaped by mask."""
    return Image.merge("RGBA", (*(Image.new("L", mask.size, c) for c in color), mask))


def hud_panel(logo, colors):
    """Dark panel, dim outline, accent corner brackets, logo layer with a soft glow."""
    accent, panel = rgb(colors["accent"]), rgb(colors["lighter_background"])
    im = Image.new("RGBA", (CELL, CELL), panel + (255,))
    glow = logo.filter(ImageFilter.GaussianBlur(6))
    glow.putalpha(glow.getchannel("A").point(lambda v: v * 0.6))
    im.alpha_composite(glow)
    im.alpha_composite(logo)
    d = ImageDraw.Draw(im)
    dim = tuple(int(a * 0.45 + p * 0.55) for a, p in zip(accent, panel))
    d.rectangle((3, 3, CELL - 4, CELL - 4), outline=dim, width=3)
    L, w = 46, 8
    for x, y, sx, sy in [(0, 0, 1, 1), (CELL - 1, 0, -1, 1), (0, CELL - 1, 1, -1), (CELL - 1, CELL - 1, -1, -1)]:
        d.line((x, y + sy * w // 2, x + sx * L, y + sy * w // 2), fill=accent, width=w)
        d.line((x + sx * w // 2, y, x + sx * w // 2, y + sy * L), fill=accent, width=w)
    return im


def render(theme, colors):
    hud = theme.startswith("hud-")
    rx = 1 if hud else 5.5  # HUD themes: sharp panel corners
    if hud:  # white logo on black: Chrome draws the masks for apps LineX lacks
        cells = "".join(cell_html(g, "#000000", "#ffffff", 0) for g, k in APPS.values())
    else:
        cells = "".join(cell_html(g, colors[k], colors["background"], rx) for g, k in APPS.values())
    html = ("<html><body style='margin:0;background:transparent'>"
            f"<style>.c{{width:{CELL}px;height:{CELL}px;float:left}}</style>{cells}</body></html>")
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "icons.html"
        page.write_text(html, encoding="utf-8")
        shot = Path(tmp) / "sheet.png"
        width = CELL * len(APPS)
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", f"--user-data-dir={tmp}\\p",
                        "--hide-scrollbars", "--default-background-color=00000000",
                        f"--window-size={width},{CELL}", f"--screenshot={shot}", page.as_uri()],
                       check=True, capture_output=True, timeout=120)
        sheet = Image.open(shot).convert("RGBA")
    # HUD themes: <theme> has logos in the accent, <theme>-color keeps LineX's gradients.
    sets = {theme: rgb(colors["accent"]), theme + "-color": None} if hud else {theme: None}
    result = {}
    for name, color in sets.items():
        out = OUT / name
        out.mkdir(parents=True, exist_ok=True)
        icons = []
        for i, (app, (_, key)) in enumerate(APPS.items()):
            im = sheet.crop((i * CELL, 0, (i + 1) * CELL, CELL))
            if hud:
                logo = linex_logo(app, color) if app in LINEX_ICONS and not RELEASE else \
                    tint(im.convert("L"), color or rgb(colors[key]))
                im = hud_panel(logo, colors)
            im.save(out / f"{app}.ico", sizes=[(s, s) for s in (16, 20, 24, 32, 40, 48, 64, 128, 256)])
            icons.append(im)
        result[name] = icons
    return result


def main():
    rows = []
    for theme in THEMES:
        colors = tomllib.loads((ROOT / "omarchy-dl" / theme / "colors.toml").read_text(encoding="utf-8"))
        for name, icons in render(theme, colors).items():
            rows.append((colors["background"], icons))
            print("built", name)
    if "--preview" in sys.argv:
        size, pad = 64, 8
        prev = Image.new("RGB", (len(APPS) * (size + pad) + pad, len(rows) * (size + 2 * pad)))
        for r, (bg, icons) in enumerate(rows):
            y = r * (size + 2 * pad)
            prev.paste(bg, (0, y, prev.width, y + size + 2 * pad))
            for i, im in enumerate(icons):
                small = im.resize((size, size), Image.LANCZOS)
                prev.paste(small, (pad + i * (size + pad), y + pad), small)
        prev.save(OUT / "preview.png")


if __name__ == "__main__":
    main()
