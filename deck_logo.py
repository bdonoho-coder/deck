r"""Draws the Deck app logo (our Files fork) into every tile asset of the package.

The mark: a dark plate with a cut top-right corner and an amber outline, three
stacked "deck" bars inside, and a lit node bottom-left. Every PNG under
files-src/src/Files.App/Assets/AppTiles/Dev is redrawn at its own size, plus
Logo.ico. BadgeLogo files are white-on-transparent (Windows requirement).

  py deck_logo.py            redraw all assets
  py deck_logo.py --preview  also write release\deck-logo-preview.png
"""
import io
import struct
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).parent
ASSETS = ROOT / "files-src" / "src" / "Files.App" / "Assets" / "AppTiles" / "Dev"
FONT = "C:/Windows/Fonts/bahnschrift.ttf"
AMBER = (255, 160, 40)
PLATE = (18, 22, 27)
SS = 4  # supersampling


def mark(size, fill=1.0, white=False):
    """The Deck mark on a transparent square. fill = how much of the square it covers."""
    N = size * SS
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = (1 - fill) / 2
    u = lambda f: pad * N + f * fill * N  # 0..1 inside the mark box
    w = max(SS, round(fill * N * 0.045))  # outline width
    col = (255, 255, 255) if white else AMBER
    if not white:
        # Plate with the top-right corner cut, glow behind the outline.
        cut = 0.2
        poly = [(u(0.06), u(0.06)), (u(0.94 - cut), u(0.06)), (u(0.94), u(0.06 + cut)),
                (u(0.94), u(0.94)), (u(0.06), u(0.94))]
        if size >= 44:
            g = Image.new("RGBA", (N, N), (0, 0, 0, 0))
            ImageDraw.Draw(g).polygon(poly, outline=AMBER + (140,), width=w * 3)
            img = Image.alpha_composite(g.filter(ImageFilter.GaussianBlur(w * 1.5)), img)
            d = ImageDraw.Draw(img)
        d.polygon(poly, fill=PLATE + (242,), outline=AMBER + (255,), width=w)
        # Corner tick inside the cut, like the HUD brackets.
        d.line([(u(0.94 - cut), u(0.06)), (u(0.94 - cut), u(0.06 + cut)), (u(0.94), u(0.06 + cut))],
               fill=AMBER + (255,), width=w)
    # Three stacked deck bars, each one shifted right and dimmer than the one above.
    bar_h = 0.085
    for i, (y, alpha) in enumerate(((0.30, 255), (0.455, 170), (0.61, 100))):
        x0, x1 = 0.24 + i * 0.05, 0.70 + i * 0.05
        c = 0.045
        d.polygon([(u(x0), u(y)), (u(x1 - c), u(y)), (u(x1), u(y + c)), (u(x1), u(y + bar_h)), (u(x0), u(y + bar_h))],
                  fill=col + (alpha,))
    # Lit node, bottom left, with a short lead line.
    s = 0.05
    d.rectangle([u(0.20), u(0.78 - s), u(0.20 + 2 * s), u(0.78 + s)], fill=col + (255,))
    d.line([(u(0.34), u(0.78)), (u(0.62), u(0.78))], fill=col + (140 if not white else 255,), width=max(SS, w // 2))
    return img.resize((size, size), Image.LANCZOS)


def tile(w, h, mark_frac, text=None):
    """Transparent tile with the mark centered (and an optional wordmark on the right)."""
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    m = round(min(w, h) * mark_frac)
    mk = mark(m)
    if text:
        font = ImageFont.truetype(FONT, round(h * 0.26))
        tw = font.getlength(text)
        gap = round(m * 0.18)
        x = (w - m - gap - tw) // 2
        img.paste(mk, (int(x), (h - m) // 2), mk)
        ImageDraw.Draw(img).text((x + m + gap, h / 2), text, font=font, fill=AMBER + (255,), anchor="lm")
    else:
        img.paste(mk, ((w - m) // 2, (h - m) // 2), mk)
    return img


def draw_asset(name, w, h):
    if name.startswith("BadgeLogo"):
        return mark(w, 0.9, white=True)
    if name.startswith("Square44x44Logo"):
        # targetsize icons (taskbar, title bar, Explorer) fill the canvas; scale ones get padding.
        return tile(w, h, 1.0 if "targetsize" in name else 0.75)
    if name.startswith("StoreLogo"):
        return tile(w, h, 0.9)
    if name.startswith("SplashScreen") or name.startswith("Wide310x150Logo"):
        return tile(w, h, 0.5, "DECK")
    return tile(w, h, 0.55)  # Square150, Small71, Large310


def write_ico(path):
    pngs = []
    for s in (16, 20, 24, 30, 32, 36, 40, 48, 60, 64, 72, 80, 96, 256):
        b = io.BytesIO()
        mark(s).save(b, "PNG")
        pngs.append((s, b.getvalue()))
    out = io.BytesIO()
    out.write(struct.pack("<HHH", 0, 1, len(pngs)))
    offset = 6 + 16 * len(pngs)
    for s, data in pngs:
        out.write(struct.pack("<BBBBHHII", s % 256, s % 256, 0, 0, 1, 32, len(data), offset))
        offset += len(data)
    for _, data in pngs:
        out.write(data)
    path.write_bytes(out.getvalue())


def main():
    n = 0
    for png in sorted(ASSETS.glob("*.png")):
        w, h = Image.open(png).size
        draw_asset(png.name, w, h).save(png)
        n += 1
    write_ico(ASSETS / "Logo.ico")
    print("redrew", n, "png + Logo.ico")
    if "--preview" in sys.argv:
        rows = [("Square150x150Logo.scale-200.png", "Square44x44Logo.targetsize-48_altform-unplated.png",
                 "Square44x44Logo.targetsize-16.png", "BadgeLogo.scale-200.png", "StoreLogo.scale-200.png"),
                ("Wide310x150Logo.scale-100.png",)]
        sheet = Image.new("RGB", (1000, 520), (40, 44, 52))
        x = 10
        for name in rows[0]:
            im = Image.open(ASSETS / name)
            sheet.paste(im, (x, 10), im)
            x += im.width + 20
        im = Image.open(ASSETS / rows[1][0])
        sheet.paste(im, (10, 330), im)
        # Light background sample, as on a light taskbar.
        light = Image.new("RGB", (120, 120), (240, 241, 245))
        im = Image.open(ASSETS / "Square44x44Logo.targetsize-96_altform-lightunplated_theme-light.png")
        light.paste(im, (12, 12), im)
        sheet.paste(light, (400, 330))
        (ROOT / "release").mkdir(exist_ok=True)
        sheet.save(ROOT / "release" / "deck-logo-preview.png")
        print("preview", ROOT / "release" / "deck-logo-preview.png")


if __name__ == "__main__":
    main()
