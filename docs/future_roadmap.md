# Estado y siguientes fases — 2026-11-14

Fases 1 y 2: base residente y voz local implementadas, con comprobaciones físicas del usuario y observaciones documentadas. Fase 3: motor híbrido, conversación local y planes simulados implementados; aceptación física pendiente. Ver `phase_3.md` e `intelligence_validation.md`.

Fase 3.1: estabilización implementada en `phase-3-1-hardening`, con evaluación técnica y aceptación física pendiente. Ver `phase_3_1.md`; los perfiles manuales de rendimiento básicos ya existen. La seguridad reservada aprobada no elimina las limitaciones de comprensión y voz.

Fase 3.2 — Jarvis Next: primera etapa textual en `phase-3-2-jarvis-next`, con contratos, proveedor sustituible y simulación directa. El residente sigue en 3.1. Ver [alcance y resultados](phase_3_2_stage_1.md) y [arquitectura](jarvis_next_architecture.md). La [segunda etapa](phase_3_2_stage_2.md) añade Groq optativo y revisiones contextuales en simulación, con clave fuera de Git y pilotos reales conservados. La [tercera etapa](phase_3_2_stage_3.md) conserva una evaluación interna de 23/32 turnos nuevos y añade barreras para citas y tiempos explícitos; el conjunto ya se retiró a desarrollo. Sigue pendiente validar de nuevo con otros datos antes de autorización automática e integración de voz; el candidato físico de volumen es posterior. No se declara completa 3.2.

Las capacidades siguientes todavía no están habilitadas:

4. Conectar herramientas reales de aplicaciones, multimedia, volumen, luces e integraciones. Validar entradas, permisos, confirmaciones aplicables y resultados. El catálogo de simulación es una base, no una autorización para ejecutarlo.
5. Memoria permanente de preferencias, alias, dispositivos y rutinas explícitas.
6. Interfaz flotante, perfiles de rendimiento, instalador y pruebas prolongadas.

Pendiente de evaluación: falsas activaciones, pausas naturales y STT con frases cortas, elección de micrófono de auriculares, voz alternativa, consumo durante juego y conversaciones espontáneas. Conservar la configuración aceptada mientras se recopilan resultados físicos. La dirección 3.2 sustituye la ampliación indefinida del motor anterior; no implica que la aceptación física pendiente de 3.1 se haya aprobado. No conectar acciones reales mientras queden fallos o abstenciones relevantes sin evaluar.

La [cuarta etapa](phase_3_2_stage_4.md) registra 12/16 aciertos en contrastes nuevos, un borrador aplazado indebido y una regresión parcial de 2/4 fallos tras aclarar el prompt. No se alcanzó la aceptación prevista. Se mantienen revisión local y simulación; próximos pasos: investigar los errores críticos restantes y aceptación textual de autor distinto, antes de voz o acciones físicas.
