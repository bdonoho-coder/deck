"""Builds fonts\\hud\\<key>-regular.ttf / -bold.ttf from fonts\\src.

Every copy is renamed to the family "HUD Face". The picker registers only the
chosen pair (per user), so Explorer's Windhawk style, which asks for
"HUD Face, Bahnschrift", follows the picker without admin rights.
Renaming also keeps the OFL rule: modified fonts must not use the original name.
"""
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).parent
SRC, OUT = ROOT / "fonts" / "src", ROOT / "fonts" / "hud"
FAMILY = "HUD Face"

# key: (regular source, bold source); a variable font takes (file, weight).
FONTS = {
    "chakra": ("ChakraPetch-Medium.ttf", "ChakraPetch-Bold.ttf"),
    "exo2": (("Exo2-VF.ttf", 500), ("Exo2-VF.ttf", 700)),
    "rajdhani": ("Rajdhani-SemiBold.ttf", "Rajdhani-Bold.ttf"),
    "oxanium": (("Oxanium-VF.ttf", 500), ("Oxanium-VF.ttf", 700)),
    "saira": (("Saira-VF.ttf", 500), ("Saira-VF.ttf", 700)),
}


def load(src):
    if isinstance(src, str):
        return TTFont(SRC / src)
    font = TTFont(SRC / src[0])
    axes = {"wght": src[1]}
    if "wdth" in [a.axisTag for a in font["fvar"].axes]:
        axes["wdth"] = 100
    return instancer.instantiateVariableFont(font, axes)


def rename(font, bold):
    style = "Bold" if bold else "Regular"
    name = font["name"]
    for nid in (16, 17, 21, 22, 25):  # typographic and variable names
        name.removeNames(nameID=nid)
    for nid, text in {1: FAMILY, 2: style, 3: f"{FAMILY} {style}", 4: f"{FAMILY} {style}",
                      6: f"HUDFace-{style}"}.items():
        name.setName(text, nid, 3, 1, 0x409)
        name.setName(text, nid, 1, 0, 0)
    os2 = font["OS/2"]
    os2.usWeightClass = 700 if bold else 400
    os2.fsSelection = (os2.fsSelection & ~0b1100001) | (0b100000 if bold else 0b1000000)
    font["head"].macStyle = 1 if bold else 0
    for t in ("STAT",):
        if t in font:
            del font[t]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for key, (reg, bold) in FONTS.items():
        for src, is_bold in ((reg, False), (bold, True)):
            font = load(src)
            rename(font, is_bold)
            out = OUT / f"{key}-{'bold' if is_bold else 'regular'}.ttf"
            font.save(out)
            print("wrote", out.name)


if __name__ == "__main__":
    main()
