"""Retro cyberpunk wallpaper for HUD Acid Signal (used by make_themes.py as 3-hud-cyber.jpg).

Synthwave grid horizon and a striped sun in the theme accent and orange, CRT
scan lines, VHS glitch bands with a cyan / red channel split, a hazard stripe,
a barcode block, a katakana tag and VHS "REC / PLAY" labels. The upper middle
stays mostly empty so windows stand out.

    py cyber_wallpaper.py            # writes wallpapers/hud-acid/3-hud-cyber.jpg
"""
import math
import random
import tomllib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FONT = "C:/Windows/Fonts/bahnschrift.ttf"
JP_FONT = "C:/Windows/Fonts/YuGothB.ttc"
TB = 90  # keep the bottom edge clear of the taskbar


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def cyber_wallpaper(tid, colors, path, size=(2560, 1600)):
    random.seed(tid + "cyber")
    W, H = size
    bg, acc = rgb(colors["background"]), rgb(colors["accent"])
    orange, cyan, red = rgb(colors["orange"]), rgb(colors["cyan"]), rgb(colors["red"])
    muted, fg = rgb(colors["muted"]), rgb(colors["foreground"])
    img = Image.new("RGB", size, bg)
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    def a(c, alpha):
        return c + (alpha,)

    big = ImageFont.truetype(FONT, 54)
    mid = ImageFont.truetype(FONT, 22)
    small = ImageFont.truetype(FONT, 15)
    tiny = ImageFont.truetype(FONT, 12)
    jp = ImageFont.truetype(JP_FONT, 26)

    # Horizon glow: a dim orange band fading up from the horizon line.
    horizon = int(H * 0.64)
    for i in range(140):
        t = 1 - i / 140
        d.line([(0, horizon - i), (W, horizon - i)], fill=a(orange, int(26 * t * t)))

    # Striped sun, just right of centre, sitting on the horizon.
    sx, sy, r = int(W * 0.58), horizon, 300
    sun = Image.new("RGBA", size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(sun)
    for i in range(r, 0, -3):
        t = i / r
        col = tuple(round(o + (y - o) * (1 - t)) for o, y in zip(orange, acc))
        sd.ellipse([sx - i, sy - i, sx + i, sy + i], fill=a(col, 255))
    # Horizontal cuts that get thicker towards the horizon (the synthwave sun).
    gap, y = 4, sy
    while y > sy - r:
        sd.rectangle([sx - r, y - gap, sx + r, y], fill=(0, 0, 0, 0))
        y -= gap + 24
        gap += 3
    sd.rectangle([0, sy, W, H], fill=(0, 0, 0, 0))
    layer.alpha_composite(sun)

    # Perspective grid below the horizon.
    vx = W // 2
    for k in range(-16, 17):
        x_bottom = vx + k * 220
        alpha = 150 if k % 4 == 0 else 95
        d.line([(vx, horizon), (x_bottom, H)], fill=a(acc, alpha), width=2)
    rows, y = 14, horizon
    for i in range(1, rows + 1):
        t = i / rows
        y = horizon + int((H - horizon) * t * t)
        d.line([(0, y), (W, y)], fill=a(acc, 60 + int(120 * t)), width=2)
    d.line([(0, horizon), (W, horizon)], fill=a(acc, 230), width=3)

    # Title block, top left: theme name, katakana tag, hazard stripe.
    tx, ty = 120, 110
    d.text((tx, ty), "ACID // SIGNAL", font=big, fill=a(acc, 240))
    d.text((tx + 2, ty + 2), "ACID // SIGNAL", font=big, fill=a(cyan, 90))
    d.text((tx, ty + 70), "アシッド・シグナル  //  RETRO LINK 1984", font=jp, fill=a(fg, 170))
    hz_y = ty + 118
    hazard = Image.new("RGBA", (560, 14), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hazard)
    for x in range(-20, 580, 28):
        hd.polygon([(x, 14), (x + 14, 0), (x + 28, 0), (x + 14, 14)], fill=a(acc, 230))
    layer.alpha_composite(hazard, (tx, hz_y))
    d.text((tx, hz_y + 22), "SYS 0x0B0B  ·  CHANNEL 03  ·  SIGNAL LOCKED", font=small, fill=a(muted, 220))

    # VHS corner labels.
    d.ellipse([W - 330, 118, W - 312, 136], fill=a(red, 240))
    d.text((W - 300, 110), "REC", font=mid, fill=a(fg, 230))
    d.text((W - 300, 140), "SP  00:11:32:016", font=small, fill=a(muted, 220))
    # Bahnschrift has no media glyphs: draw the play triangle and tracking bars by hand.
    py = H - TB - 150
    d.polygon([(122, py + 4), (122, py + 24), (140, py + 14)], fill=a(fg, 230))
    d.text((150, py), "PLAY", font=mid, fill=a(fg, 230))
    d.text((120, py + 32), "TRACKING", font=small, fill=a(muted, 220))
    for i in range(7):
        d.rectangle([205 + i * 12, py + 36, 212 + i * 12, py + 46], fill=a(acc if i < 5 else muted, 220))

    # Barcode block, bottom right.
    bx, by, x = W - 420, H - TB - 150, W - 420
    while x < W - 120:
        w = random.choice((3, 3, 5, 8))
        d.rectangle([x, by, x + w, by + 56], fill=a(acc, 230))
        x += w + random.choice((3, 5, 7))
    d.text((bx, by + 64), "ID 2026-1112-ACID  ·  NIGHT CITY SECTOR 7", font=tiny, fill=a(muted, 220))

    # Corner brackets.
    L, c = 70, 24
    for cx, cy, sxn, syn in ((c, c, 1, 1), (W - c, c, -1, 1), (c, H - c - TB, 1, -1), (W - c, H - c - TB, -1, -1)):
        d.line([(cx, cy), (cx + L * sxn, cy)], fill=a(acc, 230), width=3)
        d.line([(cx, cy), (cx, cy + L * syn)], fill=a(acc, 230), width=3)

    img.paste(layer, (0, 0), layer)

    # VHS glitch bands: slices shifted sideways with a cyan / red split.
    for _ in range(9):
        y = random.randrange(300, H - TB - 40)  # below the title block, which stays readable
        h = random.choice((6, 10, 16, 28))
        shift = random.choice((-38, -22, -12, 12, 22, 38))
        band = img.crop((0, y, W, y + h))
        img.paste(band, (shift, y))
        for tint, dx in ((cyan, -7), (red, 7)):
            ghost = Image.new("RGB", band.size, tint)
            mask = band.convert("L").point(lambda v: min(255, v * 2)).point(lambda v: v // 3)
            img.paste(ghost, (shift + dx, y), mask)

    # CRT scan lines over everything.
    scan = Image.new("RGBA", size, (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(scan)
    for y in range(0, H, 4):
        sdraw.line([(0, y), (W, y)], fill=(0, 0, 0, 46))
    img.paste(scan, (0, 0), scan)
    img.save(path, quality=94)


if __name__ == "__main__":
    colors = tomllib.loads((ROOT / "omarchy-dl" / "hud-acid" / "colors.toml").read_text(encoding="utf-8"))
    out = ROOT / "wallpapers" / "hud-acid" / "3-hud-cyber.jpg"
    cyber_wallpaper("hud-acid", colors, out)
    print(out)
