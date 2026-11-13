; pick3.ahk <row> <col>  - open the Deck theme picker (Win+T), glide the mouse to a theme row and click it.
; Row layout from ShowPicker(): top 74, label 20, rows 40 high + 6 gap, column x 22, width 300, column gap 24.
#Requires AutoHotkey v2
#SingleInstance Off
CoordMode "Mouse", "Screen"
SendLevel 1
SetControlDelay -1      ; don't wait on the picker after the click: ApplyAndClose destroys it at once
row := Integer(A_Args[1]), col := A_Args.Length >= 2 ? Integer(A_Args[2]) : 1
if WinExist("Theme Picker ahk_class AutoHotkeyGUI") && WinGetStyle("Theme Picker ahk_class AutoHotkeyGUI") & 0x10000000 {
    Send "{Esc}"
    Sleep 400
}
Send "#t"
if !WinWait("Theme Picker ahk_class AutoHotkeyGUI", , 4) {
    FileAppend "picker not found`n", "*"
    ExitApp 1
}
WinWaitActive "Theme Picker ahk_class AutoHotkeyGUI", , 0.5   ; often never active over Deck: don't wait long
Sleep 450
WinGetPos &wx, &wy, , , "Theme Picker ahk_class AutoHotkeyGUI"
x := wx + 22 + (col - 1) * 324 + 120
y := wy + 74 + 20 + (row - 1) * 46 + 20
MouseMove x, y, 10          ; glide so the viewer can follow the cursor (about 0.6 s across the screen)
Sleep 150
; Post the click straight to the picker's own control (client coords): overlays can't swallow it.
cx := 22 + (col - 1) * 324 + 120, cy := 74 + 20 + (row - 1) * 46 + 20
SetTimer () => ExitApp(0), -400     ; hard exit: the click destroys the picker and ControlClick can hang on it
try ControlClick "X" cx " Y" cy, "Theme Picker ahk_class AutoHotkeyGUI", , "Left", 1, "Pos"
catch   ; the picker is destroyed by its own click handler; a late error here must not open a dialog
    ExitApp 0
ExitApp 0   ; no stdout write: launched hidden there is no console and FileAppend "*" throws a dialog
