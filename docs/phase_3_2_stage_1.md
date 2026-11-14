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
