#Requires AutoHotkey v2.0
#SingleInstance Force

; Win + Space opens a themed finder: type part of a folder or app name, Enter
; opens it, Ctrl+Enter shows it in its parent folder, Up/Down pick, Esc closes.
; The index is rebuilt every 15 minutes; picks you use often rank higher.

global UsesIni := A_ScriptDir "\finder-uses.ini"
global Index := [], Results := [], Sel := 1, FinderGui := "", RowCtl := []
global RowCount := 8, Colors := Map()
global Home := EnvGet("USERPROFILE"), OneDrive := EnvGet("OneDrive")

BuildIndex()  ; ~0.5 s
SetTimer(BuildIndex, 15 * 60 * 1000)
OnMessage(0x6, OnActivate)  ; close when the finder loses focus
OnMessage(0x201, OnDragStart)  ; drag the finder by any empty spot
OnMessage(0x232, OnMoved)  ; WM_EXITSIZEMOVE: remember where it was dropped
; After a font switch the old glyph table for "HUD Face" stays in this process: restart.
OnMessage(DllCall("RegisterWindowMessage", "Str", "HudFontChanged", "UInt"), (*) => Reload())
global PosIni := A_ScriptDir "\finder-pos.ini"

#Space::ShowFinder()

#HotIf WinActive("Finder ahk_class AutoHotkeyGUI")
Up::MoveSel(-1)
Down::MoveSel(1)
Tab::MoveSel(1)
Enter::OpenSel(false)
^Enter::OpenSel(true)
#HotIf

; ---------- index ----------

BuildIndex() {
    global Index
    items := [], seen := Map()
    roots := [[Home, 2], [OneDrive, 3], [Home "\Downloads", 2], [Home "\modding", 3],
        ["B:\", 2], ["C:\Games", 2], ["C:\RetroBat", 2],
        ["C:\Program Files (x86)\Steam\steamapps\common", 1], ["B:\SteamLibrary\steamapps\common", 1]]
    for r in roots
        if (r[1] != "" && DirExist(r[1]))
            ScanDirs(r[1], r[2], items, seen)
    ; Pinned Quick access folders (skips the recent files mixed into that list).
    try for it in ComObject("Shell.Application").Namespace("shell:::{679f85cb-0220-4080-b29b-5540cc05aab6}").Items()
        if (SubStr(it.Path, 1, 2) != "\\" && DirExist(it.Path))
            AddItem(items, seen, it.Path, "dir", 2)
    ; Apps: Start menu and desktop shortcuts.
    for dir in [A_StartMenu, A_StartMenuCommon, A_Desktop, A_DesktopCommon]
        Loop Files dir "\*.lnk", "R"
            if !InStr(A_LoopFileName, "uninstall")
                AddItem(items, seen, A_LoopFileFullPath, "app", 0)
    Index := items
}

ScanDirs(dir, depth, items, seen) {
    static skip := "|appdata|node_modules|.git|$recycle.bin|system volume information|windows|"
    Loop Files dir "\*", "D" {
        if InStr(A_LoopFileAttrib, "H") || InStr(A_LoopFileAttrib, "S")
            || InStr(skip, "|" StrLower(A_LoopFileName) "|")
            continue
        AddItem(items, seen, A_LoopFileFullPath, "dir", 0)
        if (depth > 1)
            ScanDirs(A_LoopFileFullPath, depth - 1, items, seen)
    }
}

AddItem(items, seen, path, kind, bonus) {
    key := StrLower(path)
    if seen.Has(key) {
        items[seen[key]].bonus := Max(items[seen[key]].bonus, bonus)
        return
    }
    SplitPath(path, &name, , , &stem)
    name := (kind = "app") ? stem : name
    items.Push({name: name, lname: StrLower(name), path: path, lpath: key, kind: kind, bonus: bonus})
    seen[key] := items.Length
}

; ---------- search ----------

Search(query) {
    q := Trim(StrLower(query))
    lines := ""
    for i, it in Index {
        score := it.bonus + Min(IniRead(UsesIni, "uses", it.lpath, 0) * 6, 48)
        if (q != "") {
            for tok in StrSplit(q, " ") {
                if (tok = "")
                    continue
                if (p := InStr(it.lname, tok))
                    score += (p = 1) ? 40 : (InStr(" -_.(", SubStr(it.lname, p - 1, 1)) ? 30 : 18)
                else if InStr(it.lpath, tok)
                    score += 6
                else if IsSubsequence(tok, it.lname)
                    score += 4
                else {
                    score := -1
                    break
                }
            }
            if (score < 0)
                continue
            score += 20 - Min(StrLen(it.name), 40) / 2  ; prefer short, exact names
        } else if (score = 0)
            continue
        lines .= Format("{:06}", Round(score * 10) + 1000) "|" i "`n"
    }
    lines := Sort(RTrim(lines, "`n"), "R")
    out := []
    for line in StrSplit(lines, "`n") {
        if (line = "" || out.Length >= RowCount)
            break
        out.Push(Index[Integer(StrSplit(line, "|")[2])])
    }
    return out
}

IsSubsequence(needle, hay) {
    pos := 1
    Loop Parse needle {
        pos := InStr(hay, A_LoopField, , pos)
        if !pos
            return false
        pos++
    }
    return true
}

; ---------- window ----------

LoadColors() {
    global Colors
    ini := A_ScriptDir "\themes.ini"
    id := IniRead(A_ScriptDir "\current.ini", "state", "current", "")
    get(k, d) => (id != "" && id != "original") ? IniRead(ini, id, k, d) : d
    Colors := Map("bg", get("bg_dark", "1a1a1a"), "panel", get("bg_light", "262626"),
        "fg", get("fg", "e6e6e6"), "accent", get("accent", "4cc2ff"), "sel", get("selection", "333333"),
        "muted", "7a7a7a")
}

ShowFinder() {
    global FinderGui, RowCtl, Sel
    if IsObject(FinderGui) {
        CloseFinder()
        return
    }
    LoadColors()
    ; Font chosen in the picker: "HUD Face" (make_fonts.py) or Bahnschrift.
    F := IniRead(A_ScriptDir "\current.ini", "state", "font", "chakra") = "bahnschrift" ? "Bahnschrift" : "HUD Face"
    c := Colors, X := 22, BW := 680
    ; HUD panel: accent tab, accent rule, outlined search box, numbered rows, corner brackets.
    g := Gui("+AlwaysOnTop -Caption +ToolWindow", "Finder")
    g.BackColor := c["bg"]
    g.SetFont("s10 bold c" c["bg"], F)
    g.AddText("x" X " y18 w170 h24 +0x200 Background" c["accent"], "  ■  FIND  //  SYS")
    g.SetFont("s8 c" c["muted"], F)
    g.AddText("x" (X + BW - 260) " y24 w260 +Right", "INDEX  " Index.Length "  ITEMS")
    g.AddText("x" X " y48 w" BW " h1 Background" c["accent"])
    g.AddText("x" (X - 1) " y61 w" (BW + 2) " h44 Background" c["accent"])  ; 1 px outline behind the box
    g.SetFont("s16 c" c["fg"], F)
    box := g.AddEdit("x" X " y62 w" BW " h42 -E0x200 Background" c["panel"])
    ; Typing events can arrive while a search runs and get dropped, so search
    ; the box's current text shortly after the last keystroke instead.
    box.OnEvent("Change", (*) => SetTimer(SearchBox, -40))
    SearchBox() => IsObject(FinderGui) ? Refresh(box.Value) : 0
    RowCtl := []
    y := 116
    Loop RowCount {
        bar := g.AddText("x" (X - 10) " y" y " w4 h44 Background" c["bg"])  ; marks the selected row
        g.SetFont("s12 bold c" c["fg"], F)
        n := g.AddText("x" X " y" y " w" BW " h26 +0x200 Background" c["bg"])
        g.SetFont("s9 norm c" c["muted"], F)
        p := g.AddText("x" X " y" (y + 26) " w" BW " h18 Background" c["bg"])
        i := A_Index
        n.OnEvent("Click", ClickRow.Bind(i)), p.OnEvent("Click", ClickRow.Bind(i))
        RowCtl.Push([n, p, bar])
        y += 48
    }
    g.AddText("x" X " y" (y + 6) " w" BW " h1 Background" c["panel"])
    g.SetFont("s8 bold c" c["accent"], F)
    g.AddText("x" X " y" (y + 16) " w" BW, "ENTER OPEN   ·   CTRL+ENTER SHOW IN FOLDER   ·   ↑↓ PICK   ·   ESC CLOSE")
    W := BW + 2 * X, H := y + 44, L := 26, T := 3, o := 5
    for k in [[o, o, 1, 1], [W - o, o, -1, 1], [o, H - o, 1, -1], [W - o, H - o, -1, -1]] {
        hx := k[3] = 1 ? k[1] : k[1] - L
        vy := k[4] = 1 ? k[2] : k[2] - L
        g.AddText("x" hx " y" (k[4] = 1 ? k[2] : k[2] - T) " w" L " h" T " Background" c["accent"])
        g.AddText("x" (k[3] = 1 ? k[1] : k[1] - T) " y" vy " w" T " h" L " Background" c["accent"])
    }
    g.OnEvent("Escape", (*) => CloseFinder())
    FinderGui := g
    Refresh("")
    x := IniRead(PosIni, "pos", "x", ""), y := IniRead(PosIni, "pos", "y", "")
    onScreen := (x != "" && x >= SysGet(76) - 200 && x < SysGet(76) + SysGet(78) - 100
        && y >= SysGet(77) && y < SysGet(77) + SysGet(79) - 100)  ; virtual screen bounds
    g.Show((onScreen ? "x" x " y" y : "Center") " w" W " h" H)
    box.Focus()
}

; Clicks on empty space and plain labels reach the window itself; turn them into a title-bar drag.
OnDragStart(wParam, lParam, msg, hwnd) {
    if (IsObject(FinderGui) && hwnd = FinderGui.Hwnd)
        PostMessage(0xA1, 2, , FinderGui)  ; WM_NCLBUTTONDOWN, HTCAPTION
}

OnMoved(wParam, lParam, msg, hwnd) {
    if (IsObject(FinderGui) && hwnd = FinderGui.Hwnd) {
        WinGetPos(&x, &y, , , FinderGui)
        IniWrite(x, PosIni, "pos", "x"), IniWrite(y, PosIni, "pos", "y")
    }
}

Refresh(query) {
    global Results, Sel
    Results := Search(query), Sel := 1
    Paint()
}

Paint() {
    c := Colors
    for i, pair in RowCtl {
        it := (i <= Results.Length) ? Results[i] : ""
        on := (i = Sel && IsObject(it))
        bg := on ? c["sel"] : c["bg"]
        pair[1].Opt("Background" bg " c" (on ? c["accent"] : c["fg"]))
        pair[2].Opt("Background" bg)
        pair[3].Opt("Background" (on ? c["accent"] : c["bg"]))
        pair[1].Value := IsObject(it) ? "   " Format("{:02}", i) "   " (it.kind = "app" ? "▸ " : "▪ ") StrUpper(it.name) : ""
        pair[2].Value := IsObject(it) ? "              " it.path : ""
        pair[1].Redraw(), pair[2].Redraw(), pair[3].Redraw()  ; colored Text controls don't repaint on their own
    }
}

MoveSel(d) {
    global Sel
    if (Results.Length = 0)
        return
    Sel := Mod(Sel - 1 + d + Results.Length, Results.Length) + 1
    Paint()
}

ClickRow(i, *) {
    global Sel
    if (i <= Results.Length) {
        Sel := i
        OpenSel(false)
    }
}

OpenSel(showInFolder) {
    if (Sel > Results.Length)
        return
    it := Results[Sel]
    IniWrite(IniRead(UsesIni, "uses", it.lpath, 0) + 1, UsesIni, "uses", it.lpath)
    CloseFinder()
    try {
        if showInFolder
            Run('explorer.exe /select,"' it.path '"')
        else
            Run('"' it.path '"')
    }
}

CloseFinder() {
    global FinderGui
    if IsObject(FinderGui)
        FinderGui.Destroy()
    FinderGui := ""
}

OnActivate(wParam, lParam, msg, hwnd) {
    if (IsObject(FinderGui) && hwnd = FinderGui.Hwnd && (wParam & 0xFFFF) = 0)
        SetTimer(CloseFinder, -10)
}
