$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
Push-Location $projectRoot
try { & '.\.venv\Scripts\python.exe' -m jarvis --diagnostics; if ($LASTEXITCODE) { throw 'Falló el diagnóstico' } }
finally { Pop-Location }
