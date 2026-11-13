"""Plain dark HUD wallpapers for the hud-* themes (used by make_themes.py).

Draws a dim grid with + marks, scale bars and code labels along the edges,
and corner brackets, in the theme accent. The middle stays empty so windows
stand out. variant "frame" adds a small reticle and side tags; "minimal" is
grid and edges only.
"""
import random

from PIL import Image, ImageDraw, ImageFont

FONT = "C:/Windows/Fonts/bahnschrift.ttf"
TB = 90  # keep the bottom edge clear of the taskbar


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hud_wallpaper(tid, colors, path, variant="frame", size=(2560, 1600)):
    random.seed(tid + variant)
    W, H = size
    bg, acc = rgb(colors["background"]), rgb(colors["accent"])
    muted, fg = rgb(colors["muted"]), rgb(colors["foreground"])
    img = Image.new("RGB", size, bg)

    # Soft lighter middle, darker edges.
    glow = Image.new("L", (W // 8, H // 8), 0)
    gd = ImageDraw.Draw(glow)
    for i in range(40):
        t = i / 40
        gd.ellipse([W // 16 * t, H // 16 * t, W // 8 - W // 16 * t, H // 8 - H // 16 * t], fill=int(28 * t))
    glow = glow.resize(size, Image.BICUBIC)
    img.paste(Image.new("RGB", size, rgb(colors["lighter_background"])), (0, 0), glow)

    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    small = ImageFont.truetype(FONT, 15)
    tiny = ImageFont.truetype(FONT, 12)

    def a(c, alpha):
        return c + (alpha,)

    # Dim grid and + marks.
    step = 80
    for x in range(step, W, step):
        d.line([(x, 0), (x, H)], fill=a(muted, 14))
    for y in range(step, H, step):
        d.line([(0, y), (W, y)], fill=a(muted, 14))
    for x in range(step * 2, W - step, step * 4):
        for y in range(step * 2, H - step, step * 3):
            d.line([(x - 6, y), (x + 6, y)], fill=a(muted, 90))
            d.line([(x, y - 6), (x, y + 6)], fill=a(muted, 90))

    # Scale bars with labels along top and bottom.
    m = 46
    for row_y, up in ((m, True), (H - m - TB, False)):
        x, n = 140, 1
        while x < W - 220:
            seg = random.choice((90, 120, 150))
            hot = random.random() < 0.18
            col = a(acc, 230) if hot else a(muted, 150)
            d.line([(x, row_y), (x + seg, row_y)], fill=col, width=3 if hot else 2)
            d.line([(x, row_y - 5), (x, row_y + 5)], fill=a(muted, 120))
            label = "FN_%02d" % n
            ty = row_y - 22 if up else row_y + 8
            d.text((x, ty), label, font=tiny, fill=a(acc, 220) if hot else a(muted, 170))
            x += seg + 60
            n += 1

    # Thin side rails with a few accent tags.
    for rail_x in (m, W - m):
        d.line([(rail_x, 160), (rail_x, H - 160 - TB)], fill=a(muted, 90))
        for _ in range(3):
            y = random.randrange(240, H - 300)
            d.rectangle([rail_x - 3, y, rail_x + 3, y + random.choice((40, 70, 110))], fill=a(acc, 200))

    # Corner brackets.
    L, c = 70, 24
    for cx, cy, sx, sy in ((c, c, 1, 1), (W - c, c, -1, 1), (c, H - c - TB, 1, -1), (W - c, H - c - TB, -1, -1)):
        d.line([(cx, cy), (cx + L * sx, cy)], fill=a(acc, 230), width=3)
        d.line([(cx, cy), (cx, cy + L * sy)], fill=a(acc, 230), width=3)

    if variant == "frame":
        # Small reticle, top left, like a status gauge.
        rx, ry, r = 260, 230, 34
        d.ellipse([rx - r, ry - r, rx + r, ry + r], outline=a(muted, 160), width=2)
        d.arc([rx - r - 10, ry - r - 10, rx + r + 10, ry + r + 10], 200, 320, fill=a(acc, 230), width=3)
        d.ellipse([rx - 6, ry - 6, rx + 6, ry + 6], outline=a(acc, 230), width=2)
        d.text((rx + r + 24, ry - 18), "SERVER DATA OUTPUT [ 3-2 ]", font=small, fill=a(acc, 220))
        d.text((rx + r + 24, ry + 4), "CONNECTION STABLE", font=tiny, fill=a(muted, 200))
        # Timer label, bottom left.
        bx, by = 160, H - 170 - TB
        d.rectangle([bx, by, bx + 230, by + 52], outline=a(muted, 140))
        d.text((bx + 12, by + 6), "FUNCTION RUN", font=tiny, fill=a(muted, 200))
        d.text((bx + 12, by + 22), "00:11:32:016", font=small, fill=a(fg, 220))
        # Theme tag, right edge.
        d.rectangle([W - m - 46, H // 2 - 14, W - m - 6, H // 2 + 14], fill=a(acc, 230))
        d.text((W - m - 40, H // 2 - 9), "F_A", font=tiny, fill=a(bg, 255))

    img.paste(layer, (0, 0), layer)
    img.save(path, quality=94)
