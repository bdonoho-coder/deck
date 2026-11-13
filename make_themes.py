"""Builds the theme picker assets from Omarchy's themes.

Source: omarchy-dl/<id>/colors.toml and wallpapers, downloaded from
github.com/basecamp/omarchy (MIT), branch quattro, folder themes/<id>.

Run once (or again after adding a theme):
  - writes wallpapers/<id>/*.jpg (Omarchy's wallpapers, plus one soft-glow wallpaper)
  - writes themes.ini (read by ThemePicker.ahk)
  - adds the color schemes to Windows Terminal settings.json
"""
import json
import os
import random
import tomllib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from cyber_wallpaper import cyber_wallpaper
from hud_wallpaper import hud_wallpaper
from theme_wallpaper import theme_wallpapers

ROOT = Path(__file__).parent
SRC = ROOT / "omarchy-dl"
WT_SETTINGS = Path(os.environ["LOCALAPPDATA"]) / "Packages" / \
    "Microsoft.WindowsTerminal_8wekyb3d8bbwe" / "LocalState" / "settings.json"

# Theme id (Omarchy folder name) -> name shown in the picker.
THEMES = {
    "tokyo-night": "Tokyo Night",
    "catppuccin": "Catppuccin Mocha",
    "gruvbox": "Gruvbox",
    "nord": "Nord",
    "everforest": "Everforest",
    "catppuccin-latte": "Catppuccin Latte",
    "amber-lab": "Amber Lab",
    "hud-red": "HUD Red Alert",
    "hud-orange": "HUD Orange Ops",
    "hud-amber": "HUD Amber Control",
    "hud-cyan": "HUD Cyan Panel",
    "hud-neongrid": "HUD Neon Grid",
    "hud-synth": "HUD Neon Synth",
    "hud-pulse": "HUD Neon Pulse",
    "hud-irondeck": "HUD Iron Deck",
    "hud-acid": "HUD Acid Signal",
}

# Windows Terminal color -> Omarchy colors.toml key.
ANSI = {
    "black": "lighter_background", "red": "red", "green": "green", "yellow": "yellow",
    "blue": "blue", "purple": "magenta", "cyan": "cyan", "white": "foreground",
    "brightBlack": "muted", "brightRed": "bright_red", "brightGreen": "bright_green",
    "brightYellow": "bright_yellow", "brightBlue": "bright_blue",
    "brightPurple": "bright_magenta", "brightCyan": "bright_cyan",
    "brightWhite": "bright_foreground",
}


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def accent_palette(colors):
    """8 shades, light to dark, as Windows stores them (R G B 00). Index 3 is the accent.

    Slot 6 (SystemAccentColorDark3) holds the theme background, so the Windhawk
    taskbar and Explorer styles can use the exact theme color via ThemeResource.
    """
    c = rgb(colors["accent"])
    white, black = (255, 255, 255), (0, 0, 0)
    shades = [mix(c, white, 0.6), mix(c, white, 0.4), mix(c, white, 0.2), c,
              mix(c, black, 0.2), mix(c, black, 0.4), rgb(colors["background"]),
              rgb(colors["dark_background"])]
    return "".join("%02X%02X%02X00" % s for s in shades), shades


def glow_wallpaper(tid, colors, path, size=(2560, 1600)):
    """Soft glowing color blobs on the theme background."""
    random.seed(tid)
    small = (size[0] // 4, size[1] // 4)
    img = Image.new("RGB", small, rgb(colors["background"]))
    layer = Image.new("RGBA", small, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    alpha = 70 if colors["mode"] == "dark" else 90
    spots = [(0.78, 0.25, 0.42), (0.18, 0.85, 0.38), (0.55, 0.70, 0.22)]
    for key, (x, y, r) in zip(["accent", "magenta", "cyan"], spots):
        cx, cy, rad = x * small[0], y * small[1], r * small[0]
        d.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=rgb(colors[key]) + (alpha,))
    layer = layer.filter(ImageFilter.GaussianBlur(small[0] // 9))
    img.paste(layer, (0, 0), layer)
    img = img.resize(size, Image.BICUBIC)
    # Light grain stops color banding in the gradients.
    noise = Image.effect_noise(size, 6).convert("RGB")
    Image.blend(img, noise, 0.03).save(path, quality=92)


def build_wallpapers(tid, colors):
    """Converts Omarchy's wallpapers to JPG (Windows can't show WebP), max 3840 wide."""
    out = ROOT / "wallpapers" / tid
    out.mkdir(parents=True, exist_ok=True)
    for old in out.glob("*.jpg"):
        old.unlink()
    sources = sorted(p for p in (SRC / tid).iterdir() if p.suffix.lower() in (".jpg", ".webp", ".png"))
    for src in sources:
        im = Image.open(src).convert("RGB")
        if im.width > 3840:
            im = im.resize((3840, round(im.height * 3840 / im.width)), Image.LANCZOS)
        im.save(out / (src.stem + ".jpg"), quality=92)
    if tid.startswith("hud-"):
        hud_wallpaper(tid, colors, out / "1-hud.jpg", "frame")
        hud_wallpaper(tid, colors, out / "2-hud-minimal.jpg", "minimal")
        if tid == "hud-acid":
            cyber_wallpaper(tid, colors, out / "3-hud-cyber.jpg")
    else:
        glow_wallpaper(tid, colors, out / "9-glow.jpg")
        theme_wallpapers(tid, colors, out)
    return out


def main():
    ini = []
    schemes = []
    for tid, name in THEMES.items():
        colors = tomllib.loads((SRC / tid / "colors.toml").read_text(encoding="utf-8"))
        wp_dir = build_wallpapers(tid, colors)
        pal_hex, shades = accent_palette(colors)
        swatches = [colors[k].lstrip("#") for k in ("red", "yellow", "green", "cyan", "blue", "magenta")]
        ini += [f"[{tid}]", f"name={name}", f"mode={colors['mode']}",
                f"accent={colors['accent'].lstrip('#')}", f"menu={colors['lighter_background'].lstrip('#')}",
                f"palette={pal_hex}",
                f"bg={colors['background'].lstrip('#')}", f"fg={colors['foreground'].lstrip('#')}",
                f"bg_dark={colors['dark_background'].lstrip('#')}",
                f"bg_light={colors['lighter_background'].lstrip('#')}",
                f"selection={colors['selection'].lstrip('#')}",
                f"swatches={','.join(swatches)}",
                f"terminal={name}", f"wallpapers={wp_dir}", ""]
        scheme = {"name": name, "background": colors["background"],
                  "foreground": colors["foreground"], "cursorColor": colors["accent"],
                  "selectionBackground": colors["selection"]}
        scheme.update({k: colors[v] for k, v in ANSI.items()})
        schemes.append(scheme)
    (ROOT / "themes.ini").write_text("\n".join(ini), encoding="utf-16")

    settings = json.loads(WT_SETTINGS.read_text(encoding="utf-8"))
    names = {s["name"] for s in schemes}
    settings["schemes"] = [s for s in settings.get("schemes", []) if s["name"] not in names] + schemes
    settings["profiles"]["defaults"].setdefault("colorScheme", "Campbell")
    WT_SETTINGS.write_text(json.dumps(settings, indent=4), encoding="utf-8")
    print("built", len(THEMES), "themes")


if __name__ == "__main__":
    main()
