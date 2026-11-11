# Registro de decisiones — 2026-11-09

- Proyecto nuevo en checkout vacío; Python 3.11.14 aislado. No se consultó ni reutilizó una implementación previa.
- Rustpotter 3.0.2 mediante auxiliar Rust; no se asumió un binding oficial Python. La API real de la versión usa `process_bytes` y `WakewordRefBuildFromFiles`. Algunas muestras del README upstream corresponden a APIs anteriores; se verificó contra fuentes y compilación.
- Rust 1.85.1 GNU en herramientas locales. Compilación real satisfactoria y posterior compilación `--locked`. Se fijó `half=2.3.1` para conservar compatibilidad con el árbol Candle 0.2 y rand 0.8; no se activó CUDA ni se carga un modelo neuronal.
- `PySide6-Essentials` proporciona QtCore/Gui/Widgets sin instalar Qt completo. El árbol completo quedó alrededor de 81 MiB de RSS máximo muestreado en la prueba inicial, por lo que no se justificó reemplazar la bandeja con otra biblioteca.
- PortAudio/sounddevice para WASAPI; soxr para remuestreo continuo. `pycaw` se usa únicamente para notificaciones nativas de endpoints. Se utiliza la reinicialización privada de PortAudio para actualizar su caché, aislada en `capture.py`; debe revisarse al actualizar sounddevice.
- Nombre WASAPI exacto para selección fija; los nombres duplicados se rechazan. Un identificador de endpoint persistente sería una mejora futura si se cambia el backend de captura.
- JSON en lugar de TOML para configuración de usuario: permite persistencia y reparación con biblioteca estándar de Python. No se duplica una configuración predeterminada estática que pueda desincronizarse.
- No se registró inicio automático ni se grabó la voz del usuario durante implementación. Las mediciones de hardware procesaron audio en RAM y usaron una referencia sintética temporal claramente identificada.
- Se añadió Job Object para terminar el auxiliar si el padre muere. Se verificó con un proceso padre terminado forzosamente.
- No se declaran terminadas las pruebas acústicas reales, suspensión física, reinicio, gaming o estabilidad prolongada.

## Dependencias y mantenimiento

Versiones Python transitivas fijadas en `requirements-lock.txt`; Rust en `Cargo.lock`. Compatibilidad comprobada en Windows x64/Python 3.11 de este equipo. Las versiones fijadas proporcionan reproducibilidad, no garantizan mantenimiento futuro. Rustpotter 3.0.2 es una versión antigua; no se atribuye soporte activo sin evidencia. Su aislamiento facilita reemplazarlo si las pruebas reales muestran insuficiente precisión o problemas de mantenimiento.

Licencias declaradas por paquetes/fuentes: Rustpotter Apache-2.0; sounddevice MIT; NumPy BSD con avisos de componentes incluidos; psutil BSD-3-Clause; pycaw MIT; comtypes MIT; wrapper python-soxr BSD-3-Clause y libsoxr LGPL-2.1; PySide6/Shiboken LGPL-3.0/GPL según distribución. Se usa distribución dinámica de bibliotecas, sin empaquetar un producto cerrado. Conservar licencias y avisos de terceros al preparar un instalador; esta entrega es el checkout y entorno local, no una auditoría jurídica de redistribución.

Fuentes primarias consultadas:

- [Rustpotter 3.0.2 y API](https://docs.rs/rustpotter/3.0.2/rustpotter/)
- [Código y licencia Rustpotter](https://github.com/GiviMAD/rustpotter)
- [sounddevice 0.5.2](https://python-sounddevice.readthedocs.io/en/0.5.2/)
- [python-soxr](https://github.com/dofuuz/python-soxr)
- [pycaw](https://github.com/AndreMiras/pycaw)
- [Qt for Python](https://doc.qt.io/qtforpython-6/)

## Cambios iniciales

Ajustes posteriores de 0.3.0 (2026-11-10): respuesta a las primeras pruebas físicas del usuario. Aclaraciones de color/volumen y cancelación explícitas por ruta rápida; reconocimiento de cancelación en el filtro de primer turno; cortesía puntuada por STT; puerta de dominio antes de cargar E5. Perfil de dos hilos LLM y dos CPU lógicas para el subproceso de voz, liberación más temprana y espera activa ONNX deshabilitada. 218 pruebas automáticas aprobadas. Menor CPU LLM medida con mayor demora; reducción de memoria Python en comparación controlada, sin confundirla con memoria de Ollama. La integración sintética verifica cancelación pero conserva fallo de transcripción en la secuencia de luces; activación y STT siguen pendientes. Ver `phase_3_feedback.md`.

0.3.0 (2026-11-10): Fase 3 en `phase-3-intelligence`, base `f6ac68a` preservada en `phase-2-baseline`. Proveedor dentro del proceso de voz existente, ruta rápida más ONNX semántico y Ollama loopback, contratos Pydantic y validador independiente. Ejecutor exclusivamente de simulación y contexto volátil. Qwen3:1.7b y E5 elegidos provisionalmente por mediciones locales; se conservan comparativas con Qwen3.5:2b y MiniLM. Los modelos crudos fallaron varias categorías: no se acredita precisión general del 95%. 189 pruebas aprobadas y corpus escrito de 328 casos / 363 turnos, con revisión declarada. Medición separada del servicio externo, pruebas sintéticas fallidas conservadas y aceptación física pendiente. Sin herramientas reales de Fase 4 ni cambio de la configuración de audio aceptada. Ver `phase_3.md`, `model_comparison.md` e `intelligence_validation.md`.

0.2.0: Fase 2 en rama `phase-2-voice`; base guardada como `695c068`. Se conservó el núcleo y sus 62 pruebas. Proceso de voz bajo demanda con cola PCM limitada, modelos CPU locales, Silero común a ambos STT, respuestas deterministas, Piper y salida cancelable, semidúplex por timestamps y retención compartida de 90 s. Modelos y descargas explícitos fuera del residente, configuración de voz separada y privacidad de transcripciones desactivada por defecto. Comparación sintética reproducible y corpus voluntario de 60 frases. Aceptación física pendiente; ver `voice_validation.md`. Se corrigió la reutilización de la cola EOF del adaptador Rustpotter al reiniciar solo el detector después de una sesión.

0.1.0: estado y eventos, configuración, captura y remuestreo, integración binaria Rustpotter, calibración consentida, bandeja, notificaciones Windows, recuperación limitada, mutex, Job Object, scripts del Programador, mediciones, pruebas y documentación. Sin funcionalidades de Fase 2.
