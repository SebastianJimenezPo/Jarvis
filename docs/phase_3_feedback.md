# Ajustes después de las pruebas del usuario — 2026-11-10

El usuario comprobó órdenes/correcciones y negaciones/condiciones; la conversación mantuvo contexto con demoras. Informó fallos en aclaraciones y cancelación, dificultad ocasional de activación, picos cercanos al 30% de CPU y aproximadamente 1.3 GB en Python. La comprobación de cancelación fue aproximada. Esto no constituye todavía cierre de fase ni validación de estabilidad prolongada.

## Causas y cambios

- «Pon las luces de otro color» no tenía un camino determinista que guardase el color faltante. Ahora pregunta el color, acepta una respuesta como «azul» y valida el resultado sin LLM. Aclaraciones de volumen guardan el valor faltante; «ciento veinte» ya no puede reducirse a veinte. Una nueva orden reemplaza una pregunta pendiente; no se intenta usarla como respuesta sobre otra aplicación.
- La puntuación insertada por STT en «Por favor, pon…» podía desviar una orden directa hacia el LLM. Se quita esa fórmula de cortesía antes de interpretar, conservando la cláusula real para la validación independiente. Se añadieron regresiones con coma inicial, cortesía final y aclaración pendiente.
- Se amplían las variantes explícitas de cancelación. Además, el filtro de primera palabra podía descartar «cancela» como una transcripción ambigua de la activación. Se permite como palabra conocida, se limpia contexto y termina la sesión. Los registros anteriores contenían dos cancelaciones reconocidas; al no registrar transcripciones no se puede atribuir con certeza cada fallo físico al filtro o al STT.
- El motor semántico E5 se consultaba ante casi cualquier texto desconocido, incluso conversación sin acciones de sus seis intenciones. Ahora solo se carga con evidencia de operaciones compatibles de audio o luces. Sigue disponible para esas peticiones y conserva validación independiente.
- La conversación se orienta a Windows y uso del computador, con una o dos frases cortas por defecto. Presupuesto de salida conversacional 160 tokens. No se han añadido herramientas reales ni lecturas de estado del sistema.
- LLM: dos hilos solicitados y retención 30 s. Voz: afinidad de dos CPU lógicas y prioridad inferior a normal solo en su subproceso Windows, retención 20 s después del fin de sesión. Silero, Piper y embeddings no realizan espera activa de sus pools ONNX. Micrófono, voz, tono y silencio final de 1200 ms se conservan.

## Mediciones

`reports/phase3-feedback-memory.json` compara dos procesos nuevos con Moonshine, Silero y Piper reales. Uno fuerza la antigua carga innecesaria de E5; el otro usa la nueva puerta de conversación. Ambos usan bibliotecas y perfil CPU actuales. No hay micrófono, reproducción ni inferencia LLM: la respuesta del LLM está simulada para aislar memoria Python.

RSS del proceso que contiene modelos después de la misma pregunta: **1151 MB frente a 401 MB decimales** (aproximadamente 1098 frente a 382 MiB). No es consumo total del asistente ni una garantía para cualquier sesión: E5 todavía ocupa memoria cuando se necesita y Ollama se mide aparte. El muestreo incluye el lanzador Python de Windows y sus descendientes; los datos temporales incluyen una espera de muestreo de 300 ms y no deben usarse para comparar latencia conversacional.

LLM real, misma petición corta y modelo descargado de RAM entre ensayos:

| Hilos solicitados | CPU media de máquina | Tiempo total | RAM pico del árbol Ollama |
| --- | --- | --- | --- |
| 4 | 13.83% | 3.55 s | 1687 MB |
| 2 | 7.36% | 6.05 s | 1687 MB |

Informes `phase3-feedback-llm-4threads.json` y `phase3-feedback-llm-2threads.json`. Una muestra por perfil; la carga fría y caché de disco varían. La generación fue también más lenta con dos hilos. Son promedios, no topes instantáneos ni pruebas durante juego. Reducir CPU no elimina la RAM propia del LLM, y puede aumentar la espera.

Regresión escrita principal: 303 turnos sin fallos en el conjunto ya revisado. Desafío adicional sin LLM: 60 turnos, 96.67% de categorías, parámetros 100%; conserva dos aclaraciones por conversación sin LLM. Informes `phase3-feedback-intent-regression.json` y `phase3-feedback-challenge-degraded.json`. No son nuevos conjuntos independientes. La batería completa pasa 218 pruebas (`reports/pytest-phase3-feedback.txt`). Las nuevas pruebas cubren los fallos reportados, conservación de planes, negaciones al aclarar, cancelación en primer turno, rangos y carga semántica innecesaria.

Integración hablada sintética con perfil de dos CPU: el primer ensayo detectó el defecto de la coma y se conserva en `phase3-feedback-voice-polite-comma-failed.json`. Después de corregirlo, el ensayo `phase3-feedback-voice-integration.json` reconoció «cancela la solicitud por favor», clasificó cancelación y terminó la sesión correctamente, sin pérdidas ni reinicios. **El ensayo completo sigue marcado como fallido**: Moonshine transcribió la petición inicial de luz como «ponla en lo principal de color rojo», por lo que no se formó el plan rojo/azul. No se añadieron alias para inventar la luz a partir de esa transcripción. El STT con frases variables sigue pendiente de evaluación; no se presenta la integración completa como aprobada ni se repite hasta ocultar ese fallo.

## Pendientes físicos

Repetir aclaración de aplicación seguida de color, cancelar al inicio y después de una propuesta, observar RAM tras 60 s sin hablar y CPU durante una pregunta corta del computador. La voz no escucha durante su propia reproducción o procesamiento (semidúplex); para cancelar en esos estados usar la bandeja. No se ha habilitado interrupción por voz durante reproducción.

Activación: se mantiene umbral 0.55. Los registros disponibles muestran activaciones aceptadas, no todos los intentos rechazados; no permiten calcular sensibilidad o falsas activaciones. No se redujo el umbral sin nuevas muestras y comprobaciones físicas. Queda pendiente calibrar con el usuario si persiste la dificultad, respetando su decisión previa sobre micrófono y espera tras el tono.
