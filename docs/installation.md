# Instalación

## Entorno verificado

Windows 11 Home 10.0.26200, AMD Ryzen 9 4900HS, 16 procesadores lógicos, 16 GB de RAM, NVIDIA GTX 1660 Ti Max-Q y Radeon integrada. Python 3.11.14 x64, Rust 1.85.1 `x86_64-pc-windows-gnu`. No se usa CUDA ni se instalaron modelos STT, LLM o TTS.

El directorio inicial solo contenía `.git`. Se creó aquí un proyecto nuevo, con `.venv` independiente. El equipo tenía Python 3.13. Se instaló `uv==0.9.7` en el perfil del usuario para obtener Python 3.11.14; no se reemplazó Python 3.13 ni se cambió el PATH global. Rust quedó dentro de `.tools` del proyecto.

## Recrear Python

Ejecutar desde la raíz del proyecto. Se necesita un Python disponible para instalar uv:

```powershell
python -m pip install --user uv==0.9.7
python -m uv python install 3.11.14
python -m uv venv --python 3.11.14 .venv
python -m uv pip install --python .venv\Scripts\python.exe -r requirements-lock.txt
python -m uv pip install --python .venv\Scripts\python.exe --no-deps -e .
```

`requirements-lock.txt` fija también dependencias transitivas de ejecución y pruebas. El backend de construcción está fijado en `pyproject.toml`. Es una instalación desde checkout editable: conserva el proyecto junto al ejecutable Rust. No se ha creado un instalador redistribuible ni un único EXE.

## Compilar Rust sin Visual Studio

Descarga oficial de rustup: [rustup.rs](https://rustup.rs/). La variante GNU utilizada compiló en este equipo sin Visual Studio, GCC externo ni cambios globales de PATH:

```powershell
New-Item -ItemType Directory -Force .tools | Out-Null
Invoke-WebRequest 'https://win.rustup.rs/x86_64' -OutFile '.tools\rustup-init.exe'
$env:RUSTUP_HOME = Join-Path $PWD '.tools\rustup'
$env:CARGO_HOME = Join-Path $PWD '.tools\cargo'
& '.tools\rustup-init.exe' -y --no-modify-path --profile minimal --default-toolchain 1.85.1-x86_64-pc-windows-gnu
.\scripts\build_engine.ps1
```

`Cargo.lock` está incluido; la compilación usa `--locked`. Salida: `rust\target\release\jarvis-wakeword.exe`. Los binarios y toolchains se ignoran en Git y deben reconstruirse al clonar. No se asume compatibilidad con MSVC ni con otras versiones de Rust sin pruebas.

## Inicio por usuario

`install_startup.ps1` crea una tarea cuyo nombre incluye el SID del usuario. Usa un desencadenador al iniciar sesión, token interactivo, nivel limitado, `pythonw.exe`, rutas absolutas y directorio de trabajo explícito. No guarda contraseña. Permite batería y no corta el proceso por tiempo de ejecución. La instalación es idempotente y no inicia una sesión de captura inmediatamente.

`-ValidateOnly` construye y comprueba los objetos del Programador, sin registrar nada. `-WhatIf` muestra la operación prevista. Si una política local deniega el registro, el script informa del error; no intenta elevar permisos ni modificar políticas del sistema. No se instaló la tarea durante el desarrollo.

La tarea usa la ubicación actual del checkout. Si mueves el proyecto, recrea `.venv` y vuelve a ejecutar la instalación de inicio automático.
