# Deck

An Omarchy-style theme system for Windows 11, plus Deck, a themed fork of the
[Files](https://github.com/files-community/Files) file manager.

One hotkey (Win+T) changes the whole look: wallpaper, accent colors, taskbar, Start menu,
notification center, File Explorer, folder icons, app icons, Terminal colors and window
outlines. Deck follows the theme with its own "looks" (HUD, minimal, dossier, tree, deck,
cyber).

**Download:** the free tier (7 themes + Deck) is on the
[Releases](../../releases) page. Install steps are in [release/README.md](release/README.md).

**Deck source:** the file manager lives in its own repository,
[deck-files](https://github.com/bdonoho-coder/deck-files) (branch `hud-theme`), a fork of Files.

## What is in this repository

| Path | What it is |
|---|---|
| `ThemePicker.ahk` | The picker (Win+T): applies a theme, cycles wallpapers (Win+Shift+W), opens Deck (Win+E) |
| `Finder.ahk`, `HudFrame.ahk`, `DesktopScroll.ahk` | Quick finder (Win+Space), HUD window outlines, Win+wheel desktop switch |
| `make_themes.py` | Reads `omarchy-dl/<theme>/colors.toml`, writes `themes.ini`, wallpapers and Terminal schemes |
| `hud_wallpaper.py`, `cyber_wallpaper.py`, `theme_wallpaper.py` | Wallpaper generators |
| `make_folder_icons.py`, `ico_res.py`, `iconpack/` | Folder, drive, bin and file icons as a small `imageres.dll` per theme |
| `make_app_icons.py` | App icons from Simple Icons logos |
| `make_explorer_art.py`, `windhawk_styles.py` | Explorer top-area art and the Windhawk mod settings |
| `make_fonts.py` | "HUD Face" copies of five OFL fonts in `fonts/src` |
| `deck_logo.py` | The Deck app logo set |
| `files-build.ps1` | Builds and installs Deck from `files-src` (clone deck-files there) |
| `make_release.py`, `release/` | Packs and lints the free tier; license texts, credits, installer, README |
| `asset_audit.py` | Lists every third-party asset and whether it may ship |

## Build the assets yourself

Python 3.12+ with Pillow and fontTools, .NET SDK (for `iconpack`), AutoHotkey v2.

```
py make_fonts.py
py make_themes.py
py make_folder_icons.py
py make_app_icons.py --release
py make_explorer_art.py
py windhawk_styles.py
py make_release.py
```

## Support

Deck is free. The [HUD pack](https://bransondonoho.gumroad.com/l/deck-hud) adds 9 sci-fi
themes, and tips on [Ko-fi](https://ko-fi.com/branson91881) fund new themes.

## License

Deck's own scripts and generated art are MIT, see [LICENSE](LICENSE). Third-party parts keep
their licenses: [CREDITS.md](CREDITS.md), [NOTICE](NOTICE) and `release/LICENSES/`.
Not affiliated with the Files Community, Omarchy, or any of the color theme projects.
