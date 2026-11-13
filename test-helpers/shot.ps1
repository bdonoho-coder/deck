param([int]$ProcId, [string]$Out)
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System; using System.Runtime.InteropServices;
public class W { [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out R r);
[DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
public struct R { public int L, T, Ri, B; } }
'@
$h = (Get-Process -Id $ProcId).MainWindowHandle
[W]::SetForegroundWindow($h) | Out-Null
Start-Sleep -Milliseconds 800
$r = New-Object W+R; [W]::GetWindowRect($h, [ref]$r) | Out-Null
$w = $r.Ri - $r.L; $hh = $r.B - $r.T
$bmp = New-Object System.Drawing.Bitmap $w, $hh
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($r.L, $r.T, 0, 0, $bmp.Size)
$bmp.Save($Out)
"$w x $hh"
