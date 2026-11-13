param([int]$ProcId, [int]$X, [int]$Y, [ValidateSet("move", "right")][string]$Do = "move")
# Moves the mouse to a point relative to the window, and right-clicks there with -Do right.
Add-Type @'
using System; using System.Runtime.InteropServices;
public class Ms { [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out R r);
[DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
[DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
[DllImport("user32.dll")] public static extern void mouse_event(int f, int x, int y, int d, int e);
public struct R { public int L, T, Ri, B; } }
'@
$h = (Get-Process -Id $ProcId).MainWindowHandle
[Ms]::SetForegroundWindow($h) | Out-Null
Start-Sleep -Milliseconds 300
$r = New-Object Ms+R; [Ms]::GetWindowRect($h, [ref]$r) | Out-Null
[Ms]::SetCursorPos($r.L + $X - 6, $r.T + $Y) | Out-Null
Start-Sleep -Milliseconds 80
[Ms]::SetCursorPos($r.L + $X, $r.T + $Y) | Out-Null
for ($i = 0; $i -lt 3; $i++) { [Ms]::mouse_event(1, 1, 0, 0, 0); Start-Sleep -Milliseconds 40; [Ms]::mouse_event(1, -1, 0, 0, 0); Start-Sleep -Milliseconds 40 }  # real move input, so WinUI sees a hover
if ($Do -eq "right") { Start-Sleep -Milliseconds 100; [Ms]::mouse_event(8, 0, 0, 0, 0); [Ms]::mouse_event(16, 0, 0, 0, 0) }
