# Validación de Fase 3 — 2026-11-10

Estado: implementación terminada para revisión física, sin cierre de fase. Ninguna acción solicitada por el usuario se ejecuta en el sistema. Documento maestro conservado en `phase_3_spec.md`.

## Automatización

La base de Fase 2 tenía 122 pruebas y se ejecutó correctamente antes de los cambios. Una primera ejecución con el residente abierto fue rechazada por el mutex; se cerró ordenadamente el residente y se repitió la base. Resultado final: **189 pruebas aprobadas**; salida en `reports/pytest-phase3.txt`.

Se verifican contratos, catálogo, referencias, correcciones, planes pendientes, caducidad, negativos y números con signo, negaciones por cláusula, futuro y condiciones pospuestas, parámetros sin evidencia, dependencias ausentes, degradación, privacidad de errores, cancelación, resultados obsoletos y HTTP loopback con servidor simulado. La prueba Qt de bandeja se convirtió de temporizadores fijos a comprobación de estados/eventos con plazo máximo para evitar fragilidad bajo carga; conserva sus aserciones funcionales.

Los corpus escritos se ejecutan con scripts separados: 328 casos / 363 turnos. No se confunden con el número de pruebas pytest. Sus métricas, revisión posterior y limitaciones están en `model_comparison.md`. Un corpus revisado no es un holdout intacto.

## Integración de voz

Se recorrió captura sintética, activación de diagnóstico con Rustpotter personal cargado, VAD y Moonshine reales, inteligencia, Piper y salida de audio predeterminada. Se conservaron dos fallos: «Mejor azules» se reconoció como «Fora Sodes.»; en otro intento una petición corta se transcribió como «ponlas los esrojas». El sistema pidió aclaración y no inventó ejecución.

El informe final `phase3-voice-integration.json` usó estímulos sintéticos más claros: «Por favor pon la luz principal de color rojo» y «No, mejor cambia las luces a color azul». Comprobó propuesta roja, corrección contextual azul, respuesta hablada de simulación, dos turnos, retorno a DORMANT y ausencia de errores, reinicios o pérdidas. No se modificó STT para ocultar los fallos anteriores.

Esto demuestra integración técnica con esos estímulos; **no valida la voz real del usuario, precisión acústica, eco físico, micrófono de auriculares ni falsas activaciones**. No se realizó una búsqueda repetida hasta presentar los clips originales como correctos: los informes fallidos y el cambio de estímulo son explícitos.

## Conservación y pendientes

La arquitectura de audio, selección actual de dispositivo, voz y pausa de activación aceptadas por el usuario se conservan. Silencio final 1200 ms. Umbral de wakeword actual 0.55, sujeto a evaluación con conversación real. Las pruebas físicas previas de reinicio, suspensión y salida fueron realizadas por el usuario en fases anteriores; no acreditan automáticamente la nueva fase.

Pendiente: lista física de `phase_3.md`, conversaciones espontáneas, interrupciones, estabilidad prolongada, consumo durante juego, reinicio y suspensión con inteligencia habilitada. La conversación puede ser lenta y equivocarse; los modelos crudos mostraron baja exactitud en categorías y la semántica aceptaciones erróneas. No hay ejecución real, memoria permanente, Internet conversacional ni Fase 4. El usuario decide el cierre después de probar.
