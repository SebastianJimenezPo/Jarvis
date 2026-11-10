# Validación de Fase 2 — 2026-11-09

## Estado

**Cierre funcional de Fase 2 con observaciones**, acordado al finalizar la ronda de pruebas del usuario. La implementación de voz queda como base para la siguiente fase; este cierre no declara una validación acústica exhaustiva. Se conserva la activación con señal aceptada por el usuario y la selección de micrófono actual. El ajuste final a 1200 ms fue aceptado; no se recibió confirmación explícita de una nueva prueba física de pausa después de aplicarlo. Permanecen documentados el eco físico con altavoces, la elección de micrófono externo y el benchmark de precisión con corpus real. No se inicia Fase 3 sin nueva instrucción del usuario.

Última ronda física: el usuario reportó que el resto de la lista funcionó usando audífonos, con dos condiciones. Prefiere conservar la secuencia de activación/señal actual, aunque la frase completamente inmediata no siempre entre; no se modificó esa conducta. No quedó identificado el micrófono de los audífonos: la captura actual le resulta útil y pidió aplazar ese cambio. No se acredita por ello la prueba de eco con altavoces. El defecto pendiente fue segmentación prematura en pausas menores a un segundo: se aumentó `end_silence_ms` de 650 a 1200 tanto en defaults como en el perfil local, conservando una copia previa. Pruebas comprueban continuidad con pausas de 160/640/960 ms y cierre a ~1216 ms. **108 pruebas superadas en 17,17 s**. Falta confirmar físicamente esta corrección de pausa; no se solicita repetir las demás pruebas ya reportadas.

Actualización más reciente: el usuario repitió varias veces la activación sin frase y confirmó que dejó de producir la respuesta falsa. También confirmó la prueba de varios turnos («me escuchas bien», «Perfecto», «Gracias») y regreso a reposo. Los registros de la sesión `0:7` corroboran varios turnos, fin de reproducción y `session_end` por inactividad ~25,4 s después, seguido de DORMANT. Las palabras exactas no se guardaron por privacidad; la corrección de las respuestas se acredita al reporte del usuario. Suite vigente: **105 pruebas superadas en 16,89 s**. Quedan pendientes las pruebas físicas de eco con altavoces, cancelación, cambios de dispositivo/suspensión con voz y evaluación prolongada/corpus real; las notas anteriores siguientes conservan el historial.

Primera prueba física: el usuario confirmó voz y seguimiento, pero encontró respuestas genéricas incorrectas, incluso al decir solo Jarvis. Se aplicó una corrección conservadora al primer turno ambiguo y a las respuestas deterministas; pendiente de repetir la prueba. Evidencia y limitación: `reports/phase2-first-user-feedback.md`. Suite posterior: **103 pruebas superadas en 14,65 s**.

Implementación integrada, ejecutada con dependencias y modelos reales. **Pendiente de aceptación física por el usuario.** No se declara completada la Fase 2 ni se inicia Fase 3. La Fase 1 queda recuperable en commit `695c068`; el trabajo nuevo está en `phase-2-voice`.

## Evidencia disponible

- Antes de cambios: las 62 pruebas existentes pasaron en 11,70 s. Se mantuvieron sin borrarlas. Resultado final ampliado en `reports/pytest-phase2.txt`.
- Resultado final: **86 pruebas superadas en 14,79 s**, incluidas las 62 pruebas de regresión de Fase 1.
- Se protegió el lanzador `.pyw` con la guarda de entrada necesaria para `multiprocessing` en Windows. Una prueba comprueba que su importación en un proceso hijo no inicia un segundo residente.
- Pruebas nuevas: configuración, retrocompatibilidad, segmentación, pausas, duración máxima, privacidad, descarte de resultados obsoletos, final único por turno, respuestas deterministas, ausencia de acciones, WER/CER, arranque del proceso STT real, silencio y liberación de modelos.
- Prueba de eco controlada: se introduce audio de respuesta en la cola mientras se simula reproducción; no genera otro turno. Se comprueba también cancelación. Esto prueba la lógica de timestamps y semidúplex, **no cancelación acústica física**.
- Se cargaron realmente Moonshine Small/Tiny español, Whisper Base INT8, Silero ONNX y Piper. Los tres STT devolvieron vacío ante el silencio probado. Se corrigió la opción de hilos no admitida por Moonshine; no se simula su aplicación.
- 20 sesiones consecutivas de `VoiceSessionManager`, cada una con la pregunta sintética «¿Me escuchas bien?», conservación del primer tramo mediante pre-roll, final no vacío y cierre por inactividad. No hubo error de supervisor. TTS deshabilitado en ese ensayo: es prueba de control de sesiones y STT, no 20 conversaciones físicas. `reports/voice-pipeline-synthetic.json`.
- Integración completa `LifecycleManager`: diagnóstico manual, captura simulada con pregunta sintética, Rustpotter cargado, STT/VAD reales, diálogo y Piper reales, reproducción en la salida física y retorno a DORMANT. Un turno, cero errores, cero reinicios y cero bloques perdidos. `reports/voice-lifecycle-integration.json`. No demuestra activación acústica con micrófono ni eco físico.
- Piper reproducido por la salida predeterminada sin errores de API. Confirmación audible y preferencia de voz pendientes. `reports/piper-playback-hardware.json`.
- 165 transcripciones reales sobre corpus sintético: 55 por motor. Resultados desfavorables y detalles en `stt_benchmark.md`; no hay corpus real del usuario autorizado todavía.
- Cinco ciclos reales de carga/liberación del proceso de voz con silencio. Árbol del script: ~25–27 MiB antes/después, ~298–301 MiB máximo con Small+VAD cargados. No son la RAM del residente Qt ni de una sesión con Piper cargado. `reports/voice-resource-cycles.json`.

## Reposo y tiempos

`phase2-dormant-60s.json`: aplicación Qt y micrófono reales, código de Fase 2 con voz deshabilitada, referencia sintética temporal. CPU media 0,377 %, RSS máximo muestreado 84,25 MiB, sin pérdidas ni reinicios.

`phase2-enabled-dormant-30s.json`: misma política pero voz **habilitada**, modelos disponibles, sin activaciones. CPU media 0,305 %, RSS máximo muestreado 94,37 MiB, cero pérdidas/reinicios, ningún proceso de voz cargado en reposo. Los experimentos cortos no demuestran estabilidad prolongada. La diferencia RAM no se atribuye a un modelo: ambos quedaron sin proceso de voz; existe variación de working sets/importaciones.

En la integración de un turno: carga STT+VAD 0,750 s; fin estimado de voz→transcripción final 0,688 s (incluye silencio de segmentación); finalización STT 0,016 s; primer chunk Piper frío 4,031 s. El turno completo desde inicio detectado hasta respuesta terminada duró 8,891 s. Audio sintético y activación manual: no son latencias acústicas de usuario. El cold start Piper sigue siendo una limitación real. Síntesis caliente media ~65–71 ms para las frases breves medidas, excluyendo duración de reproducción.

CPU: tiempo usuario+kernel dividido por pared y 16 procesadores lógicos. RSS: suma de working sets padre+hijos, con posible doble conteo de páginas compartidas y sin prometer un pico instantáneo. Los benchmarks STT miden CPU activa; no se deben confundir con el 0,3–0,4 % de reposo. No se midió GPU/FPS; no se declara consumo GPU cero, aunque todos los proveedores configurados son CPU y no se cargó CUDA.

## Prueba física pendiente

Con el residente nuevo activo:

1. «Jarvis, ¿me escuchas bien?» sin pausa. Comprobar que responde «Sí, te escucho». La primera respuesta puede tardar por carga fría.
2. Sin repetir su nombre: «Perfecto», esperar respuesta; «Gracias», esperar respuesta; «Adiós». Comprobar tres respuestas y fin de sesión.
3. «Jarvis», pausa breve, «Hola». Después, «Jarvis» sin frase y esperar cierre silencioso.
4. Frase con pausa interna inferior a 650 ms; luego comparar 650/850/1000 ms configurados según experiencia real.
5. Altavoces: comprobar que no responde a sí mismo. Repetir con audífonos y confirmar el nombre de entrada/salida en diagnósticos.
6. Cancelar una respuesta desde la bandeja. Pausar durante carga, transcripción y reproducción; reanudar y volver a hablar.
7. Suspender/reanudar y cambiar micrófono durante una sesión. Repetir arranque tras iniciar sesión, ahora con Fase 2.
8. Realizar 20 activaciones y 20 conversaciones físicas, grabar voluntariamente al menos 50 frases distintas para comparar STT y evaluar gaming prolongado.

Las verificaciones físicas de Fase 1 no se trasladan automáticamente a una voz nueva. Los modelos se retienen 90 s después de sesión: durante ese tiempo habrá más RAM que en reposo frío, pero no STT continuo. Pausa/salida los liberan inmediatamente mediante cierre supervisado.

## Límites y riesgos conocidos

- El reconocedor puede confundir frases cortas, nombres y canciones. Sin datos reales todavía no existe elección definitiva Small/Tiny/Whisper.
- Silero puede aceptar voces ajenas o de juegos. No identifica al usuario. La sesión tiene duración máxima para limitar ruido sostenido.
- Semidúplex: hablar durante la respuesta puede perder esa intervención. No se implementó barge-in ni AEC.
- Cancelación durante reproducción se comprueba por bloques de ~20 ms, más latencia de dispositivo; una inferencia ONNX ya iniciada no se interrumpe hasta retornar o hasta terminar el proceso por pausa/salida.
- Cambios de endpoint cancelan conservadoramente la sesión. Selección fija por nombre y limitaciones de PortAudio heredadas de Fase 1.
- Cola de arranque limitada a ~40 s. Al agotarla hay error explícito y fin de sesión, nunca una transcripción incompleta presentada como íntegra.
- La primera síntesis tarda varios segundos. Retención caliente reduce ese coste; no se asegura respuesta fría subsegundo.
- Configuración de voz dañada conserva el archivo y deshabilita voz para mantener el núcleo Fase 1; el problema queda en diagnósticos. Modelos ausentes tampoco provocan descargas automáticas.

## Fuentes y licencias

APIs y modelos comprobados contra código instalado y fuentes primarias: [Moonshine](https://github.com/moonshine-ai/moonshine), [API de Moonshine](https://moonshine-voice.readthedocs.io/en/latest/), [faster-whisper](https://github.com/SYSTRAN/faster-whisper), [Silero VAD](https://github.com/snakers4/silero-vad), [Piper](https://github.com/OHF-Voice/piper1-gpl), [catálogo de voces](https://huggingface.co/rhasspy/piper-voices).

Moonshine código y modelos streaming españoles: MIT según catálogo/documentación actual; esto no se extrapola a modelos legacy no streaming. faster-whisper y Silero: MIT. Piper instalado: GPL-3.0. Las tarjetas de las voces se conservaron localmente (ald: dataset Unlicense, davefx: dataset CC0). Las dependencias nativas y avisos deben acompañar una futura distribución; esta entrega sigue siendo el checkout local.
