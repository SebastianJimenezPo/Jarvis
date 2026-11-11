# JARVIS — Core, voz e inteligencia local

Repositorio privado: [SebastianJimenezPo/Jarvis](https://github.com/SebastianJimenezPo/Jarvis). Los cambios terminados se guardan en commits y se publican en GitHub. La rama actual de desarrollo es `phase-3-intelligence`.

**Fase 3 implementada, pendiente de aceptación física del usuario.** Versión 0.3.0: comprensión híbrida, conversación mediante Ollama local, referencias temporales, aclaraciones y propuestas estructuradas. **Todas las acciones son simuladas.** Guías: [Fase 3 y pruebas físicas](docs/phase_3.md), [arquitectura](docs/intelligence_architecture.md), [comparación de modelos](docs/model_comparison.md) y [validación y límites](docs/intelligence_validation.md).

Tras las primeras pruebas físicas se corrigieron aclaraciones y cancelación y se redujeron cargas innecesarias de modelos. Perfil de consumo con dos hilos y liberación más temprana; [resultados y límites de los ajustes](docs/phase_3_feedback.md). La batería actual pasa 218 pruebas.

Las bases se conservan en Git: Fase 1 `695c068`; Fase 2 `f6ac68a`, rama `phase-2-baseline`. El desarrollo actual está en `phase-3-intelligence`. Para usar las respuestas de prueba de Fase 2: `python -m jarvis --disable-intelligence` y reiniciar. Para volver al comportamiento de activación de Fase 1: `python -m jarvis --disable-voice` y reiniciar.

La documentación siguiente describe la base y sus procedimientos de calibración/inicio.

La base residente utiliza micrófono único, Rustpotter, pausa, bandeja y recuperación. Conserva STT local español, Silero, Piper, varios turnos, cancelación y protección semidúplex contra eco. La interpretación de Fase 3 añade planes simulados y conversación; la ejecución real pertenece a una fase posterior.

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

En este equipo el inicio automático **ya está registrado** y el usuario comprobó que funciona después de reiniciar en Fase 1. La validación después de reinicio con el motor de Fase 2 queda pendiente. Para instalarlo en otra ubicación o equipo:

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

La entrega de Fase 3 pasa 189 pruebas automáticas y contiene corpus escritos de 328 casos / 363 turnos, comparaciones locales y una integración de voz sintética. Consulta [validación de inteligencia](docs/intelligence_validation.md) y los informes JSON en `docs/reports/`. Los conjuntos revisados y las pruebas sintéticas no demuestran precisión con lenguaje o voces nuevos.

## Documentación

- [Instalación reproducible](docs/installation.md)
- [Calibración y uso](docs/phase_1.md)
- [Arquitectura y protocolo](docs/architecture.md)
- [Configuración y recuperación](docs/configuration.md)
- [Solución de problemas](docs/troubleshooting.md)
- [Decisiones y dependencias](docs/decisions.md)
- [Visión](docs/vision.md) y [fases posteriores](docs/future_roadmap.md)
- [Documento original del usuario](docs/project_spec.md)

Datos modificables: `%LOCALAPPDATA%\JarvisCore`. Modelos, referencia acústica, configuración, registros y diagnósticos se guardan localmente. El audio y contexto conversacional permanecen en RAM; los registros de texto están deshabilitados por defecto. La inteligencia usa HTTP exclusivamente loopback con Ollama; las descargas requieren ejecutar el instalador explícitamente.
