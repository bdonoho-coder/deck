param([int]$ProcId, [int]$X, [int]$Y, [int]$Clicks = -5)
# Scrolls the mouse wheel at a point relative to the window (negative = down).
Add-Type @'
using System; using System.Runtime.InteropServices;
public class Wh { [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out R r);
[DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
[DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
[DllImport("user32.dll")] public static extern void mouse_event(int f, int x, int y, int d, int e);
public struct R { public int L, T, Ri, B; } }
'@
$h = (Get-Process -Id $ProcId).MainWindowHandle
[Wh]::SetForegroundWindow($h) | Out-Null
Start-Sleep -Milliseconds 300
$r = New-Object Wh+R; [Wh]::GetWindowRect($h, [ref]$r) | Out-Null
[Wh]::SetCursorPos($r.L + $X, $r.T + $Y) | Out-Null
for ($i = 0; $i -lt [Math]::Abs($Clicks); $i++) {
    [Wh]::mouse_event(0x800, 0, 0, [Math]::Sign($Clicks) * 120, 0)
    Start-Sleep -Milliseconds 60
}
