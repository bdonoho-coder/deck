#Requires AutoHotkey v2.0
#SingleInstance Force

; Win + T opens the theme picker. Click a theme to apply it. Esc closes.
; Win + E opens Deck (our HUD build of the Files app).
; Themes come from themes.ini (built by make_themes.py).

global ThemesIni := A_ScriptDir "\themes.ini"
global StateIni := A_ScriptDir "\current.ini"
global BackupDir := A_ScriptDir "\backup"
global IconsIni := A_ScriptDir "\icons\active.ini"
global WtSettings := EnvGet("LOCALAPPDATA") "\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json"
global Picker := ""
; Picker font row: key (fonts\hud\<key>-*.ttf from make_fonts.py), button label.
global Fonts := [["bahnschrift", "BAHN"], ["chakra", "CHAKRA"], ["exo2", "EXO 2"]
    , ["rajdhani", "RAJDHANI"], ["oxanium", "OXANIUM"], ["saira", "SAIRA"]]
; Picker FILES row: look key written to current.ini (Deck reads it at start), button label.
global Looks := [["auto", "AUTO"], ["hud", "HUD"], ["minimal", "MINIMAL"], ["dossier", "DOSSIER"], ["tree", "TREE"], ["deck", "CONSOLE"], ["cyber", "CYBER"]]  ; "deck" look is labeled CONSOLE: Deck is the app's name now

; Tell Deck (the file manager) where this folder is: it reads current.ini from here at start.
DirCreate(EnvGet("LOCALAPPDATA") "\Deck")
try FileOpen(EnvGet("LOCALAPPDATA") "\Deck\root.txt", "w", "UTF-8-RAW").Write(A_ScriptDir)

A_TrayMenu.Insert("1&", "Pick theme (Win+T)", (*) => ShowPicker())
A_TrayMenu.Insert("2&", "Next wallpaper (Win+Shift+W)", (*) => NextWallpaper())
A_TrayMenu.Insert("3&")

if (A_Args.Length && A_Args[1] = "show")  ; restarted after a font switch
    ShowPicker()

#t::ShowPicker()
#+w::NextWallpaper()
#e::LaunchFiles()  ; our Files build (HUD or minimal look, by theme) instead of Explorer

ShowPicker() {
    global Picker
    if IsObject(Picker)
        Picker.Destroy()
    current := IniRead(StateIni, "state", "current", "")
    ; HUD panel in the current theme's colors (grey when no theme is active).
    known := (current != "" && current != "original")
    acc := known ? IniRead(ThemesIni, current, "accent", "888888") : "888888"
    panel := known ? IniRead(ThemesIni, current, "bg_dark", "0b0b0b") : "0b0b0b"
    light := known ? IniRead(ThemesIni, current, "bg_light", "1a1a1a") : "1a1a1a"
    muted := "7a7a7a", F := HudFont()
    RowW := 300, RowH := 40, Gap := 6, ColGap := 24
    g := Gui("+AlwaysOnTop -Caption +ToolWindow", "Theme Picker")
    g.BackColor := panel
    g.MarginX := 22, g.MarginY := 20

    ; Header: accent tab, hotkeys, accent rule.
    g.SetFont("s11 bold c" panel, F)
    g.AddText("xm ym w220 h26 +0x200 Background" acc, "  ■  THEME  //  SELECT")
    g.SetFont("s8 c" muted, F)
    g.AddText("x" (22 + 2 * RowW + ColGap - 330) " ym+6 w330 +Right", "WIN+T  ·  ESC CLOSE  ·  WIN+SHIFT+W NEXT WALLPAPER")
    g.AddText("xm y+8 w" (2 * RowW + ColGap) " h1 Background" acc)

    ; Two columns: standard themes, HUD themes.
    ids := StrSplit(IniRead(ThemesIni), "`n")
    cols := [[], []]
    for id in ids
        cols[(SubStr(id, 1, 4) = "hud-") ? 2 : 1].Push(id)
    top := 74
    for c, list in cols {
        x := 22 + (c - 1) * (RowW + ColGap)
        g.SetFont("s8 bold c" acc, F)
        g.AddText("x" x " y" top " w" RowW, (c = 1 ? "STD" : "HUD") "  //  " Format("{:02}", list.Length))
        for n, id in list {
            y := top + 20 + (n - 1) * (RowH + Gap)
            name := StrUpper(RegExReplace(IniRead(ThemesIni, id, "name"), "^HUD "))
            bg := IniRead(ThemesIni, id, "bg"), fg := IniRead(ThemesIni, id, "fg")
            if (id = current)  ; accent bar marks the active theme
                g.AddText("x" (x - 8) " y" y " w4 h" RowH " Background" acc)
            g.SetFont("s10 bold c" fg, F)
            row := g.AddText("x" x " y" y " w" RowW " h" RowH " +0x200 Background" bg
                , "   " Format("{:02}", n) "    " name ((id = current) ? "   ●" : ""))
            row.OnEvent("Click", ApplyAndClose.Bind(id))
            for i, sw in StrSplit(IniRead(ThemesIni, id, "swatches"), ",") {
                s := g.AddText("x" (x + RowW - 112 + i * 15) " y" (y + 13) " w10 h14 Background" sw)
                s.OnEvent("Click", ApplyAndClose.Bind(id))
            }
        }
    }
    bottom := top + 20 + Max(cols[1].Length, cols[2].Length) * (RowH + Gap) + 10

    ; App icon style for HUD themes: logos in the accent, or in their own colors.
    color := IniRead(StateIni, "state", "icons", "accent") = "color"
    g.AddText("x22 y" bottom " w" (2 * RowW + ColGap) " h1 Background" light)
    g.SetFont("s8 bold c" acc, F)
    g.AddText("x22 y" (bottom + 18) " w96 h30 +0x200", "APP ICONS  //")
    for opt in ["accent", "color"] {
        on := (opt = "color") = color
        g.SetFont("s10 bold c" (on ? panel : muted), F)
        b := g.AddText("x+8 yp w94 h30 +0x200 +Center Background" (on ? acc : light), StrUpper(opt))
        b.OnEvent("Click", SetIconStyle.Bind(opt))
    }
    g.SetFont("s10 bold c" ((current = "original") ? panel : "CCCCCC"), F)
    orig := g.AddText("x" (22 + RowW + ColGap) " y" (bottom + 18) " w" RowW " h30 +0x200 Background"
        ((current = "original") ? acc : light), "   ORIGINAL  //  UNDO ALL")
    orig.OnEvent("Click", ApplyAndClose.Bind("original"))

    ; Font for the HUD text in Explorer, picker, finder and overlay.
    font := IniRead(StateIni, "state", "font", "chakra")
    g.SetFont("s8 bold c" acc, F)
    g.AddText("x22 y" (bottom + 56) " w96 h30 +0x200", "FONT  //")
    for fo in Fonts {
        on := (fo[1] = font)
        g.SetFont("s9 bold c" (on ? panel : muted), F)
        b := g.AddText("x+8 yp w80 h30 +0x200 +Center Background" (on ? acc : light), fo[2])
        b.OnEvent("Click", SetHudFont.Bind(fo[1]))
    }

    ; Deck look. AUTO = the Cyber look for every theme; the others force one look.
    look := IniRead(StateIni, "state", "look", "auto")
    g.SetFont("s8 bold c" acc, F)
    g.AddText("x22 y" (bottom + 94) " w96 h30 +0x200", "FILES  //")
    for lo in Looks {
        on := (lo[1] = look)
        g.SetFont("s9 bold c" (on ? panel : muted), F)
        b := g.AddText("x+8 yp w80 h30 +0x200 +Center Background" (on ? acc : light), lo[2])
        b.OnEvent("Click", SetLook.Bind(lo[1]))
    }

    ; Corner brackets around the whole panel.
    W := 2 * 22 + 2 * RowW + ColGap, H := bottom + 94 + 30 + 20, L := 30, T := 3, o := 6
    for c in [[o, o, 1, 1], [W - o, o, -1, 1], [o, H - o, 1, -1], [W - o, H - o, -1, -1]] {
        hx := c[3] = 1 ? c[1] : c[1] - L
        vy := c[4] = 1 ? c[2] : c[2] - L
        g.AddText("x" hx " y" (c[4] = 1 ? c[2] : c[2] - T) " w" L " h" T " Background" acc)
        g.AddText("x" (c[3] = 1 ? c[1] : c[1] - T) " y" vy " w" T " h" L " Background" acc)
    }
    g.OnEvent("Escape", (g) => g.Destroy())
    Picker := g
    g.Show("Center w" W " h" H)
}

ApplyAndClose(id, *) {
    global Picker
    Picker.Destroy(), Picker := ""
    prev := IniRead(StateIni, "state", "current", "")
    if (id = "original")
        RestoreOriginal()
    else
        ApplyTheme(id)
    IniWrite(id, StateIni, "state", "current")
    ; Tell HudFrame (and anything else listening) to restyle now.
    DllCall("PostMessageW", "Ptr", 0xFFFF, "UInt", DllCall("RegisterWindowMessage", "Str", "ThemePickerChanged", "UInt"), "Ptr", 0, "Ptr", 0)
    ; Deck reads the theme id at start only for the Acid retro extras (scan lines, glitch): restart it when Acid comes or goes.
    if ((prev = "hud-acid") != (id = "hud-acid"))
        RestartFiles()
}

IsHudTheme(id) => SubStr(id, 1, 4) = "hud-"

; FILES row: force a Deck look ("auto" = Cyber for every theme). Files reads it at start.
SetLook(key, *) {
    global Picker
    if (key = "auto") {
        try IniDelete(StateIni, "state", "look")
    } else {
        IniWrite(key, StateIni, "state", "look")
    }
    RestartFiles()
    if Picker {
        Picker.Destroy(), Picker := ""
        ShowPicker()
    }
}

; Closes our Deck build (not the Store Files) and reopens it if it was running.
RestartFiles() {
    pids := Map()
    for hwnd in WinGetList("ahk_exe Files.exe") {
        try {
            pid := WinGetPID(hwnd)
            if !InStr(ProcessGetPath(pid), "files-layout") && !InStr(ProcessGetPath(pid), "deck-app\layout")
                continue
            pids[pid] := true
            WinClose(hwnd)
        }
    }
    if !pids.Count
        return
    for pid in pids {
        if !ProcessWaitClose(pid, 15)
            ProcessClose(pid)
    }
    LaunchFiles()
}

; Opens Deck. Right after an Explorer restart the shell can refuse shell:AppsFolder ("Not implemented"):
; retry for a few seconds, then go through explorer.exe.
LaunchFiles() {
    Loop 5 {
        try {
            Run("shell:AppsFolder\Deck_ykqwq8d6ps0ag!App")
            return
        }
        Sleep(1000)
    }
    Run('explorer.exe "shell:AppsFolder\Deck_ykqwq8d6ps0ag!App"')
}

ApplyTheme(id) {
    light := IniRead(ThemesIni, id, "mode") = "light"
    accent := IniRead(ThemesIni, id, "accent")
    menu := IniRead(ThemesIni, id, "menu")
    pers := "HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
    dwm := "HKCU\Software\Microsoft\Windows\DWM"
    acc := "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Accent"

    ; Light or dark mode for apps and for Windows itself.
    RegWrite(light ? 1 : 0, "REG_DWORD", pers, "AppsUseLightTheme")
    RegWrite(light ? 1 : 0, "REG_DWORD", pers, "SystemUsesLightTheme")
    ; Accent color on Start and taskbar only works in dark mode.
    RegWrite(light ? 0 : 1, "REG_DWORD", pers, "ColorPrevalence")
    ; Accent color: shades for Start/taskbar, plus title bars and window borders.
    RegWrite(IniRead(ThemesIni, id, "palette"), "REG_BINARY", acc, "AccentPalette")
    RegWrite(ToAbgr(accent), "REG_DWORD", acc, "AccentColorMenu")
    RegWrite(ToAbgr(menu), "REG_DWORD", acc, "StartColorMenu")
    RegWrite(ToAbgr(accent), "REG_DWORD", dwm, "AccentColor")
    RegWrite(0xC4000000 | Integer("0x" accent), "REG_DWORD", dwm, "ColorizationColor")
    RegWrite(0xC4000000 | Integer("0x" accent), "REG_DWORD", dwm, "ColorizationAfterglow")
    RegWrite(1, "REG_DWORD", dwm, "ColorPrevalence")
    RegWrite(0, "REG_DWORD", "HKCU\Control Panel\Desktop", "AutoColorization")

    RegWrite("10", "REG_SZ", "HKCU\Control Panel\Desktop", "WallpaperStyle")  ; 10 = fill
    list := WallpaperList(id)
    i := IniRead(StateIni, "wallpaper", id, 1)
    SetWallpaper(list[(i >= 1 && i <= list.Length) ? i : 1])
    SetTerminalScheme(IniRead(ThemesIni, id, "terminal"))
    TellWindowsColorsChanged()
    SetFileIcons(id)
    CopyAppIcons(id)
    SetExplorerArt(id)
    SetIconPack(id)
}

; File Explorer's top-area art (make_explorer_art.py). Explorer loads it at start,
; and every theme switch restarts Explorer.
SetExplorerArt(id) {
    src := A_ScriptDir "\explorer-art\" (DirExist(A_ScriptDir "\explorer-art\" id) ? id : "none")
    DirCreate(A_ScriptDir "\explorer-art\active")
    try FileCopy(src "\*.png", A_ScriptDir "\explorer-art\active\", 1)
}

; HUD themes: text, image, media, zip and ini files get the theme's HUD icons
; (file_icons.py, per-user registry). Other themes get the original icons back.
SetFileIcons(id) {
    files := A_ScriptDir "\icons\" id "\files"
    RunWait('py "' A_ScriptDir '\file_icons.py" ' ((id != "" && DirExist(files)) ? 'set "' files '"' : "restore"), , "Hide")
}

; App shortcuts point at appicons\active (see app_icons.ps1). HUD themes also
; have a <id>-color set, used when the picker's icon style is "Color".
CopyAppIcons(id) {
    src := A_ScriptDir "\appicons\" id
    if (IniRead(StateIni, "state", "icons", "accent") = "color" && DirExist(src "-color"))
        src .= "-color"
    DirCreate(A_ScriptDir "\appicons\active")
    try FileCopy(src "\*.ico", A_ScriptDir "\appicons\active\", 1)
}

SetIconStyle(opt, *) {
    IniWrite(opt, StateIni, "state", "icons")
    id := IniRead(StateIni, "state", "current", "")
    if (id != "" && id != "original") {
        CopyAppIcons(id)
        RestartExplorer()  ; Windows keeps the old icons cached until the cache is cleared
    }
    ShowPicker()  ; redraw with the new selection
}

; "HUD Face" is the chosen font, renamed by make_fonts.py. Bahnschrift needs no copy:
; with HUD Face missing, Explorer's style falls back to it.
HudFont() => IniRead(StateIni, "state", "font", "chakra") = "bahnschrift" ? "Bahnschrift" : "HUD Face"

SetHudFont(key, *) {
    IniWrite(key, StateIni, "state", "font")
    InstallHudFont(key)
    RestartExplorer()  ; Explorer reads fonts at start
    DllCall("PostMessageW", "Ptr", 0xFFFF, "UInt", DllCall("RegisterWindowMessage", "Str", "ThemePickerChanged", "UInt"), "Ptr", 0, "Ptr", 0)
    ; A running process keeps the old font's glyph table for "HUD Face" and draws
    ; gibberish with the new one, so the finder and the picker restart.
    DllCall("PostMessageW", "Ptr", 0xFFFF, "UInt", DllCall("RegisterWindowMessage", "Str", "HudFontChanged", "UInt"), "Ptr", 0, "Ptr", 0)
    Run('"' A_AhkPath '" /restart "' A_ScriptFullPath '" show')
    ExitApp()
}

; Per-user font install: copy to the user font folder, register it, tell running apps.
InstallHudFont(key) {
    dir := EnvGet("LOCALAPPDATA") "\Microsoft\Windows\Fonts"
    reg := "HKCU\Software\Microsoft\Windows NT\CurrentVersion\Fonts"
    for style in ["", " Bold"] {
        old := RegRead(reg, "HUD Face" style " (TrueType)", "")
        if (old = "")
            continue
        DllCall("RemoveFontResourceW", "Str", old)
        RegDelete(reg, "HUD Face" style " (TrueType)")
        try FileDelete(old)
    }
    if (key != "bahnschrift") {
        DirCreate(dir)
        for style in ["regular", "bold"] {
            dst := dir "\HUDFace-" key "-" style ".ttf"
            try FileCopy(A_ScriptDir "\fonts\hud\" key "-" style ".ttf", dst, 1)
            DllCall("AddFontResourceW", "Str", dst)
            RegWrite(dst, "REG_SZ", reg, "HUD Face" (style = "bold" ? " Bold" : "") " (TrueType)")
        }
    }
    DllCall("SendMessageTimeoutW", "Ptr", 0xFFFF, "UInt", 0x1D, "Ptr", 0, "Ptr", 0, "UInt", 2, "UInt", 1000, "Ptr*", 0)  ; WM_FONTCHANGE
}

RestoreOriginal() {
    for f in ["personalize", "dwm", "accent", "desktop"]
        RunWait('reg import "' BackupDir '\' f '.reg"', , "Hide")
    SetWallpaper(RegRead("HKCU\Control Panel\Desktop", "WallPaper", ""))
    SetTerminalScheme("Campbell")
    TellWindowsColorsChanged()
    SetFileIcons("")
    SetExplorerArt("none")
    SetIconPack("")
}

; Points the Windhawk Resource Redirect mod at the theme's icon pack
; (icons\<id>\<pack>\theme.ini) by rewriting icons\active.ini with full paths.
; Our own "HUD Folders" pack wins when the theme has one; otherwise the first
; pack found (a downloaded niivu/Papirus pack) is used.
; Explorer only reads it at start, so restart Explorer when the pack changes.
SetIconPack(id) {
    text := "[redirections]`n"
    if (id != "") {
        own := A_ScriptDir "\icons\" id "\HUD Folders\theme.ini"
        Loop Files FileExist(own) ? own : A_ScriptDir "\icons\" id "\theme.ini", "R" {
            for line in StrSplit(FileRead(A_LoopFileFullPath), "`n", "`r")
                if InStr(line, "=.\")
                    text .= StrReplace(line, "=.\", "=" A_LoopFileDir "\") "`n"
            break
        }
    }
    if FileExist(IconsIni) && FileRead(IconsIni) = text
        return
    f := FileOpen(IconsIni, "w", "UTF-16")
    f.Write(text), f.Close()
    RestartExplorer()
}

RestartExplorer() {
    ; Remember open folders (one entry per tab) to reopen them afterwards.
    folders := []
    try for w in ComObject("Shell.Application").Windows
        try folders.Push(w.Document.Folder.Self.Path)
    RunWait("taskkill /f /im explorer.exe", , "Hide")
    ; Old icons stay in the cache unless it is cleared while Explorer is down.
    Loop Files EnvGet("LOCALAPPDATA") "\Microsoft\Windows\Explorer\iconcache*.db"
        try FileDelete(A_LoopFileFullPath)
    Run("explorer.exe")
    if !folders.Length || !WinWait("ahk_class Shell_TrayWnd", , 15)
        return
    Sleep(1000)  ; let the shell finish starting
    for path in folders
        try Run('explorer.exe "' path '"')
}

; All wallpapers for a theme, in file-name order. A relative wallpapers= path
; (as written by the release packer) is taken from the picker's own folder.
WallpaperList(id) {
    list := []
    dir := IniRead(ThemesIni, id, "wallpapers")
    if !InStr(dir, ":")
        dir := A_ScriptDir "\" dir
    Loop Files dir "\*.jpg"
        list.Push(A_LoopFileFullPath)
    return list
}

; Shows the next wallpaper of the current theme and remembers it.
NextWallpaper() {
    id := IniRead(StateIni, "state", "current", "")
    if (id = "" || id = "original")
        return
    list := WallpaperList(id)
    i := Mod(IniRead(StateIni, "wallpaper", id, 1), list.Length) + 1
    IniWrite(i, StateIni, "wallpaper", id)
    SetWallpaper(list[i])
}

; "rrggbb" -> 0xFFbbggrr, the byte order Windows stores accent colors in.
ToAbgr(hex) {
    c := Integer("0x" hex)
    return 0xFF000000 | ((c & 0xFF) << 16) | (c & 0xFF00) | ((c >> 16) & 0xFF)
}

SetWallpaper(path) {
    ; SPI_SETDESKWALLPAPER, save to profile and notify.
    DllCall("SystemParametersInfoW", "UInt", 0x14, "UInt", 0, "Str", path, "UInt", 3)
}

SetTerminalScheme(name) {
    if !FileExist(WtSettings)
        return
    text := FileRead(WtSettings, "UTF-8")
    text := RegExReplace(text, '"colorScheme"\s*:\s*"[^"]*"', '"colorScheme": "' name '"', , 1)
    f := FileOpen(WtSettings, "w", "UTF-8-RAW")
    f.Write(text), f.Close()
}

TellWindowsColorsChanged() {
    for what in ["ImmersiveColorSet", "WindowsThemeElement"]
        DllCall("SendMessageTimeoutW", "Ptr", 0xFFFF, "UInt", 0x1A, "Ptr", 0, "Str", what
            , "UInt", 2, "UInt", 1000, "Ptr*", 0)
}
