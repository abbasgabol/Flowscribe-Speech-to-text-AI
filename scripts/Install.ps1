$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
Write-Host "`n  LOCAL DICTATION" -ForegroundColor Green
Write-Host "  Your voice. Your computer.`n"
Write-Host 'Keep this extracted folder in a permanent, writable location.'
Write-Host 'First setup requires internet for Python, dependencies, and speech models.'
Write-Host 'Dictation runs offline after setup. No account or API key required.'

try {
    $pythonPath = $null
    $runtimePython = Join-Path $projectRoot 'runtime\python.exe'
    if (Test-Path -LiteralPath $runtimePython) { $pythonPath = $runtimePython }
    if (-not $pythonPath -and (Get-Command py.exe -ErrorAction SilentlyContinue)) {
        foreach ($version in @('-3.11', '-3.10')) {
            $ErrorActionPreference = 'Continue'
            $candidate = & py.exe $version -c "import sys,struct; print(sys.executable if struct.calcsize('P')==8 else '')" 2>$null
            $pythonExit = $LASTEXITCODE
            $ErrorActionPreference = 'Stop'
            if ($pythonExit -eq 0 -and $candidate -and (Test-Path -LiteralPath $candidate)) { $pythonPath = $candidate; break }
        }
    }
    if (-not $pythonPath) {
        Write-Host "`nDownloading Python 3.11.9 from python.org..."
        $installerPath = Join-Path $projectRoot 'python-setup.exe'
        Invoke-WebRequest -UseBasicParsing -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe' -OutFile $installerPath
        $signature = Get-AuthenticodeSignature -LiteralPath $installerPath
        if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch 'Python Software Foundation') {
            throw 'Python installer signature verification failed. Setup stopped.'
        }
        $runtimeDir = Join-Path $projectRoot 'runtime'
        $arguments = @('/passive', 'InstallAllUsers=0', ('TargetDir="{0}"' -f $runtimeDir),
            'Include_launcher=0', 'InstallLauncherAllUsers=0', 'PrependPath=0', 'AssociateFiles=0',
            'Shortcuts=0', 'Include_test=0', 'Include_doc=0', 'Include_pip=1', 'Include_tcltk=1')
        $installation = Start-Process -FilePath $installerPath -ArgumentList $arguments -Wait -PassThru -WindowStyle Hidden
        if ($installation.ExitCode -notin @(0, 3010)) { throw "Python setup failed (code $($installation.ExitCode))." }
        if (-not (Test-Path -LiteralPath $runtimePython)) {
            throw 'Python is installed elsewhere. Install Python 3.10 or 3.11 with its launcher from python.org, then run Setup again.'
        }
        $pythonPath = $runtimePython
    }
    Write-Host "`nPreparing the app environment..."
    if (-not (Test-Path '.venv\Scripts\python.exe')) {
        & $pythonPath -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Could not create the Python environment.' }
    }
    & '.\.venv\Scripts\python.exe' -m pip install --disable-pip-version-check -r requirements-lock.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Check your internet connection and retry.' }
    foreach ($downloadScript in @('scripts/download_model.py', 'scripts/download_punctuation.py')) {
        & '.\.venv\Scripts\python.exe' $downloadScript
        if ($LASTEXITCODE -ne 0) { throw "Model setup failed in $downloadScript. Run Setup again to retry." }
    }
    $shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path ([Environment]::GetFolderPath('Desktop')) 'Local Dictation.lnk'))
    $shortcut.TargetPath = Join-Path $projectRoot '.venv\Scripts\pythonw.exe'
    $shortcut.Arguments = '-m local_dictation'
    $shortcut.WorkingDirectory = $projectRoot
    if (Test-Path 'assets/app.ico') { $shortcut.IconLocation = Join-Path $projectRoot 'assets/app.ico' }
    $shortcut.Save()
    Write-Host "`nReady. Opening Local Dictation. Hold Win + Alt in a text field to speak." -ForegroundColor Green
    Start-Process -FilePath (Join-Path $projectRoot '.venv\Scripts\pythonw.exe') -ArgumentList '-m','local_dictation' -WorkingDirectory $projectRoot -WindowStyle Hidden
} catch {
    Write-Host "`n$($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
