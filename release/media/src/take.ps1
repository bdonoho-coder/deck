# The take: a timed sequence of theme switches through the real picker (Win+T + click), logging wall-clock marks.
param([string]$Log)
$pick = Join-Path $PSScriptRoot 'pick2.ps1'
$t0 = Get-Date
function Mark($s) { $ms = [int]((Get-Date) - $t0).TotalMilliseconds; "$ms`t$s" | Tee-Object -FilePath $Log -Append }
# themes.ini order: col1 = tokyo-night, catppuccin, gruvbox, nord, everforest, catppuccin-latte, amber-lab
#                   col2 = red, orange, amber, cyan, neongrid, synth, pulse, irondeck, acid
$seq = @(
    @{ Row = 1; Col = 1; Name = 'tokyo-night'; Wait = 7 },
    @{ Row = 4; Col = 1; Name = 'nord';        Wait = 7 },
    @{ Row = 4; Col = 2; Name = 'hud-cyan';    Wait = 7 },
    @{ Row = 1; Col = 2; Name = 'hud-red';     Wait = 7 },
    @{ Row = 9; Col = 2; Name = 'hud-acid';    Wait = 9 }
)
Start-Sleep -Seconds 2.5
foreach ($s in $seq) {
    Mark "open picker for $($s.Name)"
    $p = Start-Process -FilePath "$env:LOCALAPPDATA\Programs\AutoHotkey\v2\AutoHotkey64.exe" -ArgumentList @((Join-Path $PSScriptRoot 'pick3.ahk'), $s.Row, $s.Col) -PassThru
    $p.WaitForExit(8000) | Out-Null
    $r = if ($p.HasExited) { "exit $($p.ExitCode)" } else { Stop-Process -Id $p.Id -Force; 'helper killed (hung after click)' }
    Mark "clicked $($s.Name): $r"
    Start-Sleep -Seconds $s.Wait
}
Mark 'end'
