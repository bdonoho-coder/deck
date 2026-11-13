# Deck free tier: one-time setup. Run from the extracted folder, as a normal user:
#   powershell -ExecutionPolicy Bypass -File .\install.ps1
# What it does (all per-user, no admin):
#   1. saves your current Windows colors/wallpaper to backup\ (the picker's "Original (undo all)" restores them)
#   2. writes windhawk-styles.reg with this folder's path (you import it as admin, see README)
#   3. puts the picker, finder, window frame and desktop-scroll scripts in your Startup folder and starts them
#   4. registers the Deck file manager (needs Developer Mode; the app is not signed)
# Rerun it any time; every step is safe to repeat.
param([switch]$SkipDeck)
$ErrorActionPreference = 'Stop'
$root = $PSScriptRoot
Set-Location $root
Start-Transcript -Path "$root\install.log" -Append | Out-Null  # keeps a record of every run next to the scripts
"Deck install $(Get-Date -Format s) as $env:USERNAME in $root"

# 0. AutoHotkey v2 is required for the picker and the hotkeys.
$ahk = Get-ChildItem "$env:LOCALAPPDATA\Programs\AutoHotkey\v2\AutoHotkey64.exe", "$env:ProgramFiles\AutoHotkey\v2\AutoHotkey64.exe" -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $ahk) {
    Write-Host "AutoHotkey v2 is not installed. Get it from https://www.autohotkey.com (v2), then run install.ps1 again." -ForegroundColor Yellow
    Start-Process 'https://www.autohotkey.com/download/'
    exit 1
}

# 1. Backup of the current look (only once).
New-Item -ItemType Directory -Force "$root\backup" | Out-Null
$keys = @{
    personalize = 'HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize'
    dwm         = 'HKCU\Software\Microsoft\Windows\DWM'
    accent      = 'HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Accent'
    desktop     = 'HKCU\Control Panel\Desktop'
}
foreach ($k in $keys.Keys) {
    $file = "$root\backup\$k.reg"
    if (-not (Test-Path $file)) { reg export $keys[$k] $file /y | Out-Null }
}
Write-Host "1. backup of your current look: $root\backup"

# 2. Windhawk settings for this folder.
$tpl = Get-Content "$root\windhawk-styles.template.reg" -Encoding Unicode -Raw
$tpl = $tpl.Replace('{{ROOT_URI}}', $root.Replace('\', '/')).Replace('{{ROOT}}', $root.Replace('\', '\\'))  # .reg doubles backslashes
[IO.File]::WriteAllText("$root\windhawk-styles.reg", $tpl, [Text.Encoding]::Unicode)
Write-Host "2. wrote windhawk-styles.reg (import it as admin after installing the Windhawk mods, see README)"

# 3. Startup shortcuts + start the scripts now.
$startup = [Environment]::GetFolderPath('Startup')
$shell = New-Object -ComObject WScript.Shell
foreach ($script in 'ThemePicker.ahk', 'Finder.ahk', 'HudFrame.ahk', 'DesktopScroll.ahk') {
    $lnk = $shell.CreateShortcut("$startup\$([IO.Path]::GetFileNameWithoutExtension($script)).lnk")
    $lnk.TargetPath = $ahk.FullName
    $lnk.Arguments = "`"$root\$script`""
    $lnk.WorkingDirectory = $root
    $lnk.Save()
    Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*\$script*" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
    Start-Process $ahk.FullName -ArgumentList "`"$root\$script`"" -WorkingDirectory $root
}
Write-Host "3. picker (Win+T), finder (Win+Space), window frames and Win+wheel desktop switch are running and in Startup"

# 4. Deck, the file manager (Win+E in the picker opens it).
if (-not $SkipDeck) {
    $dev = (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock' -ErrorAction SilentlyContinue).AllowDevelopmentWithoutDevLicense
    if ($dev -ne 1) {
        Write-Host "4. Deck needs Developer Mode (Settings > System > For developers > Developer Mode). Turn it on, then run install.ps1 again." -ForegroundColor Yellow
        Start-Process 'ms-settings:developers'
        exit 1
    }
    $msix = Get-ChildItem "$root\deck-app\Deck_*_x64.msix" | Select-Object -First 1
    $layout = "$root\deck-app\layout"
    Get-Process Files -ErrorAction SilentlyContinue | Where-Object { $_.Path -like "$layout*" } | Stop-Process -Force
    Get-AppxPackage Deck | Remove-AppxPackage -PreserveApplicationData
    if (Test-Path $layout) { Remove-Item $layout -Recurse -Force }
    Add-AppxPackage "$root\deck-app\Microsoft.WindowsAppRuntime.2.msix" -ErrorAction SilentlyContinue
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    [IO.Compression.ZipFile]::ExtractToDirectory($msix.FullName, $layout)
    try {
        Add-AppxPackage -Register "$layout\AppxManifest.xml"
        Write-Host "4. Deck registered: $((Get-AppxPackage Deck).PackageFamilyName)"
    } catch {
        if ("$_" -match '0x80073CFB') {
            # Windows allows one developer (loose-folder) registration of a package per PC. Another account has one.
            Write-Host "4. Deck could not be registered: another account on this PC already has a developer install of Deck. Uninstall it there (Settings > Apps > Deck), then run install.ps1 again. Everything else is set up." -ForegroundColor Yellow
        } else {
            Write-Host "4. Deck could not be registered: $_" -ForegroundColor Yellow
        }
    }
}
Write-Host "Done. Press Win+T to pick a theme."
Stop-Transcript | Out-Null
