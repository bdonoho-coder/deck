# Deck (free tier)

One hotkey changes the whole look of Windows 11: wallpaper, accent colors, taskbar, Start menu,
notification center, File Explorer, folder icons, app icons, Terminal colors and window outlines.
Deck also brings its own file manager, a fork of the open-source Files app with themed "looks".

This free tier has 7 themes: Tokyo Night, Catppuccin Mocha, Gruvbox, Nord, Everforest,
Catppuccin Latte (light) and Amber Lab.

## What you need

- Windows 11, 64-bit.
- **AutoHotkey v2** (free): https://www.autohotkey.com. It runs the picker and the hotkeys.
- **Windhawk** (free): https://windhawk.net, with these mods installed from its Explore page:
  Windows 11 Taskbar Styler, Windows 11 Start Menu Styler, Windows 11 Notification Center Styler,
  Windows 11 File Explorer Styler, Resource Redirect. Without Windhawk you still get wallpapers,
  accent colors, fonts, app icons and the Deck file manager.
- **Developer Mode** on (Settings > System > For developers) if you want the Deck file manager.
  It is an unsigned package, so Windows only installs it in Developer Mode.
- Optional: Python 3 with Pillow, for themed file-type icons (text, image, media, zip).

## Install

1. Extract the zip. A short path without spaces works best, for example `C:\Deck`.
   Keep it there: the scripts, icons and wallpapers are used in place.
2. Open PowerShell in that folder and run:

   ```
   powershell -ExecutionPolicy Bypass -File .\install.ps1
   ```

   It backs up your current colors, writes `windhawk-styles.reg` for your folder, adds the
   scripts to Startup, starts them, and registers the Deck file manager.
3. Windhawk part, once, as admin: right-click `windhawk-styles.reg` and choose **Merge**
   (or run `reg import windhawk-styles.reg` from an admin prompt). Then restart Explorer or
   sign out and in. This gives the mods their styles and points Resource Redirect at the
   theme's icon pack. It does not change which mods are installed.
4. Press **Win+T** and pick a theme.

The picker's **FILES** row picks the look of the Deck file manager. **AUTO** is the cyber look
(open frames, places rail, file plates) for every theme. HUD, MINIMAL, DOSSIER, TREE, CONSOLE
and CYBER force one look. Deck restarts when the look changes.

Optional: Windows Terminal colors. Open Terminal settings, "Open JSON file", and add the
schemes from `terminal-schemes.json` to the `schemes` list. The picker then switches the
scheme with the theme.

Optional: themed app icons on your shortcuts. `app_icons.ps1` repoints known shortcuts
(Chrome, Steam, Discord, ...) at the themed icons; run it as admin. `app_icons.ps1 -Restore`
puts them back.

## Hotkeys

| Keys | What it does |
|---|---|
| Win + T | Theme picker |
| Win + E | Deck file manager |
| Win + Shift + W | Next wallpaper of the current theme |
| Win + Space | Quick finder for folders, apps and games |
| Win + mouse wheel | Switch virtual desktop, wraps around |

## Undo

- Theme picker > **Original (undo all)** restores your saved colors and wallpaper.
- App icons: `app_icons.ps1 -Restore` as admin.
- Windhawk: disable or remove the mods in Windhawk.
- Deck file manager: Settings > Apps > Installed apps > Deck > Uninstall. If you had set it as
  the default file manager in its settings, File Explorer comes back by itself.
- Startup: delete the four shortcuts in `shell:startup`.

## Folder map

- `ThemePicker.ahk`, `Finder.ahk`, `HudFrame.ahk`, `DesktopScroll.ahk`: the scripts.
- `themes.ini`: the theme list the picker reads. `current.ini` is created with your choice.
- `wallpapers/`, `icons/`, `appicons/`, `explorer-art/`, `fonts/`: the theme assets.
- `deck-app/`: the Deck file manager package and its runtime.
- `LICENSES/`, `CREDITS.md`, `NOTICE`: who made what, and under which license.

## Credits

Deck is built on Files, Omarchy, the Tokyo Night, Catppuccin, Nord, Everforest and Gruvbox
palettes, Google Fonts under the OFL and Simple Icons. See `CREDITS.md`. Deck is not
affiliated with any of these projects.
