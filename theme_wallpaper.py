"""Own wallpapers for the non-HUD themes (used by make_themes.py).

theme_wallpapers(tid, colors, out_dir) writes two files:
  7-ridges.jpg    layered soft mountain ridges with a faint glow at the horizon
  8-contours.jpg  thin topographic contour lines and two soft color blobs
Both work for dark and light themes. Output is repeatable (seeded by theme id).
The bottom ~90 px stay quiet because the taskbar auto-hides there.
"""
import math
import random

from PIL import Image, ImageDraw, ImageFilter

SIZE = (2560, 1600)
TB = 90  # quiet strip at the bottom


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def finish(img, path):
    """Upscale to full size, add light grain against banding, save."""
    img = img.resize(SIZE, Image.BICUBIC)
    noise = Image.effect_noise(SIZE, 6).convert("RGB")
    Image.blend(img, noise, 0.03).save(path, quality=93)


def ridge_y(x, base, amp, rng):
    """Smooth ridge height: a few sine waves with random phase."""
    waves = [(rng.uniform(1.0, 2.0), rng.uniform(0, 6.3), 1.0),
             (rng.uniform(2.5, 4.5), rng.uniform(0, 6.3), 0.5),
             (rng.uniform(5.0, 8.0), rng.uniform(0, 6.3), 0.22)]
    return [base - amp * sum(a * math.sin(f * 6.283 * xi / x + p) for f, p, a in waves) / 1.7
            for xi in range(x)]


def ridges(tid, colors, path):
    rng = random.Random(tid + "ridges")
    W, H = SIZE[0] // 2, SIZE[1] // 2
    light = colors["mode"] == "light"
    bg = rgb(colors["background"])
    acc = rgb(colors["accent"])
    if light:
        far, near = mix(bg, rgb(colors["selection"]), 0.7), rgb(colors["darker_background"])
        near = mix(near, rgb(colors["muted"]), 0.5)
    else:
        far, near = rgb(colors["lighter_background"]), rgb(colors["darker_background"])
    # Sky: background with a faint accent glow low in the sky.
    img = Image.new("RGB", (W, H), bg)
    horizon = int(H * 0.52)
    glow = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(glow)
    gx = int(W * rng.uniform(0.35, 0.65))
    gd.ellipse([gx - W * 0.35, horizon - H * 0.22, gx + W * 0.35, horizon + H * 0.22], fill=70 if light else 85)
    glow = glow.filter(ImageFilter.GaussianBlur(W // 12))
    img.paste(Image.new("RGB", (W, H), acc), (0, 0), glow)
    d = ImageDraw.Draw(img)
    layers = 5
    for i in range(layers):
        t = i / (layers - 1)
        base = horizon + t * H * 0.26
        amp = H * (0.07 + 0.04 * t)
        ys = ridge_y(W, base, amp, rng)
        col = mix(far, near, t ** 0.8)
        # Hazy far layers: blend toward the sky color.
        col = mix(col, bg, 0.35 * (1 - t))
        pts = [(x, y) for x, y in enumerate(ys)] + [(W, H), (0, H)]
        layer = Image.new("L", (W * 2, H * 2), 0)
        ImageDraw.Draw(layer).polygon([(x * 2, y * 2) for x, y in pts], fill=255)
        layer = layer.filter(ImageFilter.GaussianBlur(1.6)).resize((W, H), Image.LANCZOS)
        img.paste(Image.new("RGB", (W, H), col), (0, 0), layer)
        if i == 0:
            # Thin accent line along the farthest ridge, very faint.
            line = Image.new("L", (W * 2, H * 2), 0)
            ImageDraw.Draw(line).line([(x * 2, y * 2) for x, y in enumerate(ys)], fill=90, width=3)
            line = line.filter(ImageFilter.GaussianBlur(1.5)).resize((W, H), Image.LANCZOS)
            img.paste(Image.new("RGB", (W, H), acc), (0, 0), line)
    # Fade the bottom strip to one flat color so the taskbar zone is quiet.
    fade = Image.new("L", (1, H), 0)
    fh = int(TB / 2) + 40
    fade.putdata([int(255 * min(1, max(0, (y - (H - fh)) / fh))) for y in range(H)])
    img.paste(Image.new("RGB", (W, H), near), (0, 0), fade.resize((W, H)))
    finish(img, path)


def contours(tid, colors, path):
    rng = random.Random(tid + "contours")
    W, H = 800, 500  # field size; the mask is upscaled 3.2x
    light = colors["mode"] == "light"
    bg = rgb(colors["background"])
    img = Image.new("RGB", (W, H), bg)
    # Two soft blobs: accent and one secondary color, low alpha.
    sec = rgb(colors[rng.choice(["blue", "magenta", "green"])])
    blobs = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(blobs)
    alpha = 60 if light else 55
    for col, (cx, cy, r) in ((rgb(colors["accent"]), (0.70, 0.38, 0.30)), (sec, (0.22, 0.62, 0.26))):
        cx, cy, r = cx * W + rng.uniform(-40, 40), cy * H + rng.uniform(-30, 30), r * W
        bd.ellipse([cx - r, cy - r * 0.8, cx + r, cy + r * 0.8], fill=col + (alpha,))
    blobs = blobs.filter(ImageFilter.GaussianBlur(W // 8))
    img.paste(blobs, (0, 0), blobs)
    # Height field: a few gaussian hills plus a gentle wave.
    hills = [(rng.uniform(0.1, 0.9) * W, rng.uniform(0.1, 0.8) * H, rng.uniform(0.15, 0.3) * W,
              rng.uniform(0.6, 1.0)) for _ in range(5)]
    ph = [rng.uniform(0, 6.3) for _ in range(2)]
    f = [[0.0] * W for _ in range(H)]
    for y in range(H):
        row = f[y]
        for x in range(W):
            v = 0.15 * math.sin(x / W * 9 + ph[0]) + 0.1 * math.sin(y / H * 7 + x / W * 3 + ph[1])
            for hx, hy, hr, ha in hills:
                v += ha * math.exp(-((x - hx) ** 2 + (y - hy) ** 2) / (2 * hr * hr))
            row[x] = v * 9  # one unit = one contour step
    # Line mask: bright where the field is near a whole number, width ~1 px.
    mask = Image.new("L", (W, H), 0)
    data = []
    qstart = H - int(TB / 3.2) - 25
    for y in range(H):
        row = f[y]
        for x in range(W):
            v = row[x]
            gx = row[min(x + 1, W - 1)] - v
            gy = f[min(y + 1, H - 1)][x] - v
            g = math.hypot(gx, gy) + 1e-4
            dist = abs(v - round(v)) / g  # distance to the line in pixels
            a = max(0.0, 1.0 - dist / 0.9)
            if y > qstart:  # fade out near the taskbar
                a *= max(0.0, 1 - (y - qstart) / 25)
            data.append(int(a * 255))
    mask.putdata(data)
    mask = mask.point(lambda p: int(p * (0.40 if light else 0.50)))
    img.paste(Image.new("RGB", (W, H), rgb(colors["muted"])), (0, 0), mask)
    finish(img, path)


def theme_wallpapers(tid, colors, out_dir):
    """Writes 7-ridges.jpg and 8-contours.jpg into out_dir."""
    ridges(tid, colors, out_dir / "7-ridges.jpg")
    contours(tid, colors, out_dir / "8-contours.jpg")
