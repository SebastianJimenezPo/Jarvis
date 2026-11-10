# Comparación STT — evidencia inicial

Se evaluaron 10 frases generadas por Piper es_MX-ald-medium y un archivo de silencio. Cada archivo se transcribió cinco veces por motor: **55 transcripciones por motor, 165 en total**. Es un corpus **sintético pequeño**, no grabaciones reales del usuario ni 50 frases distintas. Las 60 frases preparadas para grabar están en `voice_corpus.json`.

Cada motor se ejecutó en un proceso nuevo, con exactamente los mismos WAV. STT fuera de línea, sin Silero: las métricas no mezclan errores del VAD con errores de reconocimiento. Se midió desde comenzar a entregar el archivo hasta disponer del final; se añadió un segundo de silencio al audio para terminar streams. Los resultados no son la latencia física del usuario ni una comparación validada de calidad general.

| Motor CPU | WER | CER | Media / mediana / P95 | Carga / recarga | RSS máximo muestreado |
|---|---:|---:|---|---|---:|
| Moonshine Small español | 32,35 % | 13,17 % | 0,312 / 0,255 / 0,786 s | 0,635 / 0,511 s | 284,75 MiB |
| Moonshine Tiny español | 32,35 % | 11,71 % | 0,117 / 0,103 / 0,310 s | 0,302 / 0,197 s | 144,86 MiB |
| faster-whisper Base INT8 | 54,12 % | 22,93 % | 1,193 / 0,805 / 2,402 s | 0,689 / 0,537 s | 163,32 MiB |

Los cinco vacíos por motor corresponden al archivo de silencio repetido cinco veces; no se detectaron alucinaciones en ese silencio. Hubo errores importantes: «Hola» sintético se transcribió mal, y nombres como Jarvis/Chrome y títulos en inglés fallaron. Las preguntas y frases largas sencillas funcionaron mejor. Los informes incluyen los textos y errores por archivo, sin ocultar resultados desfavorables.

WER/CER: distancia de Levenshtein dividida por palabras/caracteres de referencia, agregada en todo el corpus. Se normaliza mayúsculas, Unicode NFC y puntuación; se conservan acentos. Los silencios aportan inserciones al numerador si hay alucinación, sin añadir referencias. Los informes incluyen RTF, latencias por repetición, descarga, recarga, CPU normalizada sobre 16 procesadores y vacíos. RSS se mide tras carga e inferencias, no es pico instantáneo; CPU corresponde a procesamiento activo repetido, no al residente en reposo. La recarga se realizó inmediatamente: no equivale a una carga tras horas con caché de disco fría.

Selección: Small queda como predeterminado **provisional**, por preferencia inicial del proyecto y pendiente de datos reales. Tiny es una alternativa instalada con menor latencia/memoria y el mismo WER en este conjunto. No se declara ganador definitivo ni se extrapola a español colombiano o gaming. Whisper Small se admite en el instalador/adaptador, pero no se instaló sin evidencia que lo justifique.

Reproducir (las muestras generadas no contienen voz del usuario):

```powershell
.\.venv\Scripts\python.exe scripts\generate_speech_fixture.py
.\.venv\Scripts\python.exe scripts\speech_benchmark.py --dataset build\synthetic-speech\manifest.jsonl --repeats 5 --output build\stt-comparison.json
```

Evidencia: `reports/stt-synthetic-benchmark.json`, informes separados `moonshine-small.json`, `moonshine-tiny.json`, `whisper-base.json`.

## Piper

Se sintetizaron las mismas diez frases con dos voces reales del catálogo:

- es_MX-ald-medium: carga 4,045 s, síntesis media preparada 0,071 s.
- es_ES-davefx-medium: carga 2,820 s, síntesis media preparada 0,065 s.

Se elige provisionalmente ald por la variante latinoamericana, pendiente de preferencia auditiva del usuario. Las cargas incluyen importación de Piper y verificación de modelo. La síntesis preparada cumplió la meta inicial; el arranque frío **no** responde en menos de un segundo. En la integración completa el primer chunk frío tardó 4,031 s desde comenzar la preparación de TTS. No se oculta ese coste.

Se ejecutó reproducción física por la salida predeterminada. La API terminó correctamente; oír el sonido y valorar calidad requieren confirmación del usuario. Las tarjetas instaladas declaran Unlicense para el dataset ald y CC0 para davefx. El motor Piper instalado es GPL-3.0; se conserva esta información para futura distribución.
