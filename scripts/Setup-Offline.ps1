$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not [Environment]::Is64BitOperatingSystem) { throw '64-bit Windows is required.' }
if ($env:PROCESSOR_ARCHITECTURE -eq 'ARM64') { throw 'This kit targets Intel/AMD x64 Windows, not ARM64.' }
# Verify the copied payload before executing installers or packages.
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'manifest.json') -Raw | ConvertFrom-Json
foreach ($file in $manifest.files) {
    $actual = (Get-FileHash -LiteralPath (Join-Path $PSScriptRoot $file.path) -Algorithm SHA256).Hash
    if ($actual -ne $file.sha256) { throw "Corrupt or changed bundle file: $($file.path)" }
}
$python = Join-Path $PSScriptRoot 'runtime\python.exe'
if (-not (Test-Path -LiteralPath $python)) {
    $installer = Join-Path $PSScriptRoot 'installers\python-installer.exe'
    $target = Join-Path $PSScriptRoot 'runtime'
    $signature = Get-AuthenticodeSignature -LiteralPath $installer
    if ($signature.Status -ne 'Valid') { throw 'Python installer signature is not valid. Ask IT to verify this installer.' }
    $process = Start-Process -FilePath $installer -Wait -PassThru -ArgumentList @(
        '/passive', 'InstallAllUsers=0', "TargetDir=`"$target`"", 'Include_pip=1',
        'Include_launcher=0', 'Include_test=0', 'Include_doc=0', 'Shortcuts=0', 'PrependPath=0'
    )
    if ($process.ExitCode -notin @(0, 3010)) { throw "Python installation failed: $($process.ExitCode)" }
    if ($process.ExitCode -eq 3010) { Write-Warning 'Windows requested a restart; restart before hardware testing.' }
}
& $python -c "import sys, struct; assert sys.version_info[:2] == (3, 13) and struct.calcsize('P') == 8, 'Wrong Python runtime'"
if ($LASTEXITCODE -ne 0) { throw 'Python runtime check failed.' }
& $python -m pip --isolated install --no-index --find-links (Join-Path $PSScriptRoot 'wheelhouse') 'echemtips[fpga,analysis,movies]'
if ($LASTEXITCODE -ne 0) { throw 'Offline package installation failed.' }
& $python -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Package dependency check failed.' }
& $python -c "import PySide6, pyqtgraph, scipy, nifpga, nptdms, imageio_ffmpeg; print('Dependencies OK')"
if ($LASTEXITCODE -ne 0) { throw 'Dependency import check failed.' }
$shell = New-Object -ComObject WScript.Shell
foreach ($entry in @(@('eChemTips', 'Start eChemTips.vbs'), @('eChemTips Analysis', 'Start Analysis.vbs'))) {
    $shortcut = $shell.CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) ($entry[0] + '.lnk')))
    $shortcut.TargetPath = Join-Path $env:WINDIR 'System32\wscript.exe'
    $shortcut.Arguments = '"' + (Join-Path $PSScriptRoot $entry[1]) + '"'
    $shortcut.WorkingDirectory = $PSScriptRoot
    $shortcut.Save()
}
Write-Host 'Ready. Test Simulation first. NI drivers and a compatible private bitfile are separate.'
