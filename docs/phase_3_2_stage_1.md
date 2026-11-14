# Jarvis Next — primera etapa, 2026-11-14

Alcance autorizado: auditoría, restauración, contratos y motor textual mínimo con proveedores intercambiables, pruebas y documentación. No implementa toda la Fase 3.2. Especificación íntegra: [documento maestro](phase_3_2_spec.md). La instrucción adicional del usuario limita esta intervención a los cimientos.

## Auditoría y restauración

Inicio limpio en `5337b86901565372a3fbfcc506173d5430114103`. La batería de referencia se repitió antes de modificar: **379 pruebas aprobadas en 21,75 s**. `phase-3-1-hardening` conserva ese commit y el tag anotado `phase-3-1-restore` lo fija explícitamente, publicado en GitHub. Rama nueva: `phase-3-2-jarvis-next`.

| Componente | Decisión | Evidencia / motivo |
| --- | --- | --- |
| Residente, Rustpotter, bandeja, mutex, suspensión e inicio | Conservar | Independientes de comprensión; no hay evidencia para reconstruirlos en esta etapa. |
| Captura, Silero, Moonshine y Piper | Conservar | STT tiene fallos conocidos, pero rehacer voz simultáneamente impediría atribuir resultados. No tocar dispositivo, referencia, umbral ni silencio. |
| Ciclo de vida de trabajadores | Conservar | Liberación y carga bajo demanda verificadas en 3.1. |
| DialogueManager / FastPath | Reconstruir en módulo Next separado | `_candidate` mezcla rutas, recuperación y contexto mutable; `interpret` compone, valida y aplica. La cancelación del modelo solo cambia `operation`, dependiendo de mutaciones previas del intérprete. |
| Validación por vocabulario | Retirar del camino Next | `check_scope_coverage` penaliza lenguaje natural. Next reconoce frases completas en su ruta mínima y delega el resto; no reutiliza ese vocabulario global. |
| E5, Qwen y Ollama | Fuera del camino Next | Ningún resultado final semántico en los 181 turnos anteriores; memoria E5 ~820 MB y Ollama ~1,7 GB activos. No son dependencias de funcionamiento del nuevo motor. |
| Composición libre de control | Sustituir | Las respuestas deben proceder de decisiones/resultados locales, nunca de afirmaciones del modelo. |
| Contratos, revisiones, transacciones y cancelación | Conservar garantías, reconstruir implementación pequeña | Evitar que el nuevo proveedor herede autorización o pueda mutar estado. |
| Pruebas, corpus, informes y CI | Conservar | Son regresión y evidencia histórica; no promesa de generalización ni obligación de conservar todos los detalles internos. |

No se borran todavía los módulos antiguos: el residente de voz sigue usándolos hasta validar la sustitución. Next no los importa ni los carga junto con su motor. La separación temporal permite comparar y volver atrás; no se diseña una cadena obligatoria de dos arquitecturas.

## Decisiones de esta etapa

Entrada nueva inicialmente **textual**, independiente de Windows y de los modelos de voz. Se integra con el residente en un bloque posterior mediante el límite ya existente `DialogueBridge`; no se cambia silenciosamente el asistente que el usuario tiene configurado.

Orden de implementación: contratos y registro mínimo; ruta directa de frases completas; gestor central con revisión y cancelación; proveedor offline/falso con plazo y descarte de respuestas tardías; CLI y pruebas. La interpretación inteligente es un límite sustituible, no una API seleccionada en esta etapa. Groq será el primer candidato del siguiente bloque; antes de elegir modelo/HTTP se consultará su documentación oficial vigente.

La política inicial permite **simulación validada de órdenes directas**. Una propuesta compleja del proveedor puede cumplir el esquema y el catálogo sin demostrar autorización semántica: queda retenida, sin sustituir el plan validado ni producir resultados de herramientas. Esta limitación deliberada es temporal; no se pretende presentar el intérprete falso como comprensión inteligente ni sustituir permanentemente la política semántica con la gramática directa.

No se implementan todavía API remota, proveedor Ollama, memoria persistente, modificaciones contextuales completas, escenas ni herramientas físicas. Las operaciones futuras quedan diferenciadas en los contratos y se rechazan explícitamente si no están implementadas.

## Referencia de métricas

Histórico 3.1, no vuelto a medir aquí: clasificación 86,7%, recall de acciones 86,4%, parámetros 84,5%, contexto 95,6%; crítico final 0/104 propuestas indebidas y 0/1.062 bypasses; voz 7/18 turnos, ninguna secuencia completa y mediana 6,94 s. Reposo de 30 s: CPU media 0,365%, RSS pico 89,3 MB. Ver [informe conservado](phase_3_1.md). No hay nueva medición de residente, micrófono, juegos o API por crear un módulo textual.

## Entrega de la primera etapa

Motor implementado en `21d0b58`; CI y mediciones en `33ea78e`. Rama [phase-3-2-jarvis-next](https://github.com/SebastianJimenezPo/Jarvis/tree/phase-3-2-jarvis-next). Arquitectura y uso: [contratos y límites](jarvis_next_architecture.md). El residente conserva versión 0.3.1; el protocolo nuevo de decisiones tiene versión 1. No se ha publicado como producto 3.2 terminado.

| Componente | Estado anterior | Cambio realizado | Motivo | Evidencia | Estado final |
| --- | --- | --- | --- | --- | --- |
| Restauración | Rama 3.1 en `5337b86` | Tag anotado y rama nueva | Comparación y retorno reproducibles | Referencias remotas verificadas | 3.1 intacta |
| Núcleo y voz | Residente funcional, STT con fallos documentados | Se conservan íntegros | Evitar rehacer captura y comprensión simultáneamente | 379 pruebas anteriores siguen pasando | Voz sigue usando 3.1 |
| Ruta de inteligencia | FastPath/recuperación/E5/Qwen acoplados | Motor Next independiente y gramática completa mínima | Funcionamiento directo sin modelos ni red | Entrada CLI y prueba de importaciones/red bloqueadas | Prototipo textual funcional |
| Proveedores | Cliente Ollama específico | Protocol, offline y falso; plazo, errores, cierre y suspensión | Reemplazo sin mutación del gestor | Conexión/cuota/autenticación falsas, timeout y concurrencia | API real pendiente |
| Contratos y herramientas | Lista de intenciones y diccionarios | Decisiones de plan v1, registro con parámetros tipados y resultados separados | Extensión futura sin dar acceso al sistema al modelo | JSON inválido, herramientas/objetivos/IDs inventados y rangos | Cinco capacidades, solo simulación |
| Contexto y cancelación | CANCEL podía depender de efectos del intérprete | Gestor central, tickets, revisiones, TTL, cancelación y retención | Evitar planes vivos tras cancelación o respuestas tardías | Cancelación sobre plan no vacío; carreras, expiración y copia profunda | Base aplicada; operaciones contextuales complejas retenidas |
| Respuestas | Texto libre podía afirmar ejecuciones | Plantillas locales y resultados simulados/desconocidos | No inventar observaciones | Proveedor sin campo de respuesta libre; consulta no inventa volumen | Sin afirmaciones de ejecución real |
| Dependencias y CI | Extra intelligence con ONNX/tokenizadores | Extra next solo Pydantic; CI mínimo separado | Demostrar independencia, no solo una bandera desactivada | CI sin paquetes de modelos, 64 pruebas | Ninguna dependencia nueva de terceros |

### Comprobaciones realizadas

- Base antes de cambios: 379/379, 21,75 s.
- Next: **64 pruebas nuevas**, todas aprobadas; son desarrollo, no un holdout ni una medición de comprensión general.
- Batería local completa: **443 aprobadas, cero fallos**, 29,82 s; [salida preservada](reports/pytest-phase32-stage1.txt). No se eliminó ninguna prueba anterior.
- Selección headless local: 438 aprobadas, cinco excluidas por dependencia nativa/modelos/GUI.
- [CI comprobado en GitHub](https://github.com/SebastianJimenezPo/Jarvis/actions/runs/43636526841): selección general, 437 aprobadas, una omitida por instalación explícita de voz y cinco excluidas; job `next-offline`, 64 aprobadas sin extras de voz/inteligencia. Las 64 de ese job se solapan con la batería general: no se suman como pruebas distintas.
- Compilación/importaciones, CLI multiturno y enlaces locales comprobados. No se cambiaron los módulos `jarvis.intelligence`, las preferencias personales ni los modelos instalados.

Se prueban, entre otros: solicitudes con condiciones/comillas/preguntas y cláusulas adicionales; propuestas falsas del proveedor; targets/IDs/revisiones/dependencias inventados; valores booleanos o texto donde se exige entero; cancelación independiente del parser; no-cancelación; retención; fin de contexto; cierre; respuesta fuera de orden; plazo ante un proveedor que ignora cancelación; límite de un trabajador; suspensión tras fallos; ausencia de filtración de una credencial falsa en errores; consultas de estado desconocido y copia aislada de resultados. No hay confirmación física que pueda reutilizarse: ese mecanismo no se implementa todavía.

### Microbenchmark textual, no integración de voz

`scripts/benchmark_next_foundation.py` ejecutó cada arquitectura en un proceso nuevo con seis frases conocidas, cinco calentamientos y 30 ciclos por frase: 180 turnos por arquitectura. El motor antiguo se limita expresamente a reglas, sin LLM/E5; Next usa su perfil offline predeterminado. Orden fijo antiguo → nuevo y una inicialización por proceso. [Datos completos](reports/phase32-foundation-benchmark.json).

| Frase | 3.1 reglas, mediana / p95 ms | Next, mediana / p95 ms |
| --- | --- | --- |
| Abre Steam | 2,489 / 3,150 | 0,197 / 0,354 |
| Volumen al 30% | 2,499 / 5,218 | 0,233 / 0,427 |
| Pausa la música | 2,474 / 4,614 | 0,225 / 0,348 |
| Silencia el audio | 2,461 / 3,883 | 0,234 / 0,356 |
| Cancela | 1,642 / 3,925 | 0,123 / 0,251 |
| Olvida todo lo anterior | 2,058 / 3,557 | 0,097 / 0,243 |

La última frase cayó en fallback/aclaración en 3.1 sin LLM y en cancelación directa en Next. La cancelación de un plan no vacío se verifica aparte en pruebas: el microbenchmark tiene una cancelación previa en su ciclo y no basta para demostrar esa garantía.

RSS tras inicialización textual: antiguo 43,8 MB, Next 31,1 MB; tras 180 turnos, 44,6 y 31,3 MB. Son instantáneas, no picos ni consumo del residente completo. Importación/construcción: 0,501 s y 0,319 s, una muestra por arquitectura. CPU acumulada del proceso durante el bucle: 0,4375 y 0,03125 s, con resolución Windows gruesa; no se infiere CPU media/pico de juego o reposo. No se midió GPU.

Estos casos no son nuevos ni reservados. No equivalen a comparar Qwen activo, Groq o voz, ni prueban los objetivos de precisión del 95%, 1,5 s desde fin de voz o estabilidad prolongada. No hay llamadas remotas, cuotas consumidas, precisión remota ni latencia API que reportar.

### Límites y siguiente bloque

La primera etapa tiene cimientos funcionales y verificables; **la Fase 3.2 sigue abierta**. No hay regresiones detectadas en la batería conservada, pero los errores previos de voz/comprensión del residente no se consideran resueltos por añadir Next. No se eliminó físicamente la arquitectura antigua de la distribución, porque todavía sirve al residente; E5, Qwen, Ollama, la recuperación de fragmentos y la autorización por vocabulario quedan fuera del flujo Next.

Faltan proveedor real, interpretación/autorización semántica compleja, referencias y modificaciones de planes completas, integración con voz, evaluación nueva reservada, métricas de API, observaciones reales y herramientas físicas. La memoria persistente y todos los demás proveedores no se desarrollan en esta intervención.

Siguiente bloque recomendado: **un piloto textual de Groq y contexto/política acotados**, usando primero HTTP simulado y un conjunto piloto de desarrollo pequeño. Consultar documentación oficial vigente antes de elegir modelo y cuotas; pedir configuración local de clave solo al preparar el uso real, sin leerla ni publicarla en chats/Git. Aceptar decisiones complejas solo tras definir evidencia y sus pruebas de autorización; no sustituir esas pruebas por JSON válido. Mantener una llamada por turno y modo offline. Con eso comprobado, incorporar el adaptador de voz existente sin reconstruir la captura.

Para esta etapa no se necesita clave ni prueba física. Después siguen pendientes voz real, ruido, pausas, reinicio/suspensión con Next, duración prolongada y videojuegos; no se simulan esos resultados. El primer candidato físico de volumen se prepara y habilita en su bloque específico, con aprobación explícita antes de activar una acción real.
