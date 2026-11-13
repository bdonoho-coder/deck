param([int]$ProcId, [int]$X, [int]$Y)
Add-Type @'
using System; using System.Runtime.InteropServices;
public class M { [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out R r);
[DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
[DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
[DllImport("user32.dll")] public static extern void mouse_event(int f, int x, int y, int d, int e);
public struct R { public int L, T, Ri, B; } }
'@
$h = (Get-Process -Id $ProcId).MainWindowHandle
[M]::SetForegroundWindow($h) | Out-Null
Start-Sleep -Milliseconds 300
$r = New-Object M+R; [M]::GetWindowRect($h, [ref]$r) | Out-Null
[M]::SetCursorPos($r.L + $X, $r.T + $Y) | Out-Null
Start-Sleep -Milliseconds 100
[M]::mouse_event(2, 0, 0, 0, 0); [M]::mouse_event(4, 0, 0, 0, 0)
