# Points app shortcuts at themed icons in appicons\active (filled by ThemePicker.ahk).
#   app_icons.ps1          apply (backs up each .lnk first, once)
#   app_icons.ps1 -Restore put the backed-up .lnk files back
# Run as admin once: the Public desktop and the shared Start menu need it.
param([switch]$Restore)

$root = $PSScriptRoot
$active = Join-Path $root "appicons\active"
$backup = Join-Path $root "backup\shortcuts"
$listFile = Join-Path $backup "list.csv"

# Target program file name -> icon id (appicons\<theme>\<id>.ico).
$map = @{
    'chrome.exe' = 'chrome'; 'spotifast.exe' = 'spotify'; 'steam.exe' = 'steam'
    'epicgameslauncher.exe' = 'epic'; 'ubisoftconnect.exe' = 'ubisoft'; 'telegram.exe' = 'telegram'
    'notion.exe' = 'notion'; 'obsidian.exe' = 'obsidian'; 'zoom.exe' = 'zoom'; 'obs64.exe' = 'obs'
    'blender-launcher.exe' = 'blender'; 'blender.exe' = 'blender'; 'krita.exe' = 'krita'
    'nvidia app.exe' = 'nvidia'; 'itunes.exe' = 'itunes'; 'malwarebytes.exe' = 'malwarebytes'
    'pythonw.exe' = 'python'; 'python.exe' = 'python'; 'firefox.exe' = 'firefox'
    'playnite.desktopapp.exe' = 'playnite'; 'nxplayer.exe' = 'nomachine'; 'sumatrapdf.exe' = 'sumatrapdf'
    'windhawk.exe' = 'windhawk'; 'cheat engine.exe' = 'cheatengine'; 'wand.exe' = 'wemod'
}

$folders = @(
    "$env:APPDATA\Microsoft\Internet Explorer\Quick Launch\User Pinned\TaskBar",
    [Environment]::GetFolderPath('Desktop'),
    "$env:PUBLIC\Desktop",
    "$env:APPDATA\Microsoft\Windows\Start Menu\Programs",
    "$env:ProgramData\Microsoft\Windows\Start Menu\Programs"
)

if ($Restore) {
    foreach ($row in Import-Csv $listFile) {
        Copy-Item -LiteralPath $row.Copy -Destination $row.Original -Force
        "restored $($row.Original)"
    }
    return
}

New-Item -ItemType Directory -Force $backup, $active | Out-Null
$saved = @{}
if (Test-Path $listFile) { Import-Csv $listFile | ForEach-Object { $saved[$_.Original] = $_ } }
$rows = @($saved.Values)
$shell = New-Object -ComObject WScript.Shell

foreach ($dir in $folders) {
    foreach ($f in Get-ChildItem -LiteralPath $dir -Filter *.lnk -Recurse -ErrorAction SilentlyContinue) {
        $lnk = $shell.CreateShortcut($f.FullName)
        if (-not $lnk.TargetPath) { continue }
        $id = $map[[IO.Path]::GetFileName($lnk.TargetPath).ToLower()]
        if (-not $id) { continue }
        if (-not $saved.ContainsKey($f.FullName)) {
            $copy = Join-Path $backup ("{0:D3}_{1}" -f $rows.Count, $f.Name)
            Copy-Item -LiteralPath $f.FullName -Destination $copy
            $row = [pscustomobject]@{ Original = $f.FullName; Copy = $copy }
            $rows += $row; $saved[$f.FullName] = $row
        }
        $lnk.IconLocation = (Join-Path $active "$id.ico") + ",0"
        try { $lnk.Save(); "set $id  $($f.FullName)" } catch { "FAILED $($f.FullName): $_" }
    }
}
$rows | Export-Csv $listFile -NoTypeInformation
