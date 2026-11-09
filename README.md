# JARVIS CORE — Fase 1

Motor residente local para Windows: micrófono único, Rustpotter, ciclo de activación de 10 segundos, pausa, bandeja y recuperación. **No interpreta órdenes ni conversa.**

La implementación es ejecutable, el auxiliar Rust está compilado y la referencia personal está calibrada en este equipo. Se comprobó activación con voz, pausa/reanudación, reinicio, suspensión y salida. La validación funcional básica está completada; quedan pruebas prolongadas y mediciones de precisión acústica. Sin referencia válida, la bandeja muestra `DEGRADED`.

## Empezar en este equipo

Desde la carpeta del proyecto, con Jarvis cerrado:

```powershell
.\.venv\Scripts\python.exe -m jarvis --list-devices
.\.venv\Scripts\python.exe -m jarvis --calibrate-wakeword
.\.venv\Scripts\python.exe -m jarvis --debug
```

La calibración solicita escribir `GRABAR` y obtiene seis muestras explícitas. Después, para iniciar sin consola:

```powershell
Start-Process -FilePath '.\.venv\Scripts\pythonw.exe' -ArgumentList '"scripts\run_resident.pyw"' -WindowStyle Hidden
```

En la bandeja: estado, pausar, reanudar/reintentar, activación manual, diagnósticos, registros y salir. La activación manual solo funciona cuando los recursos están preparados en `DORMANT`. Pausar cierra el micrófono y el auxiliar.

En este equipo el inicio automático **ya está registrado** tras la calibración y prueba del usuario. Falta comprobarlo al cerrar y volver a iniciar sesión. Para instalarlo en otra ubicación o equipo:

```powershell
.\scripts\install_startup.ps1 -ValidateOnly
.\scripts\install_startup.ps1
# Para quitarlo:
.\scripts\uninstall_startup.ps1
```

## Verificación

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m jarvis --diagnostics
# Abre el micrófono real, no guarda audio; usa una referencia sintética temporal:
.\.venv\Scripts\python.exe scripts\benchmark.py --seconds 60
```

Se ejecutaron 62 pruebas automáticas al preparar la entrega, además de mediciones reales de 60 y 30 segundos. Consulta [validación y límites](docs/validation.md) y los informes JSON en `docs/reports/`. Las pruebas sintéticas no demuestran precisión con voces reales.

## Documentación

- [Instalación reproducible](docs/installation.md)
- [Calibración y uso](docs/phase_1.md)
- [Arquitectura y protocolo](docs/architecture.md)
- [Configuración y recuperación](docs/configuration.md)
- [Solución de problemas](docs/troubleshooting.md)
- [Decisiones y dependencias](docs/decisions.md)
- [Visión](docs/vision.md) y [fases posteriores](docs/future_roadmap.md)
- [Documento original del usuario](docs/project_spec.md)

Datos modificables: `%LOCALAPPDATA%\JarvisCore`. Solo se guarda la referencia acústica, configuración, registros y diagnósticos. El audio del residente permanece en memoria. No hay conexiones de red en el funcionamiento normal.
