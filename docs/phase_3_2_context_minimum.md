# Contexto operativo mínimo de Next

15 de noviembre de 2026. Todo permanece en simulación.

`NextConversation` coordina el motor, las preguntas y las confirmaciones. No interpreta cualquier respuesta corta fuera de contexto. Una pregunta pendiente conserva intención, parámetro faltante, candidatos ordenados, sesión, revisión y vencimiento (45 s). Los referentes de aplicación son propuestas mencionadas, no observaciones físicas; viven como máximo 120 s y no dependen del contenido actual del plan. Nada se escribe como memoria permanente ni se envía como historial conversacional a Groq.

Ejemplos comprobados offline:

1. «Abre una aplicación» → pregunta concreta con Spotify, Steam, Chrome y Discord → «Spotify» abre una propuesta simulada para Spotify. «El segundo» selecciona Steam del orden mostrado. «Ese» solo resuelve si hay un referente único vigente.
2. «Abre Steam, pero todavía no hagas nada» → propuesta retenida → «Mejor Spotify» conserva el ID de acción y la retención, sin resultados de herramienta. Un «sí» aislado no la autoriza. «Autoriza la simulación» muestra la propuesta exacta y solicita confirmación; un «sí» vigente autoriza únicamente esa simulación.
3. «Ajusta el volumen» pregunta porcentaje y acepta valores numéricos entre 0 y 100. No inventa un número por una respuesta ambigua.

Los patrones locales añadidos son gramáticas de turno completo para estos actos de diálogo, no una lista general de palabras permitidas. El resto sigue por el proveedor o pide aclaración; no se afirma cobertura de todas las paráfrasis. Una pregunta genérica del proveedor no genera una intención pendiente inventada.

Modificar, revisar y autorizar son operaciones distintas. Confirmar la revisión de un plan retenido solo confirma la edición: mantiene la retención y no simula herramientas. `authorize_plan` es una solicitud local reconstruida que requiere otra confirmación; el proveedor no puede autorizarse por JSON. Las revisiones se ligan al contenido exacto, sesión, generación, revisión y vencimiento (máximo 30 s). Caducidad, nueva sesión, turno ordinario y cancelación invalidan la confirmación anterior. «No» ante un borrador lo descarta y conserva el plan previo; «cancela» centraliza el descarte de plan, pregunta, referente y confirmación.

Las respuestas se generan con plantillas locales: pregunta, negación, solicitud futura no programable, indisponibilidad, propuesta retenida, simulación o cancelación. No se realiza otra consulta al modelo para redactar mensajes. El CLI Next utiliza ahora el candidato 120B Medium y 4 s cuando se elige Groq; offline continúa predeterminado y `low` permanece configurable, sin fallback.

Comprobación del bloque: 205 pruebas de Next aprobadas (incluidas las regresiones previas). La referencia sellada anterior pasó 32/32 turnos (29 nuevos y tres controles), mediana remota 1,720 s, p95 2,845 s y cero timeouts con 4 s; es una evaluación interna de autor común sobre el motor anterior. No se atribuye esa tasa a las ampliaciones de contexto ni a la voz.
