param([int]$ProcId, [string]$Out)
# Window screenshot that works when another window covers it: PrintWindow with PW_RENDERFULLCONTENT (2).
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System; using System.Runtime.InteropServices;
public class PW { [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out R r);
[DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr dc, uint flags);
public struct R { public int L, T, Ri, B; } }
'@
$h = (Get-Process -Id $ProcId).MainWindowHandle
$r = New-Object PW+R; [PW]::GetWindowRect($h, [ref]$r) | Out-Null
$w = $r.Ri - $r.L; $hh = $r.B - $r.T
$bmp = New-Object System.Drawing.Bitmap $w, $hh
$g = [System.Drawing.Graphics]::FromImage($bmp)
$dc = $g.GetHdc()
$ok = [PW]::PrintWindow($h, $dc, 2)
$g.ReleaseHdc($dc)
$bmp.Save($Out)
"$w x $hh printwindow=$ok"
