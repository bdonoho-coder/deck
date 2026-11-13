r"""Packs the free tier of Deck (picker + 7 standard themes + the Deck file manager) for release.

Writes release\deck-free\ and release\deck-free-<version>.zip, then lints the result:
nothing from LineX, niivu/Papirus packs, Omarchy photos or the paid hud-* themes may be
inside, and no shipped text file may carry a path from this machine.

  py make_release.py            pack + lint + zip
  py make_release.py --no-zip   pack + lint only
"""
import json
import os
import shutil
import sys
import tomllib
import zipfile
from pathlib import Path

import make_themes  # ANSI + THEMES, no side effects on import

ROOT = Path(__file__).parent
VERSION = "0.1.0"
OUT = ROOT / "release" / "deck-free"
FREE = ["tokyo-night", "catppuccin", "gruvbox", "nord", "everforest", "catppuccin-latte", "amber-lab"]
OWN_WALLPAPERS = {"7-ridges.jpg", "8-contours.jpg", "9-glow.jpg"}
STARTUP = Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
PKG = ROOT / "files-pkg" / "Files.App_4.3.0.0_x64_Test"
TEXT = {".ahk", ".ps1", ".py", ".ini", ".md", ".json", ".reg", ".txt"}
FORBIDDEN_PATH = ("linex", "niivu", "papirus", "tokyo night blank", "catppuccin mocha", "catppuccin latte", "hud-")
# This machine's user name and any user-profile path must not leak into shipped text files.
FORBIDDEN_TEXT = (os.environ.get("USERNAME") or "no-user", "C:" + chr(92) + "Users" + chr(92), "C:/Users/")


def copy(src, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def read_ini(path):
    """UTF-16 ini -> ordered {section: [lines]}."""
    sections, cur = {}, None
    for line in path.read_text(encoding="utf-16").splitlines():
        if line.startswith("[") and line.endswith("]"):
            cur = line[1:-1]
            sections[cur] = []
        elif cur is not None and line.strip():
            sections[cur].append(line)
    return sections


def pack():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    # Scripts (AutoHotkey v2 + the optional helpers).
    for name in ("ThemePicker.ahk", "Finder.ahk", "HudFrame.ahk", "file_icons.py", "app_icons.ps1"):
        copy(ROOT / name, OUT / name)
    copy(STARTUP / "DesktopScroll.ahk", OUT / "DesktopScroll.ahk")

    # themes.ini: only the free themes, wallpapers as a relative path (the picker resolves it).
    ini = []
    for tid, lines in read_ini(ROOT / "themes.ini").items():
        if tid not in FREE:
            continue
        ini.append(f"[{tid}]")
        ini += [f"wallpapers=wallpapers\\{tid}" if l.startswith("wallpapers=") else l for l in lines]
        ini.append("")
    (OUT / "themes.ini").write_text("\n".join(ini), encoding="utf-16")

    # Windows Terminal color schemes, for a manual or scripted merge into settings.json.
    schemes = []
    for tid in FREE:
        colors = tomllib.loads((ROOT / "omarchy-dl" / tid / "colors.toml").read_text(encoding="utf-8"))
        scheme = {"name": make_themes.THEMES[tid], "background": colors["background"],
                  "foreground": colors["foreground"], "cursorColor": colors["accent"],
                  "selectionBackground": colors["selection"]}
        scheme.update({k: colors[v] for k, v in make_themes.ANSI.items()})
        schemes.append(scheme)
    (OUT / "terminal-schemes.json").write_text(json.dumps(schemes, indent=2), encoding="utf-8")

    # Per-theme assets: own wallpapers, our folder/file icon packs, app icons without LineX, Explorer art.
    for tid in FREE:
        for wp in sorted((ROOT / "wallpapers" / tid).glob("*.jpg")):
            if wp.name in OWN_WALLPAPERS or tid == "amber-lab":  # amber-lab wallpapers are fal-generated (ours)
                copy(wp, OUT / "wallpapers" / tid / wp.name)
        shutil.copytree(ROOT / "icons" / tid / "HUD Folders", OUT / "icons" / tid / "HUD Folders",
                        ignore=shutil.ignore_patterns("*.old"))
        shutil.copytree(ROOT / "icons" / tid / "files", OUT / "icons" / tid / "files")
        shutil.copytree(ROOT / "release" / "appicons" / tid, OUT / "appicons" / tid)
        art = ROOT / "explorer-art" / tid
        if art.exists():
            shutil.copytree(art, OUT / "explorer-art" / tid)
    (OUT / "explorer-art" / "none").mkdir(parents=True, exist_ok=True)
    (OUT / "appicons" / "active").mkdir(parents=True, exist_ok=True)

    # Fonts (HUD Face copies) + their license.
    for f in (ROOT / "fonts" / "hud").glob("*.ttf"):
        copy(f, OUT / "fonts" / "hud" / f.name)

    # Windhawk settings as a template; install.ps1 fills in the install folder.
    reg = (ROOT / "windhawk-styles.reg").read_text(encoding="utf-16")
    # .reg strings double every backslash; the Explorer art is referenced as a file:/// URI.
    root_reg, root_uri = str(ROOT).replace("\\", "\\\\"), str(ROOT).replace("\\", "/")
    assert root_reg in reg and root_uri in reg, "windhawk-styles.reg has no root path to template"
    reg = reg.replace(root_reg, "{{ROOT}}").replace(root_uri, "{{ROOT_URI}}")
    (OUT / "windhawk-styles.template.reg").write_text(reg, encoding="utf-16")

    # The Deck file manager: unsigned MSIX + the Windows App Runtime it needs.
    copy(PKG / "Files.App_4.3.0.0_x64.msix", OUT / "deck-app" / f"Deck_{VERSION}_x64.msix")
    copy(PKG / "Dependencies" / "x64" / "Microsoft.WindowsAppRuntime.2.msix",
         OUT / "deck-app" / "Microsoft.WindowsAppRuntime.2.msix")

    # Docs and licenses.
    shutil.copytree(ROOT / "release" / "LICENSES", OUT / "LICENSES")
    for name in ("README.md", "CREDITS.md", "NOTICE", "LICENSE", "install.ps1"):
        copy(ROOT / "release" / name, OUT / name)
    (OUT / "VERSION").write_text(VERSION + "\n", encoding="utf-8")


def lint():
    problems = []
    total = 0
    for p in OUT.rglob("*"):
        if p.is_dir():
            continue
        total += p.stat().st_size
        rel = str(p.relative_to(OUT))
        low = rel.lower()
        if any(f in low for f in FORBIDDEN_PATH):
            problems.append(f"forbidden path: {rel}")
        if rel.startswith("wallpapers") and p.suffix == ".jpg" and p.parent.name != "amber-lab" \
                and p.name not in OWN_WALLPAPERS:
            problems.append(f"third-party wallpaper: {rel}")
        if p.suffix.lower() in TEXT:
            raw = p.read_bytes()
            text = raw.decode("utf-16") if raw[:2] in (b"\xff\xfe", b"\xfe\xff") else raw.decode("utf-8", "replace")
            for bad in FORBIDDEN_TEXT:
                if bad in text:
                    problems.append(f"machine path '{bad}' in {rel}")
    for lic in (OUT / "LICENSES").iterdir():
        if lic.stat().st_size < 200:
            problems.append(f"license too short: {lic.name}")
    for must in ("README.md", "CREDITS.md", "NOTICE", "LICENSE", "install.ps1", "themes.ini",
                 "deck-app/Deck_%s_x64.msix" % VERSION, "fonts/hud/chakra-regular.ttf"):
        if not (OUT / must).exists():
            problems.append(f"missing: {must}")
    return problems, total


def main():
    pack()
    problems, total = lint()
    files = sum(1 for p in OUT.rglob("*") if p.is_file())
    print(f"packed {files} files, {total / 1e6:.1f} MB -> {OUT}")
    if problems:
        print("LINT FAILED:")
        for p in problems:
            print("  " + p)
        sys.exit(1)
    print("lint ok")
    if "--no-zip" in sys.argv:
        return
    zip_path = ROOT / "release" / f"deck-free-{VERSION}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in OUT.rglob("*"):
            if p.is_file():
                z.write(p, f"deck-free/{p.relative_to(OUT).as_posix()}")
    print(f"zip {zip_path.stat().st_size / 1e6:.1f} MB -> {zip_path}")


if __name__ == "__main__":
    main()
