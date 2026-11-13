#Requires AutoHotkey v2.0
#SingleInstance Force
Persistent

; Gives every top-level window square corners and a thin outline in the
; current theme's accent color (Windows 11 DWM attributes). Follows theme
; changes made with the picker; "Original" puts Windows' defaults back.

global StateIni := A_ScriptDir "\current.ini"
global ThemesIni := A_ScriptDir "\themes.ini"
global Border := -1, Corner := 0, StateTime := ""
global Hud := false, Accent := 0, Dark := 0, Overlays := Map()
global FontColl := 0, FontName := "Bahnschrift"

DllCall("LoadLibrary", "Str", "gdiplus")
si := Buffer(24, 0), NumPut("UInt", 1, si)
DllCall("gdiplus\GdiplusStartup", "Ptr*", &GdipToken := 0, "Ptr", si, "Ptr", 0)

DllCall("RegisterShellHookWindow", "Ptr", A_ScriptHwnd)
OnMessage(DllCall("RegisterWindowMessage", "Str", "SHELLHOOK", "UInt"), OnShell)
; Explorer restarts (icon pack changes) drop the shell hook: hook again, restyle all.
OnMessage(DllCall("RegisterWindowMessage", "Str", "TaskbarCreated", "UInt"), Rehook)

Rehook(*) {
    DllCall("DeregisterShellHookWindow", "Ptr", A_ScriptHwnd)
    DllCall("RegisterShellHookWindow", "Ptr", A_ScriptHwnd)
    for hwnd in WinGetList()
        Style(hwnd)
}
; The picker broadcasts this message right after a theme change.
OnMessage(DllCall("RegisterWindowMessage", "Str", "ThemePickerChanged", "UInt"), ThemeChanged)
CheckTheme()
SetTimer(CheckTheme, 2000)  ; backup in case a message is missed

ThemeChanged(*) {
    global StateTime := ""  ; force a reload even within the same second
    SetTimer(CheckTheme, -1)
}
SetTimer(TrackFrames, 30)

; Reads the theme when current.ini changes, then restyles all windows.
CheckTheme() {
    global Border, Corner, StateTime, Hud, Accent, Dark
    t := FileExist(StateIni) ? FileGetTime(StateIni) : ""
    if (t = StateTime)
        return
    StateTime := t
    id := IniRead(StateIni, "state", "current", "")
    if (id = "" || id = "original") {
        Border := 0xFFFFFFFF, Corner := 0  ; DWMWA_COLOR_DEFAULT, DWMWCP_DEFAULT
    } else {
        c := Integer("0x" IniRead(ThemesIni, id, "accent", "888888"))
        Border := ((c & 0xFF) << 16) | (c & 0xFF00) | ((c >> 16) & 0xFF)  ; RGB -> COLORREF
        Corner := 1  ; DWMWCP_DONOTROUND
    }
    ; HUD themes also get the panel frame overlay on Explorer windows.
    Hud := (SubStr(id, 1, 4) = "hud-")
    if Hud {
        Accent := 0xFF000000 | Integer("0x" IniRead(ThemesIni, id, "accent"))
        Dark := 0xFF000000 | Integer("0x" IniRead(ThemesIni, id, "bg_dark"))
    }
    LoadFont()
    for target, ov in Overlays
        ov.gui.Destroy()
    Overlays.Clear()
    for hwnd in WinGetList()
        Style(hwnd)
}

; ---------- HUD frame overlay (route B) ----------
; One click-through layered window per tracked window, owned by it so it stays
; just above it in z-order. Everything is drawn outside the window's edges.
; Only these window classes get one (no browsers or games: a frame would get in the way).

global M := 34, TabH := 24  ; overlay margin around the window, tab height
global Kinds := Map(
    "CabinetWClass", "EXPLORER",
    "CASCADIA_HOSTING_WINDOW_CLASS", "TERMINAL",
    "ConsoleWindowClass", "CONSOLE",
    "Notepad", "NOTEPAD",
    "TaskManagerWindow", "TASKS",
    "ApplicationFrameWindow", "SYSTEM",  ; Settings, Calculator, Photos and other built-in apps
    "WinUIDesktopWin32WindowClass ahk_exe Files.exe", "FILES")  ; Files app; other WinUI apps share the class

TrackFrames() {
    seen := Map()
    if Hud {
        for cls, kind in Kinds
            for target in WinGetList("ahk_class " cls) {
                seen[target] := true
                try UpdateFrame(target, kind)
                catch as e
                    FileAppend(e.Message " line " e.Line " " e.What "`n", A_ScriptDir "\hudframe-err.log")
            }
    }
    for target, ov in Overlays.Clone()
        if !seen.Has(target) {
            ov.gui.Destroy()
            Overlays.Delete(target)
        }
}

UpdateFrame(target, kind) {
    DllCall("dwmapi\DwmGetWindowAttribute", "Ptr", target, "UInt", 14, "Int*", &cloaked := 0, "UInt", 4)
    visible := DllCall("IsWindowVisible", "Ptr", target) && !cloaked && WinGetMinMax(target) = 0
    if !Overlays.Has(target) {
        if !visible  ; many hidden helper windows share these classes: only frame real ones
            return
        g := Gui("-Caption +ToolWindow +E0x080800A0")  ; layered, transparent, noactivate, toolwindow
        g.Show("NA x0 y0 w1 h1")
        DllCall("SetWindowLongPtr", "Ptr", g.Hwnd, "Int", -8, "Ptr", target)  ; owner = tracked window
        ; Code label with the lowest free number for this kind (the window shows its own title).
        n := 1
        while HasNumber(kind, n)
            n++
        Overlays[target] := {gui: g, x: 0, y: 0, w: 0, h: 0, kind: kind, n: n, title: kind "  //  " Format("{:02}", n), shown: true}
    }
    ov := Overlays[target]
    if !visible {
        if ov.shown
            ov.gui.Hide(), ov.shown := false
        return
    }
    rc := Buffer(16)  ; visible frame, without the invisible resize border
    DllCall("dwmapi\DwmGetWindowAttribute", "Ptr", target, "UInt", 9, "Ptr", rc, "UInt", 16)
    x := NumGet(rc, 0, "Int"), y := NumGet(rc, 4, "Int")
    w := NumGet(rc, 8, "Int") - x, h := NumGet(rc, 12, "Int") - y
    if (w != ov.w || h != ov.h || !ov.shown) {
        ov.w := w, ov.h := h, ov.x := x, ov.y := y
        ; Caption buttons (minimize, maximize, close), in frame coordinates, for their color marks.
        btn := Buffer(16), win := Buffer(16)
        ov.bx := 0
        if !DllCall("dwmapi\DwmGetWindowAttribute", "Ptr", target, "UInt", 5, "Ptr", btn, "UInt", 16)
            && DllCall("GetWindowRect", "Ptr", target, "Ptr", win) {
            off := x - NumGet(win, 0, "Int")  ; invisible resize border
            ov.bx := NumGet(btn, 0, "Int") - off, ov.bw := (NumGet(btn, 8, "Int") - NumGet(btn, 0, "Int")) / 3
        }
        Paint(ov)
    } else if (x != ov.x || y != ov.y) {
        ov.x := x, ov.y := y
        DllCall("SetWindowPos", "Ptr", ov.gui.Hwnd, "Ptr", 0, "Int", x - M, "Int", y - M, "Int", 0, "Int", 0, "UInt", 0x15)  ; NOSIZE|NOZORDER|NOACTIVATE
    }
    if !ov.shown
        ov.gui.Show("NA"), ov.shown := true
    ; Keep the overlay directly above its own window, never above windows in front of it.
    prev := DllCall("GetWindow", "Ptr", target, "UInt", 3, "Ptr")  ; GW_HWNDPREV
    if (prev && DllCall("GetWindowLongPtr", "Ptr", prev, "Int", -20, "Ptr") & 0x8)  ; prev is always-on-top
        prev := 0  ; HWND_TOP: top of the normal windows
    if (prev != ov.gui.Hwnd)
        DllCall("SetWindowPos", "Ptr", ov.gui.Hwnd, "Ptr", prev ? prev : 0, "Int", 0, "Int", 0, "Int", 0, "Int", 0, "UInt", 0x13)  ; NOSIZE|NOMOVE|NOACTIVATE
}

HasNumber(kind, n) {
    for target, ov in Overlays
        if (ov.kind = kind && ov.n = n)
            return true
    return false
}

Paint(ov) {
    W := ov.w + 2 * M, H := ov.h + 2 * M
    hdc := DllCall("CreateCompatibleDC", "Ptr", 0, "Ptr")
    bi := Buffer(40, 0)
    NumPut("UInt", 40, "Int", W, "Int", -H, "UShort", 1, "UShort", 32, bi)
    hbm := DllCall("CreateDIBSection", "Ptr", hdc, "Ptr", bi, "UInt", 0, "Ptr*", 0, "Ptr", 0, "UInt", 0, "Ptr")
    old := DllCall("SelectObject", "Ptr", hdc, "Ptr", hbm, "Ptr")
    DllCall("gdiplus\GdipCreateFromHDC", "Ptr", hdc, "Ptr*", &g := 0)
    DllCall("gdiplus\GdipSetSmoothingMode", "Ptr", g, "Int", 4)
    DllCall("gdiplus\GdipSetTextRenderingHint", "Ptr", g, "Int", 4)
    DrawHud(g, ov, W, H)
    DllCall("gdiplus\GdipDeleteGraphics", "Ptr", g)
    pt := ((ov.x - M) & 0xFFFFFFFF) | ((ov.y - M) << 32)
    sz := W | (H << 32)
    DllCall("UpdateLayeredWindow", "Ptr", ov.gui.Hwnd, "Ptr", 0, "Int64*", pt, "Int64*", sz, "Ptr", hdc
        , "Int64*", 0, "UInt", 0, "UInt*", 0x01FF0000, "UInt", 2)  ; per-pixel alpha
    DllCall("SelectObject", "Ptr", hdc, "Ptr", old)
    DllCall("DeleteObject", "Ptr", hbm), DllCall("DeleteDC", "Ptr", hdc)
}

DrawHud(g, ov, W, H) {
    x0 := M, y0 := M, x1 := M + ov.w, y1 := M + ov.h
    ; Soft glow just outside the outline.
    for a in [[48, 3], [26, 7], [12, 12]]
        Rect(g, Alpha(Accent, a[1]), a[2], x0 - a[2] / 2, y0 - a[2] / 2, ov.w + a[2], ov.h + a[2])
    ; Corner brackets.
    o := 7, L := 26
    for c in [[x0 - o, y0 - o, 1, 1], [x1 + o, y0 - o, -1, 1], [x0 - o, y1 + o, 1, -1], [x1 + o, y1 + o, -1, -1]] {
        if (c[2] < y0 && c[3] = 1)  ; top-left bracket sits under the tab
            continue
        Line(g, Accent, 2, c[1], c[2], c[1] + L * c[3], c[2])
        Line(g, Accent, 2, c[1], c[2], c[1], c[2] + L * c[4])
    }
    ; Tab with angled cut, title in caps, small square marker.
    font := MakeFont(13)
    tw := Max(TextWidth(g, ov.title, font), 40) + 46
    Poly(g, Accent, [x0, y0 - TabH, x0 + tw, y0 - TabH, x0 + tw + TabH, y0 + 1, x0, y0 + 1])
    Fill(g, Dark, x0 + 10, y0 - TabH + 8, 8, 8)
    Text(g, ov.title, font, Dark, x0 + 26, y0 - TabH + 4)
    ; Scale line next to the tab, with a bright segment at the end.
    lx := x0 + tw + TabH + 14
    ; Over the caption buttons the scale line turns into fixed color marks, whatever
    ; the theme: green = minimize, amber = maximize, red = close.
    bx := (ov.bx > 0 && ov.bx < ov.w) ? x0 + ov.bx : x1 - 70
    if (bx - 6 > lx)
        Line(g, Alpha(Accent, 90), 1, lx, y0 - 7, bx - 6, y0 - 7)
    if (ov.bx > 0 && ov.bx < ov.w) {
        for i, col in [0xFF46E08A, 0xFFFFA62B, 0xFFFF4040] {
            sx := bx + (i - 1) * ov.bw
            Line(g, col, 3, sx + 6, y0 - 7, sx + ov.bw - 6, y0 - 7)
            Fill(g, col, sx + ov.bw / 2 - 3, y0 - 17, 6, 6)
        }
    } else
        Line(g, Accent, 3, x1 - 64, y0 - 7, x1, y0 - 7)
    ; Code label under the bottom-right corner.
    small := MakeFont(11)
    Fill(g, Accent, x1 - 92, y1 + 10, 6, 6)
    Text(g, "WIN " Format("{:02}", Mod(ov.w // 10, 100)) "  /  SYS", small, Alpha(Accent, 220), x1 - 80, y1 + 5)
    DllCall("gdiplus\GdipDeleteFont", "Ptr", font), DllCall("gdiplus\GdipDeleteFont", "Ptr", small)
}

Alpha(argb, a) => (a << 24) | (argb & 0xFFFFFF)

Line(g, argb, w, x1, y1, x2, y2) {
    DllCall("gdiplus\GdipCreatePen1", "UInt", argb, "Float", w, "Int", 2, "Ptr*", &pen := 0)
    DllCall("gdiplus\GdipDrawLine", "Ptr", g, "Ptr", pen, "Float", x1, "Float", y1, "Float", x2, "Float", y2)
    DllCall("gdiplus\GdipDeletePen", "Ptr", pen)
}

Rect(g, argb, w, x, y, rw, rh) {
    DllCall("gdiplus\GdipCreatePen1", "UInt", argb, "Float", w, "Int", 2, "Ptr*", &pen := 0)
    DllCall("gdiplus\GdipDrawRectangle", "Ptr", g, "Ptr", pen, "Float", x, "Float", y, "Float", rw, "Float", rh)
    DllCall("gdiplus\GdipDeletePen", "Ptr", pen)
}

Fill(g, argb, x, y, rw, rh) {
    DllCall("gdiplus\GdipCreateSolidFill", "UInt", argb, "Ptr*", &br := 0)
    DllCall("gdiplus\GdipFillRectangle", "Ptr", g, "Ptr", br, "Float", x, "Float", y, "Float", rw, "Float", rh)
    DllCall("gdiplus\GdipDeleteBrush", "Ptr", br)
}

Poly(g, argb, xy) {
    pts := Buffer(4 * xy.Length)
    for i, v in xy
        NumPut("Float", v, pts, (i - 1) * 4)
    DllCall("gdiplus\GdipCreateSolidFill", "UInt", argb, "Ptr*", &br := 0)
    DllCall("gdiplus\GdipFillPolygon", "Ptr", g, "Ptr", br, "Ptr", pts, "Int", xy.Length // 2, "Int", 0)
    DllCall("gdiplus\GdipDeleteBrush", "Ptr", br)
}

; The picker's font (make_fonts.py), loaded from its file: GDI+ doesn't see
; fonts installed after it started. Bahnschrift comes from the system.
LoadFont() {
    global FontColl, FontName
    if FontColl
        DllCall("gdiplus\GdipDeletePrivateFontCollection", "Ptr*", &FontColl)
    FontColl := 0, FontName := "Bahnschrift"
    key := IniRead(StateIni, "state", "font", "chakra")
    file := A_ScriptDir "\fonts\hud\" key "-bold.ttf"
    if (key = "bahnschrift" || !FileExist(file))
        return
    DllCall("gdiplus\GdipNewPrivateFontCollection", "Ptr*", &FontColl)
    DllCall("gdiplus\GdipPrivateAddFontFile", "Ptr", FontColl, "WStr", file)
    FontName := "HUD Face"
}

MakeFont(px) {
    DllCall("gdiplus\GdipCreateFontFamilyFromName", "WStr", FontName, "Ptr", FontColl, "Ptr*", &fam := 0)
    DllCall("gdiplus\GdipCreateFont", "Ptr", fam, "Float", px, "Int", 1, "Int", 2, "Ptr*", &f := 0)  ; bold, pixels
    DllCall("gdiplus\GdipDeleteFontFamily", "Ptr", fam)
    return f
}

TextWidth(g, s, font) {
    lay := Buffer(16, 0), box := Buffer(16, 0)
    NumPut("Float", 2000, lay, 8), NumPut("Float", 100, lay, 12)
    DllCall("gdiplus\GdipMeasureString", "Ptr", g, "WStr", s, "Int", -1, "Ptr", font, "Ptr", lay, "Ptr", 0, "Ptr", box, "Ptr", 0, "Ptr", 0)
    return NumGet(box, 8, "Float")
}

Text(g, s, font, argb, x, y) {
    lay := Buffer(16, 0)
    NumPut("Float", x, "Float", y, "Float", 2000, "Float", 100, lay)
    DllCall("gdiplus\GdipCreateSolidFill", "UInt", argb, "Ptr*", &br := 0)
    DllCall("gdiplus\GdipDrawString", "Ptr", g, "WStr", s, "Int", -1, "Ptr", font, "Ptr", lay, "Ptr", 0, "Ptr", br)
    DllCall("gdiplus\GdipDeleteBrush", "Ptr", br)
}

OnShell(wParam, lParam, *) {
    if (wParam = 1 || wParam = 4 || wParam = 0x8004)  ; window created / activated
        Style(lParam)
}

Style(hwnd) {
    try {
        if !(WinGetStyle(hwnd) & 0xC00000)  ; WS_CAPTION: real app windows only
            return
        DllCall("dwmapi\DwmSetWindowAttribute", "Ptr", hwnd, "UInt", 33, "UInt*", Corner, "UInt", 4)
        DllCall("dwmapi\DwmSetWindowAttribute", "Ptr", hwnd, "UInt", 34, "UInt*", Border, "UInt", 4)
    }
}
