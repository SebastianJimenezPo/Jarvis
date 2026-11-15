param([switch]$Offline, [double]$ExitAfter = 0, [string]$Stt = '')
$workspacePath = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $workspacePath '.venv\Scripts\pythonw.exe'
$launcherPath = Join-Path $PSScriptRoot 'run_resident.pyw'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Falta el entorno .venv del proyecto.' }
# Explicit experimental launcher; the owner confirmed this Groq account is Free.
# No credential is stored here. The worker reads Windows Credential Manager.
$launchArguments = @(('"' + $launcherPath + '"'), '--profile', 'next')
if (-not $Offline) { $launchArguments += @('--allow-remote', '--free-tier') }
if ($Stt) { $launchArguments += @('--next-stt', $Stt) }
if ($ExitAfter -gt 0) { $launchArguments += @('--exit-after', $ExitAfter.ToString([cultureinfo]::InvariantCulture)) }
Start-Process -FilePath $pythonPath -ArgumentList $launchArguments -WorkingDirectory $workspacePath -WindowStyle Hidden -PassThru
