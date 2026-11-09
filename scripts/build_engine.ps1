$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$localCargo = Join-Path $projectRoot '.tools\cargo\bin\cargo.exe'
if (Test-Path -LiteralPath $localCargo) {
    $env:RUSTUP_HOME = Join-Path $projectRoot '.tools\rustup'
    $env:CARGO_HOME = Join-Path $projectRoot '.tools\cargo'
    $cargoPath = $localCargo
} else { $cargoPath = (Get-Command cargo -ErrorAction Stop).Source }
& $cargoPath +1.85.1-x86_64-pc-windows-gnu build --release --locked --manifest-path (Join-Path $projectRoot 'rust\Cargo.toml')
if ($LASTEXITCODE) { throw 'La compilación Rust falló.' }
