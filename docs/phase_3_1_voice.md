# Voz y recuperación — Fase 3.1

Se conservan micrófono, referencia personal, umbral 0.55, VAD/silencio de 1200 ms y semidúplex. No se habilita interrupción hablada durante síntesis o inferencia; la bandeja conserva cancelación.

## Comparación de STT

`scripts/compare_phase31_stt.py` genera una única colección de 16 estímulos Piper en RAM, publica sus hashes y pasa exactamente los mismos arrays a Moonshine con afinidad de dos y cuatro CPU lógicas y a Whisper base con dos. Incluye las diez frases cortas pedidas, la secuencia principal de luces y dos frases históricas. No usa micrófono ni reproduce audio. Moonshine recibe bloques a ritmo de 32 ms; Whisper procesa audio completo. Los resultados crudos se preservan en `reports/phase31-stt-comparison.json`.

Moonshine reconoció exactamente 2/16 textos en ambos perfiles y produjo los mismos textos con dos y cuatro CPU. Whisper base reconoció exactamente 1/16. Ambos fallaron varias frases cortas y la petición corta inicial de luces. Esto demuestra un problema con estos estímulos sintéticos, no una tasa de error de la voz del usuario. Tampoco demuestra que elevar afinidad corrija reconocimiento. No se alteraron los textos esperados, se añadieron alias acústicos ni se repitió el corpus hasta presentarlo como aprobado.

## Recuperación conservadora

Una frase reconocible sin destino fiable, como «ponla en lo principal de color rojo», genera una aclaración sobre la luz; no genera una luz inventada. La información de color se conserva y el destino necesita una respuesta explícita. Los fragmentos cortos incoherentes durante una propuesta pueden pedir repetir, en lugar de enviarse al LLM como si fuesen órdenes completas. Las preguntas y seguimientos conversacionales mantienen su ruta normal.

Existe una segunda transcripción **opcional, desactivada por defecto**: `voice.stt_recovery_enabled`. Solo se solicita ante una duda concreta, con 320 ms de actividad VAD y 0.5–20 s de audio acumulado. Carga el Whisper base ya instalado en un subproceso, una vez y de forma secuencial. No descarga nada. `stt_recovery_timeout_seconds=8` limita el trabajo, con cancelación y terminación del proceso propio al vencer el plazo. El audio no sale de RAM y se descarta tras el turno.

La alternativa debe conservar colores, números y entidades ya reconocidos y superar el mismo validador. Una contradicción provoca aclaración. El resultado también está ligado a la revisión/sesión anterior a la recuperación, para que no pueda sobrescribir un turno nuevo. Dada la comparación anterior, no hay evidencia para activarla universalmente ni sustituir Moonshine por Whisper. Su utilidad física queda pendiente.

## Diagnóstico voluntario

Cerrar el residente antes de estos scripts; usan el mismo mutex para impedir una segunda captura simultánea.

```powershell
.\.venv\Scripts\python.exe scripts\diagnose_voice_session.py --seconds 90
# Solo si quieres guardar voluntariamente el texto de esta sesión en un informe local:
.\.venv\Scripts\python.exe scripts\diagnose_voice_session.py --seconds 90 --include-text
.\.venv\Scripts\python.exe scripts\diagnose_wakeword.py --attempts 10 --window 5 --noise-seconds 30
```

El diagnóstico de voz usa configuración temporal y no cambia la privacidad del residente. La prueba semántica se separa: este diagnóstico de captura deshabilita E5 temporalmente para atribuir fallos. El informe contiene estados, sesiones/turnos, límites de audio, motor, ruta, validación, revisiones y latencias. Con `--include-text` añade original, transcripción seleccionada, normalización y respuesta. Los informes se guardan únicamente en `%LOCALAPPDATA%\JarvisCore\diagnostics`; no subir conversaciones personales a Git.

La prueba de activación solicita que el usuario marque cada intento y diga Jarvis una vez. Así existe denominador para intentos perdidos. Registra el dispositivo, estado, umbral y puntuaciones de detecciones aceptadas disponibles. No inventa puntuaciones de intentos rechazados que Rustpotter no publica. La ventana de ruido se etiqueta como ausencia de palabra de activación. No cambia umbral, referencia ni micrófono. Comparar distancia/ruido/micrófonos en sesiones separadas y conservar también falsos positivos antes de decidir una recalibración.

No se ejecutaron estos procedimientos con voz del usuario durante desarrollo. Quedan pendientes habla espontánea, audífonos si el usuario decide usarlos, pausas, música y calibración física.

## Integración final sintética A–F

El informe `reports/phase31-voice-integration.json` conserva los 18 turnos originales, transcripciones, decisiones y eventos. Solo 7 cumplieron el criterio de categoría/acción; 11 fallaron y ninguna secuencia pasó completa. No se puntúa calidad de la respuesta conversacional. «Dame un ejemplo» se reconoció correctamente pero produjo aclaración; otros fallos son acústicos, como Steam → Sta. y Cancela → En la danza de la ciudad. Mediana fin estimado de voz → reproducción: 6,943 s (1,451–18,169), incluidos fallos y cargas. Cero errores del proceso y cero bloques perdidos; esto demuestra transporte e integración, no reconocimiento fiable.

Los informes `phase31-voice-integration-harness-v1.json` y `-v2.json` se conservan como inválidos para exactitud: espera fija y una carrera al comprobar IDLE, respectivamente. El ensayo corregido espera consumo de la activación y estado de escucha; mantiene frases y expectativas. Sus seis activaciones acústicas sintéticas no son una medida de wakeword con voz humana. No hay evidencia para cambiar micrófono, umbral ni motor predeterminado a partir de estos clips.
