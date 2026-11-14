# Fase 3.1 — informe de preparación, 2026-11-14

Versión 0.3.1 en `phase-3-1-hardening`, repositorio [Jarvis](https://github.com/SebastianJimenezPo/Jarvis/tree/phase-3-1-hardening). Base `fed3f113455c6e867283b4959a5f21bdd0c35d4b` conservada en `phase-3-intelligence`. Documento solicitado: [especificación íntegra](phase_3_1_spec.md).

**Preparación parcial: mantener simulación y continuar estabilización antes de Fase 4. Fase 3.1 no cerrada.** La revisión mejora validación y coherencia, pero la evaluación nueva conserva errores de comprensión y cancelación, y el STT sintético falla frases cortas. No hay evidencia física nueva con la voz del usuario ni mediciones durante videojuegos. Las propuestas no ejecutan acciones en Windows o dispositivos.

## Cambios y evidencia

| Problema | Estado anterior | Cambio realizado | Prueba | Estado final |
| --- | --- | --- | --- | --- |
| Temporalidad | Subordinadas y condiciones podían producir propuestas inmediatas. | Análisis global de acto/alcance; distinción del pasado relativo; abstención ante alcance no interpretado. | Reproducciones previas; crítico v1 falló 3/104 y fue retirado; crítico v2 nuevo: 0/104 autorizaciones indebidas. | Mejorado; no garantiza cobertura de todo el español. |
| Correcciones | reason_code o ruta rápida podían sustituir evidencia y saltarse prohibiciones. | Validación idéntica para todas las rutas; operación/objetivo/parámetro fundamentados; plan retenido no se reactiva por elipsis. | 1.062 propuestas forzadas contra validador, 0 bypasses en crítico v2; regresiones específicas. | Verificado en casos internos; sigue solo simulación. |
| Contexto | Interpretación podía mutar estado antes del rechazo o aceptar resultados tardíos. | Copias acotadas y confirmación atómica con revisión/sesión/caducidad/cancelación; planes con IDs y dependencias. | Rechazo sin mutación, carreras, caducidad, respuestas fuera de orden, snapshots y límites. | Pruebas automáticas pasan; estabilidad física prolongada pendiente. |
| Aclaraciones | Negar una cancelación podía borrar pending; ampliaciones perdían partes del plan. | Conservación, rechazo de alternativa, cambio de solicitud y cancelación selectiva diferenciados. | Regresiones; contexto reservado 95,6%; 23 aclaraciones correctas y 9 innecesarias. | Parcial: «Olvida todo lo anterior» se clasificó como conversación. |
| Normalización | Conjunciones numéricas, correcciones cortas y objetivos absolutos se confundían. | Preservación de signos/fracciones/decimales, números compuestos y foco; rangos y dirección revalidados. | Pruebas numéricas/coloquiales; parámetros reservados 84,5%. | Parcial: vocabulario conservador rechaza también solicitudes válidas. |
| Voz | Errores STT en frases cortas; sin diagnóstico para atribuirlos. | Trazas optativas privadas, repetición/aclaración y segunda transcripción acotada y cancelable, desactivada por defecto. | Comparación de 16 clips idénticos; integración A–F; guía física separada. | No se acredita mejora acústica real ni precisión de la voz del usuario. |
| Rendimiento | CPU y RAM activas elevadas; coste de perfiles sin comparación repetida. | 2/3/4 hilos comparados, caché solo de metadatos, E5 diferido/descargable, perfiles manuales. | 54 solicitudes reales; retención, streaming, E5 y reposo con procesos separados. | Se conserva gaming de dos hilos; impacto durante juego pendiente. |

## Automatización y regresión

La línea base pasó 218 pruebas. La batería local completa final pasó **379 pruebas, cero fallos**, en 26,97 s (`reports/pytest-phase31-final.txt`). Antes de corregir, 23 de 38 reproducciones iniciales fallaron; ambas salidas se conservan. La selección headless actual pasó 374 pruebas localmente y excluyó 5 con dependencias de modelos, auxiliar nativo o GUI. CI en un Windows nuevo pasó 373, omitió una prueba de instalación explícita de voz y excluyó las mismas 5: [ejecución verificada](https://github.com/SebastianJimenezPo/Jarvis/actions/runs/43631160253). No descarga modelos para aprobar pruebas unitarias.

Los corpus anteriores se volvieron a ejecutar como **regresión con reglas, LLM y semántica deshabilitados**: 303 turnos, un desacuerdo; desafío 60 turnos, cuatro desacuerdos. Cero propuestas inesperadas en ambos. Se conservan las cinco diferencias: «Por favor Busca Hotel California», «Bájale tantico al sonido», «Necesito que abras Discord» y dos conversaciones que requieren LLM en este modo. Son resultados de regresión, no evaluación nueva ni prueba del modo híbrido completo. La abstención adicional tiene coste funcional y no se oculta como aprobación total.

## Evaluación reservada

Motor de inteligencia congelado en `9522150`; hashes de cada módulo, casos y resultados en `docs/evaluation` y `docs/reports`. El manifiesto final tiene SHA256 `a125b07c5b739994aa575567d2dae644635bd170dfdd001b2943bd816a1a3f1d`. El general original no se alteró ni evaluó para ajustar las reglas. Los ejemplos fueron redactados internamente por el mismo autor después del congelamiento; no son datos externos, voces humanas ni una evaluación ciega por otra persona. Ver [protocolo](evaluation/PROTOCOL.md).

| Medida | Resultado |
| --- | --- |
| General | 156 casos / 181 turnos; un duplicado de desarrollo excluido: 155 casos / 180 turnos nuevos. |
| Clasificación | 86,7% (156/180); 24 turnos con diferencias de clasificación o acciones/parámetros. |
| Propuestas | Precisión 100%; recall 86,4%; parámetros exactos 84,5%. Las omisiones no cuentan como aciertos. |
| Contexto | 95,6% en los turnos de categoría context; no implica éxito físico del diálogo. |
| Aclaraciones | 23 correctas; 9 innecesarias. |
| Negaciones/condiciones | 0 con acciones indebidas en general. |
| Cancelación | 1 no reconocida: «Olvida todo lo anterior». No se debe asumir que borra el plan previo. |
| Abstención | 66,7% de turnos; incluye conversación y otras categorías que no deben proponer acciones. |
| Crítico v2 | 104 escenarios nuevos, 104 turnos prohibidos y 4 preparaciones: 0 propuestas indebidas, 0 bypasses / 1.062 ataques; todas las preparaciones correctas. |

El primer crítico v1 encontró tres autorizaciones indebidas y pasó a desarrollo; su informe fallido se conserva y no se presenta como holdout final. No se modificó el motor con errores del general final o del crítico v2. Si se usan para corregir después, esos datos deberán retirarse del rol reservado y hará falta otra evaluación nueva.

Latencia de interpretación general, sin audio: ruta rápida 140 turnos, mediana 0,91 ms / p95 2,15 ms; LLM 39, mediana 2,276 s / p95 9,225 s; fallback 2, alrededor de 12,02 s por timeout. Ningún turno terminó por ruta semántica: esta evaluación no acredita su exactitud; E5 se probó funcionalmente y en su ciclo de recursos aparte. Incluye el duplicado en latencias, excluido en métricas nuevas.

Ejemplos conservados de límites: «Necesito que cierres Discord», «Quiero que abras Spotify para escuchar música», «Pasa a la siguiente pista musical», «Pon la luz principal amarilla» y «Dame una comparación sencilla». Algunas frases se rechazan por cobertura conservadora de vocabulario/evidencia; otras conversacionales dependen del LLM. Hay dos fallbacks por timeout y errores adicionales devueltos por Ollama; no se silencian ni se reintentan hasta obtener un acierto.

## Recursos y demora

Medianas de tres repeticiones por condición, Qwen CPU: con 2/3/4 hilos la conversación breve preparada tardó 1,571/1,261/1,198 s y la propuesta JSON preparada 3,977/3,267/2,956 s. La CPU preparada media fue aproximadamente 12,5/18,7/25%; máximos muestreados 15,2/21,2/31,3%. Se mantiene el perfil de dos hilos por la prioridad del usuario. Cargas frías y contexto están en [comparación completa](phase_3_1_performance.md). El benchmark usa plazo 45 s, distinto del límite de producción de 12 s.

Ollama y sus descendientes alcanzaron unos 1,66–1,71 GB de RSS; se miden aparte de Python, sin prometer reducir el peso del modelo por limitar hilos. En reposo real de 30 s: CPU media 0,365%, pico 0,625%, RSS pico del residente 89,3 MB y modelos Ollama vacíos antes/después. Es una muestra breve, no estabilidad prolongada. No hay inferencia LLM continua en DORMANT.

E5 aislado: RSS 44,7 MB antes, 820,4 MB cargado, 78,2 MB tras descargar, 823,5 MB al recargar. La salida del proceso de voz también libera sus recursos. No confundir asignaciones rastreadas por Python con memoria nativa ni sumar Ollama como si fuera Python. La retención 30 s descargó el modelo a los 30,375 s observados; el perfil de 60 se descargó manualmente. Streaming conversacional solo adelantó la primera frase completa unos 50 ms frente al final en la sonda breve, por lo que no se añadió complejidad de Piper incremental.

## Voz y aceptación

La comparación usa los mismos 16 estímulos Piper sintéticos, sin micrófono: Moonshine 2 y 4 CPU produjo idénticas transcripciones y 2/16 coincidencias exactas; Whisper base 1/16. No representa una tasa de error con la voz del usuario. No se agregaron sustituciones fonéticas ni se cambiaron frases fallidas para contarlas como aciertos. La alternativa Whisper permanece desactivada.

La integración nueva ejecuta captura PCM sintética, detección acústica Rustpotter con referencia temporal sintética, VAD, Moonshine, diálogo y Piper con salida predeterminada. No usa ni modifica la referencia personal y no valida eco físico. La semántica se desactiva solo en ese ensayo para aislar la cadena de voz. Los resultados A–F se conservan en `reports/phase31-voice-integration.json`. Dos informes anteriores del propio ensayo se preservan como inválidos para exactitud: una espera fija podía atribuir el turno de activación a la orden y una comprobación posterior podía salir antes de que Lifecycle arrancara voz. La revisión del ensayo espera eventos de consumo de la activación y de escucha; no cambia runtime, frases ni expectativas. Esas ejecuciones inválidas no se suman como pruebas aprobadas de STT.

Resultado de integración válida: **7/18 turnos cumplieron el criterio; 11 fallaron y ninguna de las seis secuencias A–F pasó completa**. Hubo seis activaciones acústicas con referencia sintética, todas consumidas antes de inyectar órdenes, sin errores del proceso de voz ni bloques de audio perdidos. El criterio comprueba categoría y acción/objetivo/parámetros, no exactitud de la explicación conversacional. Por ejemplo, la pregunta de RAM se reconoció como «memoria RN» y obtuvo categoría conversación; eso no demuestra una explicación correcta de RAM.

Se conservaron «pon las luces rocas», «Sta.», «En la danza de la ciudad» para Cancela y «Me Fora Soleth.» para Mejor azules. La petición larga histórica roja pasó. «Dame un ejemplo» tuvo transcripción correcta pero terminó en aclaración: es un fallo de interpretación, no de STT. La mediana desde fin estimado de voz hasta inicio de reproducción fue 6,943 s, mínimo 1,451 y máximo 18,169 s en 18 turnos; incluye silencios, STT, carga, LLM y síntesis, también turnos fallidos. Estas demoras no se confunden con la latencia de Qwen aislada.

Las comprobaciones con voz real, ruido, pausas, audífonos, cancelación de bandeja, reinicio/suspensión, 30 minutos y videojuegos se detallan en la [guía física A–F](phase_3_1_physical_checks.md). Se conservan micrófono, umbral 0.55, silencio 1200 ms, privacidad y semidúplex. No se garantiza escuchar «Jarvis» mientras piensa o reproduce voz.

## Reproducir y continuar

Con entorno y modelos instalados explícitamente, cerrar el residente antes de pruebas de voz o GUI:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest -q --strict-markers -m "not models and not native and not gui and not hardware"
.\.venv\Scripts\python.exe scripts\evaluate_phase31_reserved.py --dataset docs/evaluation/phase31_final_reserved.json --split critical --hybrid --output build/critical-repeat.json
.\.venv\Scripts\python.exe scripts\evaluate_phase31_reserved.py --dataset docs/evaluation/phase31_final_reserved.json --split general --hybrid --output build/general-repeat.json
.\.venv\Scripts\python.exe scripts\validate_phase31_voice.py --case all --output build/voice-repeat.json
```

Crear `build` si no existe. Los scripts reservados y de voz rechazan sobrescribir informes; una repetición es comprobación de reproducibilidad, no otro holdout independiente. Los benchmarks no requieren guardar audio personal. No subir informes voluntarios con conversaciones a Git.

Siguiente trabajo recomendado dentro de 3.1: retirar los datos generales del rol reservado antes de usar sus fallos, mejorar cobertura de intención/alcance sin quitar los vetos, corregir cancelación global con reproducción previa y preparar nuevos datos. Después, validar STT y activación con la voz del usuario y medir el impacto durante juego. La preparación parcial permite revisar la implementación; no justifica habilitar herramientas reales.
