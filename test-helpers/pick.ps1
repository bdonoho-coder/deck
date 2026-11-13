param([int]$Row, [int]$Col = 1)  # 1-based row; column 1 = STD themes, 2 = HUD themes
# Opens the theme picker with Win+T and clicks a theme row by screen position.
Add-Type @'
using System; using System.Runtime.InteropServices;
public class Pk { [DllImport("user32.dll")] public static extern IntPtr FindWindow(string c, string t);
[DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out R r);
[DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
[DllImport("user32.dll")] public static extern void mouse_event(int f, int x, int y, int d, int e);
[DllImport("user32.dll")] public static extern void keybd_event(byte v, byte s, int f, int e);
public struct R { public int L, T, Ri, B; } }
'@
[Pk]::keybd_event(0x5B,0,0,0); [Pk]::keybd_event(0x54,0,0,0); [Pk]::keybd_event(0x54,0,2,0); [Pk]::keybd_event(0x5B,0,2,0)
$h = [IntPtr]::Zero
for ($i = 0; $i -lt 30 -and $h -eq [IntPtr]::Zero; $i++) { Start-Sleep -Milliseconds 200; $h = [Pk]::FindWindow("AutoHotkeyGUI", "Theme Picker") }
if ($h -eq [IntPtr]::Zero) { "picker not found"; exit 1 }
$r = New-Object Pk+R; [Pk]::GetWindowRect($h, [ref]$r) | Out-Null
# Row layout from ShowPicker(): top 74, label 20, rows 40 high with 6 gap, column x 22, width 300, column gap 24.
$x = $r.L + 22 + ($Col - 1) * 324 + 120; $y = $r.T + 74 + 20 + ($Row - 1) * 46 + 20
[Pk]::SetCursorPos($x, $y) | Out-Null; Start-Sleep -Milliseconds 150
[Pk]::mouse_event(2,0,0,0,0); [Pk]::mouse_event(4,0,0,0,0)
"clicked row $Row at $x,$y"
