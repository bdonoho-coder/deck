"""Builds HUD folder icon packs for the hud-* themes.

Each folder is a dark panel with a thin accent outline and an accent tab with
an angled cut on top (like the user's HUD reference pictures). Special folders
(Desktop, Downloads, ...) get a small line symbol.

Writes icons/<theme>/HUD Folders/Windhawk Resources/imageres.dll: a small DLL
holding only the HUD folder icon groups, plus theme.ini
for the Windhawk Resource Redirect mod (the picker points the mod at it).

  py make_folder_icons.py                 build every theme (omarchy-dl/*/colors.toml)
  py make_folder_icons.py nord gruvbox    build only these themes
  py make_folder_icons.py --preview       also write icons/hud-preview.png
"""
import io
import math
import subprocess
import struct
import sys
import tomllib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

import ico_res

ROOT = Path(__file__).parent
# The pack DLL holds only the folder icons. The Resource Redirect mod falls back
# to the real imageres.dll for every icon missing here, so only folders change.
PROJECT = ROOT / "iconpack" / "IconPack.csproj"
# Every theme with a palette gets a pack in its own colors (the 7 non-HUD themes too,
# so no downloaded niivu/Papirus pack is needed for a release).
THEMES = sorted(p.parent.name for p in (ROOT / "omarchy-dl").glob("*/colors.toml"))
SIZES = [16, 20, 24, 32, 40, 48, 64, 96, 128, 256]
SS = 4  # supersampling

# imageres.dll icon group -> symbol drawn on the folder ("" = plain folder).
GROUPS = {
    3: "", 4: "", 5: "", 6: "", 162: "", 1023: "", 143: "", 175: "", 190: "", 198: "",
    183: "desktop", 184: "download", 112: "doc", 1001: "doc", 1014: "doc",
    113: "picture", 108: "music", 189: "video", 115: "star", 1020: "star",
    186: "game", 185: "link", 18: "search", 1025: "search",
    123: "person", 181: "person", 178: "person", 166: "check",
    5325: "search",  # the File Explorer app icon (taskbar, Start)
}


# Other imageres groups -> (shape, symbol): drives, This PC, Recycle Bin, file types.
OTHER = {
    28: ("drive", ""), 29: ("drive", ""), 30: ("drive", ""), 32: ("drive", ""), 33: ("drive", "link"),
    35: ("drive", ""), 36: ("drive", "win"), 31: ("drive", "x"),
    109: ("pc", ""), 25: ("pc", "link"),
    55: ("bin", ""), 54: ("bin", "full"),
    2: ("file", ""), 102: ("file", "doc"), 15: ("file", "app"), 67: ("file", "gear"), 69: ("file", "gear"),
    174: ("file", "zip"), 22: ("file", "music"), 23: ("file", "video"),
    21: ("file", "picture"), 70: ("file", "picture"), 71: ("file", "picture"), 72: ("file", "picture"),
}


# File types whose icons come from apps, not imageres: icons/<theme>/files/<kind>.ico,
# set per user by file_icons.py when the picker applies a HUD theme.
FILE_KINDS = {"text": "doc", "config": "gear", "image": "picture", "media": "video", "zip": "zip"}


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def draw_symbol(d, kind, cx, cy, s, w, col):
    """Line symbol centered at cx, cy; s = half size, w = line width."""
    L = lambda pts: d.line(pts, fill=col, width=w, joint="curve")
    if kind == "desktop":
        d.rectangle([cx - s, cy - s * 0.75, cx + s, cy + s * 0.4], outline=col, width=w)
        L([(cx, cy + s * 0.4), (cx, cy + s * 0.8)])
        L([(cx - s * 0.5, cy + s * 0.85), (cx + s * 0.5, cy + s * 0.85)])
    elif kind == "download":
        L([(cx, cy - s), (cx, cy + s * 0.45)])
        L([(cx - s * 0.55, cy - s * 0.05), (cx, cy + s * 0.5), (cx + s * 0.55, cy - s * 0.05)])
        L([(cx - s, cy + s * 0.9), (cx + s, cy + s * 0.9)])
    elif kind == "doc":
        for i, f in enumerate((1, 1, 0.6)):
            y = cy - s * 0.6 + i * s * 0.6
            L([(cx - s, y), (cx - s + 2 * s * f, y)])
    elif kind == "picture":
        L([(cx - s, cy + s * 0.7), (cx - s * 0.3, cy - s * 0.2), (cx + s * 0.15, cy + s * 0.3),
           (cx + s * 0.45, cy), (cx + s, cy + s * 0.7), (cx - s, cy + s * 0.7)])
        r = s * 0.22
        d.ellipse([cx + s * 0.4 - r, cy - s * 0.7 - r, cx + s * 0.4 + r, cy - s * 0.7 + r], outline=col, width=w)
    elif kind == "music":
        r = s * 0.3
        d.ellipse([cx - s * 0.6 - r, cy + s * 0.55 - r, cx - s * 0.6 + r, cy + s * 0.55 + r], outline=col, width=w)
        L([(cx - s * 0.6 + r, cy + s * 0.55), (cx - s * 0.6 + r, cy - s * 0.9), (cx + s * 0.7, cy - s * 0.6)])
    elif kind == "video":
        d.polygon([(cx - s * 0.6, cy - s), (cx + s, cy), (cx - s * 0.6, cy + s)], outline=col, width=w)
    elif kind == "star":
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5
            rr = s if i % 2 == 0 else s * 0.42
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        d.polygon(pts, outline=col, width=w)
    elif kind == "game":
        d.rounded_rectangle([cx - s, cy - s * 0.55, cx + s, cy + s * 0.55], radius=s * 0.4, outline=col, width=w)
        L([(cx - s * 0.6, cy), (cx - s * 0.2, cy)])
        L([(cx - s * 0.4, cy - s * 0.2), (cx - s * 0.4, cy + s * 0.2)])
        r = s * 0.1
        for dx in (0.35, 0.6):
            d.ellipse([cx + s * dx - r, cy - r, cx + s * dx + r, cy + r], fill=col)
    elif kind == "link":
        for dx in (-0.35, 0.35):
            d.rounded_rectangle([cx + s * dx - s * 0.55, cy - s * 0.32, cx + s * dx + s * 0.55, cy + s * 0.32],
                                radius=s * 0.3, outline=col, width=w)
    elif kind == "search":
        r = s * 0.6
        d.ellipse([cx - s * 0.3 - r, cy - s * 0.3 - r, cx - s * 0.3 + r, cy - s * 0.3 + r], outline=col, width=w)
        L([(cx + s * 0.15, cy + s * 0.15), (cx + s, cy + s)])
    elif kind == "person":
        r = s * 0.38
        d.ellipse([cx - r, cy - s - 0 + 0, cx + r, cy - s + 2 * r], outline=col, width=w)
        d.arc([cx - s * 0.85, cy - s * 0.05, cx + s * 0.85, cy + s * 1.6], 180, 360, fill=col, width=w)
    elif kind == "check":
        L([(cx - s * 0.8, cy), (cx - s * 0.2, cy + s * 0.6), (cx + s * 0.9, cy - s * 0.6)])
    elif kind == "x":
        L([(cx - s * 0.6, cy - s * 0.6), (cx + s * 0.6, cy + s * 0.6)])
        L([(cx - s * 0.6, cy + s * 0.6), (cx + s * 0.6, cy - s * 0.6)])
    elif kind == "app":  # program window
        d.rectangle([cx - s, cy - s * 0.75, cx + s, cy + s * 0.75], outline=col, width=w)
        L([(cx - s, cy - s * 0.35), (cx + s, cy - s * 0.35)])
    elif kind == "gear":
        r = s * 0.42
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=w)
        for i in range(8):
            a = i * math.pi / 4
            L([(cx + r * 1.25 * math.cos(a), cy + r * 1.25 * math.sin(a)),
               (cx + s * math.cos(a), cy + s * math.sin(a))])
    elif kind == "zip":
        L([(cx, cy - s), (cx, cy + s * 0.2)])
        for i in range(4):
            y = cy - s + i * s * 0.35
            L([(cx - s * 0.3, y), (cx, y)] if i % 2 else [(cx, y), (cx + s * 0.3, y)])
        d.rectangle([cx - s * 0.3, cy + s * 0.2, cx + s * 0.3, cy + s * 0.8], outline=col, width=w)
    elif kind == "win":
        g = s * 0.12
        for dx in (-1, 1):
            for dy in (-1, 1):
                x, y = cx + dx * (g + s * 0.35) - s * 0.35, cy + dy * (g + s * 0.35) - s * 0.35
                d.rectangle([x, y, x + s * 0.7, y + s * 0.7], fill=col)


def other_image(size, colors, shape, symbol):
    """Drive, This PC, Recycle Bin or file: dark panel, accent outline, accent details."""
    acc, bg = rgb(colors["accent"]), rgb(colors["lighter_background"])
    glyph = rgb(colors.get("hud_glyph", colors["accent"]))
    N = size * SS
    u = lambda f: f * N
    small = size <= 24
    w = max(SS, round(N * (0.035 if small else 0.018)))
    sw = max(SS, round(N * (0.05 if small else 0.028)))
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if shape == "drive":
        box = [u(0.05), u(0.3), u(0.95), u(0.72)]
        d.rectangle(box, fill=bg + (235,), outline=acc + (230,), width=w)
        d.rectangle([u(0.12), u(0.56), u(0.2), u(0.64)], fill=acc + (255,))  # activity light
        d.line([(u(0.3), u(0.6)), (u(0.62), u(0.6))], fill=acc + (160,), width=w)
        if symbol:
            draw_symbol(d, symbol, u(0.8), u(0.45), u(0.08 if not small else 0.1), sw if symbol != "win" else w, glyph + (255,))
        if not small:
            t = u(0.1)
            d.line([(box[2] - t, box[3] + w * 1.8), (box[2] + w * 1.8, box[3] + w * 1.8), (box[2] + w * 1.8, box[3] - t)],
                   fill=acc + (230,), width=w)
    elif shape == "pc":
        d.rectangle([u(0.06), u(0.12), u(0.94), u(0.7)], fill=bg + (235,), outline=acc + (230,), width=w)
        d.line([(u(0.5), u(0.7)), (u(0.5), u(0.82))], fill=acc + (230,), width=w)
        d.line([(u(0.3), u(0.86)), (u(0.7), u(0.86))], fill=acc + (255,), width=w * 2)
        if not small:
            d.rectangle([u(0.06), u(0.12), u(0.3), u(0.2)], fill=acc + (255,))  # tab
        draw_symbol(d, symbol or "", u(0.5), u(0.43), u(0.16), sw, glyph + (255,))
    elif shape == "bin":
        d.polygon([(u(0.18), u(0.26)), (u(0.82), u(0.26)), (u(0.74), u(0.9)), (u(0.26), u(0.9))],
                  fill=bg + (235,), outline=acc + (230,), width=w)
        d.line([(u(0.1), u(0.2)), (u(0.9), u(0.2))], fill=acc + (255,), width=w * 2)
        d.rectangle([u(0.4), u(0.1), u(0.6), u(0.2)], outline=acc + (230,), width=w)
        if symbol == "full":
            for i in range(3):
                y = u(0.42) + i * u(0.14)
                d.line([(u(0.32), y), (u(0.68), y)], fill=glyph + (255,), width=sw)
    else:  # file: panel with an angled top-right cut
        x0, x1, y0, y1, c = u(0.16), u(0.84), u(0.06), u(0.94), u(0.2)
        d.polygon([(x0, y0), (x1 - c, y0), (x1, y0 + c), (x1, y1), (x0, y1)],
                  fill=bg + (235,), outline=acc + (230,), width=w)
        d.line([(x1 - c, y0), (x1 - c, y0 + c), (x1, y0 + c)], fill=acc + (230,), width=w)
        if not small:
            d.rectangle([x0, y1 - u(0.05), x0 + u(0.3), y1], fill=acc + (255,))  # code strip
        if symbol:  # also at 16 px: list views show files that small
            draw_symbol(d, symbol, u(0.5), u(0.55), u(0.2), sw, glyph + (255,))
    return img.resize((size, size), Image.LANCZOS)


def folder_image(size, colors, symbol):
    acc, bg = rgb(colors["accent"]), rgb(colors["lighter_background"])
    glyph = rgb(colors.get("hud_glyph", colors["accent"]))
    N = size * SS
    u = lambda f: f * N
    small = size <= 24
    w = max(SS, round(N * (0.035 if small else 0.018)))  # outline width
    img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x0, x1, top, y1 = u(0.05), u(0.95), u(0.26), u(0.86)
    tab_y = u(0.13)
    # Body: dark translucent panel.
    d.rectangle([x0, top, x1, y1], fill=bg + (235,))
    # Glow behind the outline (big sizes only).
    if size >= 48:
        g = Image.new("RGBA", (N, N), (0, 0, 0, 0))
        ImageDraw.Draw(g).rectangle([x0, top, x1, y1], outline=acc + (150,), width=w * 3)
        img = Image.alpha_composite(g.filter(ImageFilter.GaussianBlur(w * 1.5)), img)
        d = ImageDraw.Draw(img)
    d.rectangle([x0, top, x1, y1], outline=acc + (230,), width=w)
    # Tab with an angled cut on the right, joined to the body.
    d.polygon([(x0, tab_y), (u(0.50), tab_y), (u(0.50) + (top - tab_y), top + w), (x0, top + w)], fill=acc + (255,))
    if not small:
        m = u(0.045)
        d.rectangle([x0 + u(0.05), tab_y + (top - tab_y) / 2 - m / 2, x0 + u(0.05) + m, tab_y + (top - tab_y) / 2 + m / 2],
                    fill=bg + (255,))
        # Corner ticks, bottom right, like the panel brackets.
        t = u(0.12)
        d.line([(x1 - t, y1 + w * 1.8), (x1 + w * 1.8, y1 + w * 1.8), (x1 + w * 1.8, y1 - t)], fill=acc + (230,), width=w)
    if symbol and size >= 20:
        sw = max(SS, round(N * (0.05 if small else 0.028)))
        draw_symbol(d, symbol, u(0.5), u(0.57), u(0.17 if not small else 0.2), sw, glyph + (255,))
    return img.resize((size, size), Image.LANCZOS)


def build_ico(draw):
    """Multi-size .ico, every size drawn on its own by draw(size), stored as PNG entries."""
    pngs = []
    for s in SIZES:
        b = io.BytesIO()
        draw(s).save(b, "PNG")
        pngs.append((s, b.getvalue()))
    out = io.BytesIO()
    out.write(struct.pack("<HHH", 0, 1, len(pngs)))
    offset = 6 + 16 * len(pngs)
    for s, data in pngs:
        out.write(struct.pack("<BBBBHHII", s % 256, s % 256, 0, 0, 1, 32, len(data), offset))
        offset += len(data)
    for _, data in pngs:
        out.write(data)
    return out.getvalue()


def main():
    previews = []
    wanted = [a for a in sys.argv[1:] if not a.startswith("--")]
    for theme in (wanted or THEMES):
        colors = tomllib.loads((ROOT / "omarchy-dl" / theme / "colors.toml").read_text(encoding="utf-8"))
        pack = ROOT / "icons" / theme / "HUD Folders"
        res = pack / "Windhawk Resources"
        res.mkdir(parents=True, exist_ok=True)
        # Explorer keeps the active pack's DLL open: Windows allows renaming it, not overwriting it.
        for old in res.glob("imageres.dll*.old"):
            try:
                old.unlink()
            except PermissionError:
                pass
        dll = res / "imageres.dll"
        if dll.exists():
            try:
                dll.unlink()
            except PermissionError:
                dll.rename(res / f"imageres.dll.{len(list(res.glob('*.old')))}.old")
        res_file = ROOT / "iconpack" / f"{theme}.res"
        icons = {gid: build_ico(lambda s, sym=sym: folder_image(s, colors, sym)) for gid, sym in GROUPS.items()}
        icons |= {gid: build_ico(lambda s, k=k: other_image(s, colors, *k)) for gid, k in OTHER.items()}
        files = ROOT / "icons" / theme / "files"
        files.mkdir(exist_ok=True)
        for kind, sym in FILE_KINDS.items():
            (files / f"{kind}.ico").write_bytes(build_ico(lambda s, sym=sym: other_image(s, colors, "file", sym)))
        ico_res.write_res(res_file, icons)
        subprocess.run(["dotnet", "build", str(PROJECT), "-c", "Release", "-nologo", "-v", "q",
                        f"-p:IconRes={res_file}", "-o", str(res)],
                       check=True)
        for extra in res.glob("imageres.*"):
            if extra.suffix not in (".dll", ".old"):
                extra.unlink()
        (pack / "theme.ini").write_text(
            "[redirections]\n%SystemRoot%\\System32\\imageres.dll=.\\Windhawk Resources\\imageres.dll\n",
            encoding="utf-16")
        print("built", theme)
        if "--preview" in sys.argv:
            row = Image.new("RGB", (14 * 72, 80), rgb(colors["background"]))
            for i, sym in enumerate(["", "desktop", "download", "doc", "picture", "music", "video",
                                     "star", "game", "link", "search", "person", "check", ""]):
                im = folder_image(64 if i < 13 else 24, colors, sym)
                row.paste(im, (i * 72 + 4, 8), im)
            previews.append(row)
            row = Image.new("RGB", (14 * 72, 80), rgb(colors["background"]))
            for i, k in enumerate([OTHER[g] for g in (36, 32, 33, 31, 109, 25, 55, 54, 2, 102, 15, 69, 174, 23)]):
                im = other_image(64, colors, *k)
                row.paste(im, (i * 72 + 4, 8), im)
            previews.append(row)
    if previews:
        sheet = Image.new("RGB", (previews[0].width, 80 * len(previews)))
        for i, r in enumerate(previews):
            sheet.paste(r, (0, i * 80))
        sheet.save(ROOT / "icons" / ("pack-preview.png" if wanted else "hud-preview.png"))


if __name__ == "__main__":
    main()
