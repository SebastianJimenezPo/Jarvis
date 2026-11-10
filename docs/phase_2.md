# Fase 2 — Voice Engine

Implementación sobre Fase 1, rama `phase-2-voice`. Base recuperable: commit `695c068`. La implementación está preparada para validación con el usuario; **no se declara aceptada físicamente la Fase 2**.

## Instalación reproducible

Conserva el checkout y entorno de Fase 1. Para recrear las dependencias de ambas fases en Python 3.11:

```powershell
python -m uv pip install --python .venv\Scripts\python.exe -r requirements-voice-lock.txt
python -m uv pip install --python .venv\Scripts\python.exe --no-deps -e .
.\.venv\Scripts\python.exe scripts\install_voice_models.py moonshine-small moonshine-tiny whisper-base silero es_MX-ald-medium es_ES-davefx-medium
.\.venv\Scripts\python.exe -m jarvis --enable-voice
```

Las descargas se ejecutan solo con ese comando explícito de instalación. No existe descarga automática al activar Jarvis. Los modelos viven en `%LOCALAPPDATA%\JarvisCore\models`; `registry.json` registra rutas, origen, arquitectura/revisión y SHA-256. Moonshine verifica además tamaño/CRC del manifiesto oficial. Piper está fijado a la revisión indicada en el instalador, Silero a v6.2 y Whisper registra su revisión Hugging Face. Los adaptadores verifican hashes al cargar. El registro permanece en el perfil, fuera de Git.

Instalados y probados: `moonshine-voice==0.1.6`, `faster-whisper==1.2.1`, `piper-tts==1.8.0`, `onnxruntime==1.31.1`. No se instalaron torch, CUDA ni un LLM. Whisper Small es una opción del adaptador, pero no se descargó: se evaluó Base para limitar el volumen de instalación.

## Uso

Inicia como antes: `python -m jarvis --debug` para desarrollo o el lanzador pythonw para residente. El inicio automático existente conserva su ruta. Con voz habilitada:

1. Di «Jarvis, ¿me escuchas bien?» o «Jarvis», espera brevemente y habla.
2. Obtendrás una respuesta de prueba local. Durante su reproducción espera a que termine: el modo actual es semidúplex.
3. Puedes continuar sin repetir el nombre: «Perfecto», «Gracias», «¿Cómo estás?».
4. «Adiós» finaliza la sesión. Sin interacción, la espera inicial es de 6 s y la de seguimiento de 25 s.

Solo existen respuestas deterministas; una petición de abrir aplicaciones explica que esa función aún no está habilitada. La respuesta genérica no ejecuta ninguna acción. El reconocimiento puede equivocarse: estas coincidencias de prueba no representan comprensión general.

El menú mantiene los controles de Fase 1 y añade prueba Piper, cancelación de respuesta, respuestas habladas y selección STT. El control «Probar transcripción» activa una sesión de diagnóstico manual para que hables; no crea otro micrófono. Si seleccionas un modelo no instalado, los diagnósticos lo indican y se conserva el ciclo de activación de Fase 1.

«Repetir reconocimiento (diagnóstico)» activa/desactiva la repetición hablada del texto reconocido, sin habilitar registros de texto. En modo normal, un primer turno con un único token desconocido se trata como ambiguo y conserva la escucha, porque el nombre dentro del pre-roll puede transcribirse mal. Esto también puede silenciar otra palabra desconocida aislada al inicio; las frases completas y saludos conocidos se mantienen. En diagnóstico ese filtro no se aplica para poder escuchar el resultado real de STT.

Para cambiar ajustes persistentes y reiniciar:

```powershell
.\.venv\Scripts\python.exe -m jarvis --set-stt moonshine-tiny
.\.venv\Scripts\python.exe -m jarvis --set-voice es_ES-davefx-medium
.\.venv\Scripts\python.exe -m jarvis --disable-voice
```

`--disable-voice` conserva la captura y activación de Fase 1. El motor provisional sigue siendo Moonshine Small, a la espera de comparar grabaciones reales del usuario; Tiny ya está instalado y es más rápido en el banco sintético.

## Configuración y privacidad

El archivo de Fase 1 no cambia. `voice.json` es un archivo separado, validado y versionado; si no existe, voz permanece deshabilitada. Los valores definidos en `jarvis/speech/settings.py` son la fuente de verdad:

| Ajuste | Inicial | Rango |
|---|---:|---|
| enabled | false | booleano; habilitado explícitamente en este equipo para pruebas |
| engine | moonshine-small | small/tiny de Moonshine, base/small de Whisper |
| voice | es_MX-ald-medium | voz instalada en registro |
| tts_enabled | true | booleano |
| log_transcripts / diagnostic_echo | false / false | habilitación explícita; el segundo repite en voz el texto reconocido |
| first_wait_seconds / followup_seconds | 6 / 25 | 1–60 / 1–120 |
| max_turn_seconds / max_session_seconds | 20 / 600 | 1–60 / 30–1800 |
| preparation_timeout_seconds / processing_timeout_seconds | 60 / 60 | 5–180 |
| retain_seconds | 90 | 0–600; retención común del proceso de modelos |
| speech_start_ms / end_silence_ms | 200 / 650 | 32–1000 / 200–2000 |
| activation_tail_ms | 250 | 0–500; margen de voz restante tras detección, solo para primer turno de activación acústica |
| vad_threshold | 0.5 | 0.01–0.99 |
| echo_guard_seconds | 0.4 | 0.1–2 |
| pending_audio_seconds | 40 | 5–90; capacidad aproximada para bloques de 20 ms |
| cpu_threads | 4 | 1–8; controla Whisper y Piper, Silero usa 1; Moonshine no expone ese control en esta versión |
| volume / output_device | 0.75 / auto | 0–1 / nombre de salida exacto o auto |

No se guardan muestras del residente. Por defecto, se eliminan textos de los eventos antes de registrarlos y la última transcripción queda `null`. Puedes habilitar `log_transcripts` editando `voice.json` si necesitas verlos; reinicia. No se registran las respuestas generadas salvo que el propio proveedor las incluya en un diagnóstico voluntario. Los archivos de benchmark sí contienen textos de referencia y resultados porque se producen mediante una ejecución explícita.

No hay un modo full-duplex ni identificación del hablante. Voces de videos, personas o juegos pueden contar como voz durante una sesión abierta. Usar auriculares y medir falsos turnos sigue siendo necesario.

## Corpus y benchmark voluntario

`docs/voice_corpus.json` contiene 60 frases: español cotidiano, negaciones, condiciones, nombres de programas y canciones. Alterna distancias, ritmos y ruido en grupos separados y anota las condiciones junto al manifiesto. No se reutilizan muestras privadas de calibración.

Con Jarvis cerrado:

```powershell
.\.venv\Scripts\python.exe scripts\record_voice_dataset.py --output '.\build\mi-voz' --count 10
# Otro bloque, sin sobrescribir grabaciones existentes:
.\.venv\Scripts\python.exe scripts\record_voice_dataset.py --output '.\build\mi-voz' --start 11 --count 10
.\.venv\Scripts\python.exe scripts\speech_benchmark.py --dataset '.\build\mi-voz\manifest.jsonl' --output '.\build\mi-comparacion.json'
```

La herramienta solicita escribir `GUARDAR`, muestra HABLA una vez abierto el micrófono, graba hasta 8 s y pregunta si quieres conservar cada muestra. Guarda solo las aceptadas. Cada WAV se evalúa en los mismos motores. Añade una muestra de silencio con texto vacío al manifiesto para medir alucinaciones en silencio. Se usa PCM16, mono o multicanal convertido a mono.

Lee también `voice_architecture.md`, `stt_benchmark.md` y `voice_validation.md`.
