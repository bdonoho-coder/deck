"""HUD background art for File Explorer's top area (Windhawk File Explorer Styler).

Only Explorer's top area is XAML (tabs, address bar, command bar); the file list
is not, so the art lives there. Per HUD theme:
  explorer-art/<id>/cmdbar.png  command bar: theme color, dot grid, tick scale, code labels
  explorer-art/<id>/tabrow.png  right end of the tab row: code readout and scale bars
Other themes get an empty set. The picker copies the theme's set to explorer-art/active,
which windhawk_styles.py points the styles at.

  py make_explorer_art.py
"""
import random
import tomllib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent
OUT = ROOT / "explorer-art"
FONT = "C:/Windows/Fonts/bahnschrift.ttf"
HUD = ["hud-red", "hud-orange", "hud-amber", "hud-cyan",
       "hud-neongrid", "hud-synth", "hud-pulse", "hud-irondeck", "hud-acid"]
CMD_W, CMD_H = 3840, 48   # wider than any window; shown left-aligned, unscaled
TAB_W, TAB_H = 900, 40    # shown right-aligned; the right 170 px stay clear of the caption buttons


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def cmdbar(tid, c):
    random.seed(tid + "cmd")
    acc, bg, fg = rgb(c["accent"]), rgb(c["background"]), rgb(c["foreground"])
    glyph = rgb(c.get("hud_glyph", c["accent"]))
    base = mix(bg, rgb(c["lighter_background"]), 0.6)
    img = Image.new("RGBA", (CMD_W, CMD_H), base + (255,))
    d = ImageDraw.Draw(img)
    dim = mix(base, fg, 0.12)
    for x in range(8, CMD_W, 16):          # dot grid
        for y in range(8, CMD_H - 10, 12):
            d.point((x, y), fill=dim)
    y = CMD_H - 1                           # tick scale on the bottom edge
    d.line([(0, y), (CMD_W, y)], fill=mix(base, acc, 0.45))
    for i, x in enumerate(range(0, CMD_W, 20)):
        d.line([(x, y - (6 if i % 5 == 0 else 3)), (x, y)], fill=mix(base, acc, 0.55))
    for _ in range(14):                     # a few bright segments
        x = random.randrange(300, CMD_W - 200, 20)
        d.line([(x, y - 1), (x + random.choice((40, 60, 100)), y - 1)], fill=acc, width=2)
    tiny = ImageFont.truetype(FONT, 9)
    for x in range(560, CMD_W, 480):        # faint code labels in the gaps between buttons
        d.text((x, 4), "SEC-%02d" % (x // 480), font=tiny, fill=mix(base, glyph, 0.45))
    d.text((6, 3), "CMD.01", font=tiny, fill=mix(base, acc, 0.6))
    return img


def tabrow(tid, c, name):
    random.seed(tid + "tab")
    acc, fg = rgb(c["accent"]), rgb(c["foreground"])
    glyph = rgb(c.get("hud_glyph", c["accent"]))
    img = Image.new("RGBA", (TAB_W, TAB_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    right = TAB_W - 170
    small = ImageFont.truetype(FONT, 11)
    label = f"SYS // FILES  ·  {name.upper()}  ·  NODE {random.randrange(10, 99)}"
    w = d.textlength(label, font=small)
    x0 = right - w
    d.rectangle([x0 - 14, 15, x0 - 8, 21], fill=acc + (255,))
    d.text((x0, 11), label, font=small, fill=glyph + (220,))
    x = x0 - 40                             # scale bars to the left of the readout
    for _ in range(5):
        seg = random.choice((30, 50, 80))
        d.line([(x - seg, 18), (x, 18)], fill=mix(fg, acc, 0.5) + (110,), width=2)
        x -= seg + 14
    d.line([(right - 60, 34), (right, 34)], fill=acc + (255,), width=3)
    d.line([(x, 34), (right - 66, 34)], fill=acc + (70,), width=1)
    return img


def plain(c):
    """Non-HUD themes: the command bar in its usual theme color, no art."""
    base = mix(rgb(c["background"]), rgb(c["lighter_background"]), 0.6)
    return Image.new("RGBA", (CMD_W, CMD_H), base + (255,))  # full size: the brush doesn't stretch


def main():
    names = {}
    ini = (ROOT / "themes.ini").read_text(encoding="utf-16")
    for block in ini.split("\n["):
        head, _, body = block.partition("]")
        for line in body.splitlines():
            if line.startswith("name="):
                names[head.strip("[")] = line[5:].replace("HUD ", "")
    blank = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
    for tid in names:
        c = tomllib.loads((ROOT / "omarchy-dl" / tid / "colors.toml").read_text(encoding="utf-8"))
        out = OUT / tid
        out.mkdir(parents=True, exist_ok=True)
        hud = tid in HUD
        (cmdbar(tid, c) if hud else plain(c)).save(out / "cmdbar.png")
        (tabrow(tid, c, names[tid]) if hud else blank).save(out / "tabrow.png")
        print("built", tid)
    empty = OUT / "none"                     # "Original": nothing drawn
    empty.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", (1, 1), (0, 0, 0, 0)).save(empty / "cmdbar.png")
    Image.new("RGBA", (1, 1), (0, 0, 0, 0)).save(empty / "tabrow.png")


if __name__ == "__main__":
    main()
