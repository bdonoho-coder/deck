param([switch]$Undo)
# Makes Deck (our Files fork) the default file manager for the current user, the same way the
# app's own "Set as default file manager" switch does, but without the UAC prompt (HKCU only):
#   1. copy Assets\FilesOpenDialog (launcher exe + .reg files) from the installed layout to %LocalAppData%\Files
#   2. write Branch.txt = deck (the app reads it)
#   3. import SetFilesAsDefault.reg: Folder\shell\open + explore -> Files.App.Launcher.exe, Win+E CLSID
# -Undo removes the HKCU overrides so File Explorer is the default again, and deletes %LocalAppData%\Files.
$layout = Join-Path (Split-Path $PSScriptRoot) 'files-layout/Assets/FilesOpenDialog'  # the dev install layout next to this repo
$dest = Join-Path $env:LOCALAPPDATA 'Files'
if ($Undo) {
    foreach ($k in 'HKCU:\Software\Classes\Folder\shell\open\command', 'HKCU:\Software\Classes\Folder\shell\explore\command',
                   'HKCU:\Software\Classes\CLSID\{52205fd8-5dfb-447d-801a-d0b52f2e83e1}') {
        if (Test-Path $k) { Remove-Item $k -Recurse -Force }
    }
    if (Test-Path $dest) { Remove-Item $dest -Recurse -Force }
    "File Explorer is the default again"
    exit
}
if (-not (Test-Path "$layout\Files.App.Launcher.exe")) { "launcher missing in $layout"; exit 1 }
New-Item -ItemType Directory -Force $dest | Out-Null
Copy-Item "$layout\*" $dest -Force
'deck' | Out-File -Encoding utf8 -Force (Join-Path $dest 'Branch.txt')
reg import "$dest\SetFilesAsDefault.reg" 2>&1 | Out-String
(Get-ItemProperty 'HKCU:\Software\Classes\Folder\shell\open\command').'(default)'
