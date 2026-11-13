# Clean recording scene: minimize everything, open Deck on C:\DeckTry, place it centre-screen.
param([int]$X = 240, [int]$Y = 110, [int]$W = 1440, [int]$H = 900)
Add-Type @'
using System; using System.Runtime.InteropServices;
public class Sc {
 [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr a, int x, int y, int w, int hh, uint f);
 [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int n);
 [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
}
'@
(New-Object -ComObject Shell.Application).MinimizeAll()
Start-Sleep -Milliseconds 800
$deck = Get-Process Files -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 }
if (-not $deck) {
    Start-Process 'C:\DeckTry'
    for ($i = 0; $i -lt 40 -and -not $deck; $i++) { Start-Sleep -Milliseconds 500; $deck = Get-Process Files -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowHandle -ne 0 } }
}
if (-not $deck) { 'Deck window not found'; exit 1 }
$hw = ($deck | Select-Object -First 1).MainWindowHandle   # not $h: PowerShell vars are case-insensitive, $H is the height
[Sc]::ShowWindow($hw, 9) | Out-Null          # SW_RESTORE
[Sc]::SetWindowPos($hw, [IntPtr]::Zero, $X, $Y, $W, $H, 0x0040) | Out-Null
[Sc]::SetForegroundWindow($hw) | Out-Null
[Sc]::SetCursorPos(1800, 1000) | Out-Null
"deck pid $(($deck | Select-Object -First 1).Id) at $X,$Y $W x $H"
