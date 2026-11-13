#Requires AutoHotkey v2.0
#SingleInstance Force

; Win + scroll wheel switches virtual desktops, wrapping around at the ends.
; Wheel up = previous desktop, wheel down = next desktop.
#WheelUp::SwitchDesktop(-1)
#WheelDown::SwitchDesktop(1)

SwitchDesktop(step) {
    static busy := false
    if busy
        return
    busy := true
    pos := DesktopPosition()  ; [index, count], index from 0
    target := Mod(pos[1] + step + pos[2], pos[2])
    if (Abs(target - pos[1]) > 1)
        WrapSlide(target - pos[1], step)
    else if (target != pos[1])
        Send step < 0 ? "#^{Left}" : "#^{Right}"
    Sleep 150
    busy := false
}

; Windows can only slide backwards across every desktop to wrap. Instead:
; cover the screen with a picture of it, jump behind the cover with animations
; off, picture the new desktop, then slide both pictures in the scroll direction.
WrapSlide(moves, step) {
    w := A_ScreenWidth, h := A_ScreenHeight
    oldPic := CaptureScreen(w, h)
    cover := PictureWindow(oldPic, 0, w, h)

    SetAnimations(false)
    Loop Abs(moves) {
        ; Read the desktop before sending: with animations off the switch
        ; lands at once, so reading afterwards would wait for nothing.
        before := CurrentDesktopId()
        Send moves < 0 ? "#^{Left}" : "#^{Right}"
        WaitForSwitch(before)
    }
    SetAnimations(true)
    Sleep 40  ; let the new desktop paint

    newPic := CaptureScreen(w, h)  ; the cover is excluded from capture
    incoming := PictureWindow(newPic, step * w, w, h)

    DllCall("winmm\timeBeginPeriod", "UInt", 1)
    start := A_TickCount, duration := 300
    Loop {
        t := Min((A_TickCount - start) / duration, 1)
        x := Round(-step * w * (1 - (1 - t) ** 3))  ; ease-out
        ; Move both pictures in one call so they stay joined.
        hdwp := DllCall("BeginDeferWindowPos", "Int", 2, "Ptr")
        hdwp := DllCall("DeferWindowPos", "Ptr", hdwp, "Ptr", cover.Hwnd, "Ptr", 0
            , "Int", x, "Int", 0, "Int", 0, "Int", 0, "UInt", 0x15, "Ptr")  ; NOSIZE|NOZORDER|NOACTIVATE
        hdwp := DllCall("DeferWindowPos", "Ptr", hdwp, "Ptr", incoming.Hwnd, "Ptr", 0
            , "Int", x + step * w, "Int", 0, "Int", 0, "Int", 0, "UInt", 0x15, "Ptr")
        DllCall("EndDeferWindowPos", "Ptr", hdwp)
        if (t >= 1)
            break
        Sleep 4
    }
    DllCall("winmm\timeEndPeriod", "UInt", 1)
    cover.Destroy(), incoming.Destroy()
}

; A borderless, click-through, always-on-top window showing a bitmap. Tool
; windows stay visible on every desktop, so it survives the switch.
PictureWindow(hbm, x, w, h) {
    g := Gui("+AlwaysOnTop -Caption +ToolWindow -DPIScale +E0x20")
    g.MarginX := 0, g.MarginY := 0
    g.AddPicture("x0 y0 w" w " h" h, "HBITMAP:" hbm)
    g.Show("NA x" x " y0 w" w " h" h)
    DllCall("SetWindowDisplayAffinity", "Ptr", g.Hwnd, "UInt", 0x11)  ; WDA_EXCLUDEFROMCAPTURE
    return g
}

CaptureScreen(w, h) {
    sdc := DllCall("GetDC", "Ptr", 0, "Ptr")
    mdc := DllCall("CreateCompatibleDC", "Ptr", sdc, "Ptr")
    hbm := DllCall("CreateCompatibleBitmap", "Ptr", sdc, "Int", w, "Int", h, "Ptr")
    old := DllCall("SelectObject", "Ptr", mdc, "Ptr", hbm, "Ptr")
    DllCall("BitBlt", "Ptr", mdc, "Int", 0, "Int", 0, "Int", w, "Int", h
        , "Ptr", sdc, "Int", 0, "Int", 0, "UInt", 0x40CC0020)  ; SRCCOPY | CAPTUREBLT
    DllCall("SelectObject", "Ptr", mdc, "Ptr", old)
    DllCall("DeleteDC", "Ptr", mdc)
    DllCall("ReleaseDC", "Ptr", 0, "Ptr", sdc)
    return hbm
}

; SPI_SETCLIENTAREAANIMATION, in memory only (not saved to the profile).
SetAnimations(on) {
    DllCall("SystemParametersInfoW", "UInt", 0x1043, "UInt", 0, "Ptr", on, "UInt", 2)
}

CurrentDesktopId() {
    return RegRead("HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VirtualDesktops"
        , "CurrentVirtualDesktop", "")
}

WaitForSwitch(before) {
    Loop 80 {  ; up to ~800 ms
        if (CurrentDesktopId() != before)
            return
        Sleep 10
    }
}

; Windows keeps the desktop IDs (16 bytes each) and the current one in the registry.
DesktopPosition() {
    key := "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\VirtualDesktops"
    try {
        ids := RegRead(key, "VirtualDesktopIDs")
        cur := RegRead(key, "CurrentVirtualDesktop")
    } catch
        return [0, 1]
    count := StrLen(ids) // 32
    Loop count
        if (SubStr(ids, (A_Index - 1) * 32 + 1, 32) = cur)
            return [A_Index - 1, count]
    return [0, count]
}
