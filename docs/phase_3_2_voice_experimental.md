# Fase 3.2 — Consolidación y primera integración de voz

15 de noviembre de 2026. Continuación desde `731917a`. **La Fase 3.2 permanece abierta**: hay un perfil de voz experimental implementado y comprobaciones técnicas, pero la aceptación con la voz real del usuario sigue pendiente y la primera integración sintética falla en STT.

## Referencia textual sellada y plazo

Antes de tocar el motor se sellaron 32 turnos: 29 textos nuevos y tres controles directos conocidos. El [protocolo](evaluation/NEXT_CONSOLIDATION_PROTOCOL.md), [conjunto](evaluation/next_consolidation_v1.json) y [primer informe](reports/next-consolidation-first.json) conservan la primera exposición. Es una evaluación interna del mismo autor, no una validación humana independiente. El conjunto se retiró antes de ampliar contexto; no se presenta su puntuación como precisión de la versión posterior.

Groq `openai/gpt-oss-120b`, `medium`, 29 solicitudes sin reintentos: **32/32 turnos correctos**, incluidos **29/29 nuevos**. Las 29 decisiones fueron observables y válidas, 11/11 propuestas de catálogo y 29/29 referencias correctas, sin rechazos de política ni discrepancias del reductor/IDs comprobadas. El router usó la ruta directa en los tres controles y el proveedor en los demás. Cero borradores indebidos y cero timeouts. Estos contadores separados no demuestran una tasa universal ni aíslan causalmente todos los componentes.

El plazo se fijó antes de ejecutar en **4 s**, a partir del p95 previo de 2,476 s más margen. En la referencia nueva la mediana remota fue **1,720 s**, p95 **2,845 s**. El motor, CLI y perfil de voz usan ahora ese mismo plazo por defecto. Es una elección experimental con evidencia limitada; no garantiza cubrir colas o redes lentas. `low` sigue seleccionable y no hay fallback automático.

## Implementación

| Componente | Estado anterior | Cambio realizado | Motivo | Evidencia | Estado final |
|---|---|---|---|---|---|
| Contexto | Plan y revisión textual | Pregunta con intención/parámetro/candidatos/sesión/TTL; referentes RAM; respuestas cortas ligadas | Completar interacción mínima | Regresiones de Spotify, ordinales, referentes y caducidad | Implementado, gramática local acotada |
| Retención y aprobación | Una revisión podía simular un plan retenido | Edición conserva retención; solicitud local de autorización y confirmación separadas | Corregir no equivale a autorizar | Ejemplo obligatorio, IDs conservados y ataques forzados | Solo simulación |
| Respuestas | Mensajes genéricos | Plantillas locales por resultado y propuesta completa | Preguntas y confirmaciones comprensibles sin otra consulta | Pruebas de conversación | Implementado |
| Voz | Residente con motor anterior | Perfil Next exclusivo mediante fábrica perezosa | Reutilizar Rustpotter, VAD, Moonshine y Piper | Pruebas de trabajador y sondeos nativos | Experimental |
| Confirmación hablada | `:confirm ID` | «Sí» ligado al borrador exacto y vigente, armado tras presentación completa | No confirmar contenido que aún no se ha oído | Prueba de dos turnos por el trabajador y rechazos sin presentación | Sin permiso físico |
| Vigencia | Control del motor | `can_publish` antes de Piper, tras carga y entre chunks; cancelación compartida | Descartar respuestas tardías o de otra sesión | Caducidad, cambio de sesión y cancelación durante carga/proveedor | Implementado |
| Recursos | Valores históricos | Dos reposos reales de 30 s y banco de sesiones sintéticas | Medir el perfil nuevo sin atribuirle cifras antiguas | Informes conservados | Muestra corta; falta uso real prolongado |
| STT | Reconocedor personal existente | Comparador dirigido local y selección temporal opcional | Investigar errores sin sustituir el motor por intuición | Seis clips idénticos por perfil | Ningún cambio persistente |

Detalles del [contexto mínimo](phase_3_2_context_minimum.md): preguntas de 45 s, revisiones de hasta 30 s y referentes de hasta 120 s, ligados a sesión/revisión. Cancelar elimina plan, pregunta, referente y confirmación. «No» ante un borrador lo descarta sin cancelar el plan anterior. Las formas locales cubren los ejemplos obligatorios; no se afirma cobertura de cualquier paráfrasis de aclaración ni memoria histórica compleja.

Flujo implementado: **Rustpotter → captura/VAD → STT local → NextConversation/NextEngine → directo o Groq → política/contexto → simulación → Piper**. El perfil Next no importa E5, Qwen ni la inteligencia anterior, ni inicia su servicio. La arquitectura anterior queda seleccionable como perfil legacy y recuperable en Git; no funciona como segundo intérprete simultáneo.

Groq recibe solo texto y contexto mínimo bajo demanda. No se envía audio. No se conecta el oráculo del evaluador al residente. `request_mode`, JSON válido y Medium siguen siendo declaraciones del proveedor, no autorización. `authorize_plan` solo puede ofrecerse a partir de una solicitud local reconstruida y requiere confirmación posterior; el proveedor no puede concedérsela.

El inicio Next es explícito, no modifica el arranque automático ni archivos personales. Se conservaron micrófono, umbral, referencia, VAD y salida existentes. Un guardado local de hashes verificó que `config.json`, `voice.json`, configuración de inteligencia y referencia de activación no cambiaron durante los sondeos. La prueba del lanzador offline de ocho segundos cerró con código 0.

## Primera prueba sintética de voz: resultado fallido conservado

El [primer informe](reports/next-voice-synthetic-first.json) usa el código `5d1bbd3`: micrófono sintético alimentado en tiempo real, referencia Rustpotter temporal entrenada con Piper, Silero, Moonshine, Next y reproducción Piper reales. No usa audio personal ni cambia la referencia del usuario. La [lectura complementaria](reports/next-voice-synthetic-first.analysis.json) conserva hash de procedencia, discrepancias STT y efectos de fallos previos; no reescribe la prueba.

Resultado: **1/9 turnos y 0/3 secuencias**. «Abre una aplicación» fue reconocido y generó la pregunta correcta. «Spotify» se transcribió como «pot dirfe», «Sí» como «St.» y otras frases también cambiaron. Las ocho discrepancias fallidas ya eran observables en STT; esto no demuestra que STT sea su única causa ni prueba que todos los pasos posteriores fueran correctos. Las dependencias tras un fallo quedan marcadas. Hubo además un rechazo remoto de contrato al interpretar una transcripción incorrecta. Solo los dos turnos del caso remoto enviaron texto a Groq; los otros casos se probaron offline. No se corrigieron transcripciones a mano ni se confirmaron borradores por expectativas.

Se reforzó después de esa prueba el armado de confirmación hablada: requiere que Piper haya presentado la propuesta completa, con sesión, revisión y caducidad todavía válidas. El refuerzo está comprobado en integración del trabajador con transporte/STT/TTS simulados; no se atribuye una nueva puntuación al mismo audio.

## Tiempos y consumo, con límites

La instrumentación separa final de frase, finalización STT, interpretación, validación/contexto, preparación de Piper, primer chunk e inicio de reproducción. STT es streaming: parte de su trabajo coincide con captura. La instrumentación final ancla el fin de voz al callback de captura y conserva el retraso de cola; no mide la latencia física del dispositivo. Los errores del proveedor mantienen categorías normalizadas y una fase cerrada cuando es observable.

En la primera prueba nativa, anterior a la corrección del reloj de cola, los nueve inicios de respuesta estimados —incluidas respuestas a transcripciones incorrectas— tuvieron mediana **1,701 s** y máximo **11,341 s**. No son latencias de órdenes correctas ni una aceptación de extremo a extremo. La carga fría de Piper consumió **5,453–7,375 s** en los tres primeros turnos; los siguientes reutilizaron la instancia. La finalización STT observada fue de **0–0,031 s**, pero no incluye su trabajo streaming ni su carga inicial. La espera remota de los dos turnos fue de **1,215–2,416 s**, incluido el contrato del adaptador. La validación local de la respuesta observable fue inferior a 1 ms en esa muestra mínima. Hay que medir de nuevo con la voz del usuario y el reloj final.

| Reposo real, 30 s | CPU media del árbol / CPU total | RSS pico muestreado |
|---|---:|---:|
| Next offline | 0,576 % | 88,4 MiB |
| Next con remoto habilitado | 0,634 % | 88,6 MiB |

Fuentes: [offline](reports/next-resident-idle-30s.json), [remoto habilitado](reports/next-resident-remote-idle-30s.json). Bandeja Qt, micrófono y Rustpotter reales, referencia sintética: cero activaciones, cero sesiones y trabajador pesado no creado. No hubo solicitudes Groq en reposo. Son seis muestras por sondeo, incluyen inicio y cierre y no prueban estabilidad prolongada ni rendimiento durante juegos. No se afirma una mejora respecto a los históricos de 0,365 % y 89,3 MB.

Durante las sesiones sintéticas se observaron máximos muestreados del árbol del banco de pruebas de aproximadamente **554–578 MiB**, con medias de muestras CPU de **0,71–1,38 %**. Incluyen el proceso del arnés y no representan consumo exclusivo del residente. El texto de método heredado de ese informe menciona cinco segundos, pero el arnés muestreó en límites de turno; las medias son no ponderadas y los picos reales pueden ser mayores. La anotación complementaria aclara este límite. No se midió GPU ni FPS.

## Comparación dirigida de STT y entrega

Se generaron una sola vez seis clips adicionales y se suministraron los mismos arrays a Moonshine Small y Whisper Base, ambos ya instalados, sin descargas ni red. El [informe](reports/next-stt-directed-synthetic.json) conserva hashes de los estímulos: **1/6 transcripciones normalizadas exactas para Moonshine y 0/6 para Whisper**. Es otra generación sintética, no una reproducción de los clips exactos de la primera integración. No identifica por sí sola si el problema dominante es pronunciación sintética, reconocedor o combinación. No justifica sustituir la selección personal. El comparador acepta también grabaciones locales autorizadas; esos archivos e informes personales quedan fuera de Git.

La suite local final pasa **599 pruebas**. CI conserva pruebas offline sin credenciales ni llamadas externas, incluidas fábrica exclusiva Next y confirmación hablada pasando por el trabajador. Se verificaron compilación, enlaces/documentos, escaneo de credenciales, arranque/cierre y preservación de la restauración de 3.1. Los resultados físicos del usuario, juegos, suspensión real y reconocimiento con su voz no se declaran aprobados por estas pruebas.

Para probarlo, seguir la [guía física breve](next_voice_quick_test.md). El siguiente bloque debe usar esa evidencia para decidir mejoras de STT y de la primera respuesta fría de Piper. No seguir ajustando el prompt a los fallos sintéticos, no habilitar herramientas físicas y no cerrar la Fase 3.2 todavía.
