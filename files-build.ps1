# Builds Deck (our Files fork) with the VS 2026 Build Tools.
# Normal use: files-build.ps1 -Config Release -Package -Install
# -Install unpacks the MSIX to files-layout and registers it (Developer Mode, no certificate).
param([string]$Config = 'Debug', [switch]$Package, [switch]$Install)
$vs = 'C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools'
Import-Module "$vs\Common7\Tools\Microsoft.VisualStudio.DevShell.dll"
Enter-VsDevShell -VsInstallPath $vs -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
$env:PATH += ';C:\Program Files (x86)\Microsoft Visual Studio\Installer'
Set-Location (Join-Path $PSScriptRoot 'files-src')
msbuild Files.slnx -t:Restore -p:Platform=x64 -p:Configuration=$Config -v:quiet -clp:ErrorsOnly
if ($LASTEXITCODE) { exit $LASTEXITCODE }
$pkgDir = (Join-Path $PSScriptRoot 'files-pkg') + [IO.Path]::DirectorySeparatorChar
if ($Package -and (Test-Path $pkgDir)) { Remove-Item $pkgDir -Recurse -Force }
$pkg = if ($Package) { @('-p:GenerateAppxPackageOnBuild=true', '-p:AppxBundle=Never', '-p:UapAppxPackageBuildMode=SideloadOnly', '-p:AppxPackageSigningEnabled=false', "-p:AppxPackageDir=$pkgDir") } else { @() }
# The launcher (default file manager hook) is a C++ project; it copies itself into Assets\FilesOpenDialog.
if (-not (Test-Path src\Files.App\Assets\FilesOpenDialog\Files.App.Launcher.exe)) {
    msbuild src\Files.App.Launcher\Files.App.Launcher.vcxproj -p:Configuration=Release -p:Platform=x64 -v:quiet -clp:ErrorsOnly
    if ($LASTEXITCODE) { exit $LASTEXITCODE }
}
msbuild src\Files.App\Files.App.csproj -p:Configuration=$Config -p:Platform=x64 -v:quiet -clp:ErrorsOnly -m @pkg
if ($LASTEXITCODE -or -not $Install) { exit $LASTEXITCODE }

$msix = Get-ChildItem $pkgDir -Recurse -Filter 'Files.App_*.msix' | Where-Object { $_.Directory.Name -notmatch 'Dependencies' } | Select-Object -First 1
$layout = Join-Path $PSScriptRoot 'files-layout'
Get-Process Files -ErrorAction SilentlyContinue | Where-Object Path -like "$layout*" | Stop-Process -Force
Get-AppxPackage Deck | Remove-AppxPackage -PreserveApplicationData
if (Test-Path $layout) { Remove-Item $layout -Recurse -Force }
Add-Type -AssemblyName System.IO.Compression.FileSystem
[IO.Compression.ZipFile]::ExtractToDirectory($msix.FullName, $layout)
Add-AppxPackage -Register "$layout\AppxManifest.xml"
"Installed $($msix.Name)"
