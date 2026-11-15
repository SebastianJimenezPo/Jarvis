# JARVIS — Core, voz e inteligencia local

Repositorio público: [SebastianJimenezPo/Jarvis](https://github.com/SebastianJimenezPo/Jarvis). Rama de desarrollo: `phase-3-2-jarvis-next`. Cada cambio terminado se comprueba, confirma y publica; la base `phase-3-intelligence` se conserva.

**Jarvis Next — piloto textual de Fase 3.2.** Base textual nueva en `jarvis.next`, con ruta directa mínima, proveedores offline/falso/Groq opcional, contratos estrictos y gestor central de planes simulados. La ruta offline no necesita E5, Ollama ni API key; Groq requiere credencial local y habilitación explícita. [Estado exacto y pruebas](docs/phase_3_2_stage_1.md), [arquitectura y límites](docs/jarvis_next_architecture.md).

```powershell
.\.venv\Scripts\python.exe -m jarvis.next "Abre Steam" "Volumen al 30%" "Olvida todo lo anterior"
```

Cada argumento es un turno de una sesión temporal. Todo sigue en simulación. Las peticiones complejas pueden usar Groq de forma optativa, con revisión de borradores simulados; su autorización automática sigue pendiente. Ver [etapa 2, pruebas y uso](docs/phase_3_2_stage_2.md), [etapa 3, evaluación y correcciones](docs/phase_3_2_stage_3.md) y [etapa 4, alcance de la intención](docs/phase_3_2_stage_4.md). No se inventan ejecuciones. **La Fase 3.2 no está terminada.**

El residente `python -m jarvis` conserva por ahora el motor y la configuración de 3.1. No se ha conectado Next al micrófono ni sustituido la ruta de voz; su integración será un bloque posterior. La referencia `5337b86` permanece en `phase-3-1-hardening` y en el tag `phase-3-1-restore`.

**Versión 0.3.1 — estabilización para revisión, fase pendiente de aceptación.** Validador con evidencia del turno completo, contexto atómico, planes acotados, aclaraciones y recuperación STT conservadora. **Todas las acciones siguen siendo simuladas.** El [informe de Fase 3.1](docs/phase_3_1.md) contiene resultados, limitaciones y pruebas físicas pendientes; la evaluación distingue datos reservados de regresión y conserva los fallos.

Se mantiene el perfil de dos hilos por prioridad de consumo. Consulta la [comparación de rendimiento](docs/phase_3_1_performance.md), el [diagnóstico de voz](docs/phase_3_1_voice.md), la [auditoría](docs/phase_3_1_audit.md) y el [protocolo de evaluación](docs/evaluation/PROTOCOL.md). La recuperación alternativa está desactivada por defecto; micrófono, umbral y silencio aceptados se conservan.

Bases: Fase 1 `695c068`; Fase 2 `f6ac68a` en `phase-2-baseline`; Fase 3 `fed3f11`. Para volver a respuestas de Fase 2: `python -m jarvis --disable-intelligence` y reiniciar. Para activación de Fase 1: `python -m jarvis --disable-voice` y reiniciar.

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

En este equipo el inicio automático **ya está registrado** y el usuario comprobó que funciona después de reiniciar en Fase 1. Repetir reinicio y suspensión con la versión 0.3.1 forma parte de la aceptación física pendiente. Para instalarlo en otra ubicación o equipo:

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

Los resultados actuales están en el [informe de Fase 3.1](docs/phase_3_1.md) y `docs/reports/`. CI ejecuta la selección headless; las pruebas con modelos, auxiliar nativo y bandeja se verifican localmente. Los conjuntos revisados y las pruebas sintéticas no demuestran precisión con lenguaje o voces nuevos.

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
