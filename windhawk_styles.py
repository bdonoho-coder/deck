"""Writes windhawk-styles.reg: one-time settings for the Windhawk mods.

The styles read SystemAccentColorDark3 (the theme background, set by the
picker) and SystemAccentColor, so they follow every theme switch without
touching Windhawk again. Import needs admin:  reg import windhawk-styles.reg
"""
import time
from pathlib import Path

ROOT = Path(__file__).parent
MODS = r"HKEY_LOCAL_MACHINE\SOFTWARE\Windhawk\Engine\Mods"

BG = '<SolidColorBrush Color="{ThemeResource SystemAccentColorDark3}"/>'
BG_SOFT = '<SolidColorBrush Color="{ThemeResource SystemAccentColorDark3}" Opacity="0.85"/>'
LINE = '<SolidColorBrush Color="{ThemeResource SystemAccentColor}" Opacity="0.45"/>'
BLUR = '<WindhawkBlur BlurAmount="18" TintColor="{ThemeResource SystemAccentColorDark3}" TintOpacity="0.85"/>'
CLEAR = "Background=Transparent"
# The picker's font ("HUD Face", per-user install); without it Bahnschrift.
# Icon glyphs fall back to the icon fonts.
FONT = ("TextBlock", ["FontFamily=HUD Face, Bahnschrift, Segoe Fluent Icons, Segoe MDL2 Assets"])
PANEL = ["Background:=" + BLUR, "BorderThickness=1", "BorderBrush:=" + LINE]

TASKBAR = [
    ("Taskbar.TaskbarFrame > Grid#RootGrid > Taskbar.TaskbarBackground > Grid > Rectangle#BackgroundFill",
     ["Fill:=" + BG]),
    ("Taskbar.TaskbarBackground#HoverFlyoutBackgroundControl > Grid > Rectangle#BackgroundFill",
     ["Fill:=" + BG]),
    ("Rectangle#BackgroundStroke", ["Fill:=" + LINE]),
    FONT,
]

ACCENT = '<SolidColorBrush Color="{ThemeResource SystemAccentColor}"/>'
TINT = '<SolidColorBrush Color="{ThemeResource SystemAccentColor}" Opacity="0.22"/>'
HOVER = '<SolidColorBrush Color="{ThemeResource SystemAccentColor}" Opacity="0.12"/>'
# HUD field: square, dark fill, thin accent outline.
FIELD = ["CornerRadius=0", "BorderThickness=1", "BorderBrush:=" + LINE, "Background:=" + BG]

def art(name, align):
    """Theme art drawn by make_explorer_art.py; the picker copies the theme's set to explorer-art/active."""
    uri = "file:///" + str(ROOT / "explorer-art" / "active" / name).replace("\\", "/")
    return f'<ImageBrush ImageSource="{uri}" Stretch="None" {align}/>'


EXPLORER = [
    ("FileExplorerExtensions.CommandBarControl_Wave1 > Grid, Grid#CommandBarControlRootGrid",
     ["Background:=" + art("cmdbar.png", 'AlignmentX="Left" AlignmentY="Bottom"'),
      "BorderThickness=0,0,0,1", "BorderBrush:=" + LINE]),
    ("Grid#TabContainerGrid", ["Background:=" + art("tabrow.png", 'AlignmentX="Right" AlignmentY="Center"')]),
    FONT,
    ("CommandBar#FileExplorerCommandBar", ["Background=Transparent"]),
    ("Grid#NavigationBarControlGrid", ["Background:=" + BG_SOFT]),
    # Tabs: square blocks instead of curved shapes; the open tab gets a tint
    # and a bright accent line on top.
    ("TabViewItem > Grid#LayoutRoot > Canvas", ["Visibility=Collapsed"]),
    ("TabViewItem > Grid#LayoutRoot > Grid#TabContainer",
     ["Background=Transparent", "BorderThickness=0"]),
    ("TabViewItem", ["Margin=0,0,2,0"]),
    ("TabViewItem > Grid#LayoutRoot", ["CornerRadius=0", "BorderThickness=0,2,0,0"]),
    ("TabViewItem > Grid#LayoutRoot@CommonStates", [
        "Background@Normal=Transparent", "BorderBrush@Normal=Transparent",
        "Background@PointerOver:=" + HOVER, "BorderBrush@PointerOver:=" + LINE,
        "Background@Selected:=" + TINT, "BorderBrush@Selected:=" + ACCENT,
        "Background@PointerOverSelected:=" + TINT, "BorderBrush@PointerOverSelected:=" + ACCENT,
        "Background@PressedSelected:=" + TINT, "BorderBrush@PressedSelected:=" + ACCENT]),
    ("Grid#TabContainerGrid > Border#LeftBottomBorderLine", ["Background:=" + LINE]),
    ("Grid#TabContainerGrid > Border#RightBottomBorderLine", ["Background:=" + LINE]),
    # Address bar and search box.
    ("FileExplorerExtensions.AddressBarControl > Grid#PART_LayoutRoot", FIELD),
    ("AutoSuggestBox#FileExplorerSearchBox > Grid#LayoutRoot > TextBox > Grid@CommonStates > Border#BorderElement",
     FIELD),
    ("Grid#HomeViewRootGrid", ["Background=Transparent"]),
    ("FileExplorerExtensions.GalleryViewControl#GalleryViewControl > Grid", ["Background=Transparent"]),
    ("Microsoft.UI.Xaml.Controls.Grid#GalleryRootGrid", ["Background=Transparent"]),
    ("Grid#DetailsViewControlRootGrid", ["Background=Transparent"]),
    ("StackPanel#DetailsViewThumbnail > Grid", ["Background=Transparent"]),
]


# Only backgrounds and edges change; text keeps Windows' colors (readable in light mode).
START_MENU = [
    ("Border#AcrylicBorder", PANEL),
    ("Border#AcrylicOverlay", ["Visibility=Collapsed"]),
    ("MenuFlyoutPresenter > Border", PANEL),
    FONT,
]

SETTINGS = [FONT]

# HUD panels: square, blur fill, thin accent outline. Target names come from
# research/notification-center-styler.md (mod v1.8 source + styling guide).
PANEL_SQ = PANEL + ["CornerRadius=0"]
LINE_SOFT = '<SolidColorBrush Color="{ThemeResource SystemAccentColor}" Opacity="0.3"/>'
LABEL = ["Foreground:=" + ACCENT, "CharacterSpacing=60", "FontSize=11", "FontWeight=SemiBold"]
NOTIFICATIONS = [
    # Notification center shrinks to its content (VerticalAlignment 2 = Center) instead of filling the screen height.
    ("Grid#NotificationCenterGrid", PANEL_SQ + ["VerticalAlignment=2"]),
    ("Grid#CalendarCenterGrid", PANEL_SQ),
    ("Grid#ControlCenterRegion", PANEL_SQ),
    ("Grid#MediaTransportControlsRegion", PANEL_SQ),
    # Toasts: accent edge on the left, square.
    ("Border#ToastBackgroundBorder, Border#ToastBackgroundBorder2",
     ["Background:=" + BLUR, "CornerRadius=0", "BorderThickness=3,1,1,1", "BorderBrush:=" + ACCENT]),
    ("Border#JumpListRestyledAcrylic", PANEL_SQ),
    ("MenuFlyoutPresenter > Border", PANEL_SQ),
    ("ScrollViewer#CalendarControlScrollViewer", [CLEAR]),
    ("Border#CalendarHeaderMinimizedOverlay", [CLEAR]),
    ("ActionCenter.FocusSessionControl#FocusSessionControl > Grid#FocusGrid", [CLEAR]),
    ("Grid#L1Grid > Border", [CLEAR]),
    ("Grid#MediaTransportControlsRoot", [CLEAR]),
    ("ActionCenter.FlexibleToastView#FlexibleNormalToastView", [CLEAR]),
    # Header row ("Notifications", do-not-disturb, Clear all): scale line under it, square buttons.
    ("Grid#NotificationCenterTopBanner", ["BorderThickness=0,0,0,1", "BorderBrush:=" + LINE, "Padding=0,0,0,6"]),
    ("Button#ClearAll", ["CornerRadius=0", "BorderThickness=1", "BorderBrush:=" + LINE]),
    ("Windows.UI.Xaml.Controls.Primitives.ToggleButton#DoNotDisturbButton", ["CornerRadius=0"]),
    # Group headers (app name above a group) and sender names as accent code labels.
    ("Grid#GroupTitleGrid > TextBlock#Title", LABEL),
    ("TextBlock#SenderName", LABEL),
    ("TextBlock#TimeStamp", ["Foreground:=" + LINE]),
    # Notification cards: square dark plates with a thin outline.
    ("ActionCenter.FlexibleItemView", ["CornerRadius=0"]),
    ("Border#ItemOpaquePlating", ["CornerRadius=0", "BorderThickness=1", "BorderBrush:=" + LINE_SOFT, "Background:=" + BG_SOFT]),
    # Quick settings tiles square.
    ("ControlCenter.PaginatedToggleButton#ToggleButton", ["CornerRadius=0"]),
    FONT,
]


def q(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def mod_block(mod_id, styles, extra):
    key = f"{MODS}\\{mod_id}\\Settings"
    lines = [f"[-{key}]", f"[{key}]", '"theme"=""', '"styleConstants[0]"=""',
             '"themeResourceVariables[0]"=""']
    lines += extra
    for i, (target, rules) in enumerate(styles):
        lines.append(f'"controlStyles[{i}].target"={q(target)}')
        for j, rule in enumerate(rules):
            lines.append(f'"controlStyles[{i}].styles[{j}]"={q(rule)}')
    # Windhawk reloads a mod's settings when this time changes.
    lines += ["", f"[{MODS}\\{mod_id}]", '"SettingsChangeTime"=dword:%08x' % int(time.time()), ""]
    return lines


def icon_block():
    """Resource Redirect reads icons/active.ini, which the picker rewrites per theme.

    Limited to explorer.exe: active.ini is user-writable, so it must not
    reach programs that run as administrator.
    """
    mod = f"{MODS}\\icon-resource-redirect"
    return [f"[-{mod}\\Settings]", f"[{mod}\\Settings]", '"iconTheme"=""',
            '"disableThumbnails"=dword:00000000', '"allResourceRedirect"=dword:00000000',
            '"themePaths[0]"=' + q(str(ROOT / "icons" / "active.ini")),
            '"redirectionResourcePaths[0].original"=""',
            '"redirectionResourcePaths[0].redirect"=""', '"themeFolder"=""', "",
            f"[{mod}]", '"Include"="explorer.exe"',
            '"SettingsChangeTime"=dword:%08x' % int(time.time()), ""]


def main():
    out = ["Windows Registry Editor Version 5.00", ""]
    out += icon_block()
    out += mod_block("windows-11-taskbar-styler", TASKBAR, [
        '"clickThroughTaskbar"=dword:00000000', '"xamlDiagnosticsHandling"="alert"'])
    out += mod_block("windows-11-start-menu-styler", START_MENU, [
        '"disableNewStartMenuLayout"=""', '"webContentStyles[0].target"=""',
        '"webContentStyles[0].styles[0]"=""', '"webContentCustomJs"=""'])
    out += mod_block("windows-11-notification-center-styler", NOTIFICATIONS, [])
    out += mod_block("windows-11-settings-styler", SETTINGS, [])
    out += mod_block("windows-11-file-explorer-styler", EXPLORER, [
        '"xamlDiagnosticsHandling"="alert"',
        # Blur stays on when the window is inactive; Mica Alt turns solid gray.
        '"backgroundTranslucentEffect"="acrylicblur"',
        '"backgroundTranslucentEffectRegion"=""',
        '"explorerFrameContainerHeight"=dword:00000000'])
    (ROOT / "windhawk-styles.reg").write_text("\r\n".join(out) + "\r\n", encoding="utf-16")
    print("wrote windhawk-styles.reg")


if __name__ == "__main__":
    main()
