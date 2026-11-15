# Comparación de desarrollo low / medium

Fecha: 15 de noviembre de 2026. Base semántica `202a41a`; solo se añaden diagnósticos de error antes de congelar el motor para ambas configuraciones. No se modifica prompt, esquema, política ni reductor durante la comparación.

Ocho turnos conocidos por configuración: negación, cita, condición aplazada, hipótesis, orden afirmativa con prohibición de otro objetivo y una secuencia contextual de tres turnos (preparación directa, corrección con adición, cancelación selectiva). No es un conjunto reservado ni una medición de precisión general.

Se ejecuta primero `low`, después `medium`, con el mismo modelo `openai/gpt-oss-120b`, plazo 8 s, salida máxima 1024 tokens y mínimo 20 s entre solicitudes remotas. Solo cambia `reasoning_effort`. Cada ejecución tiene siete posibles solicitudes remotas: **máximo global 14**. Se conservan errores y se detiene la configuración al primer error de proveedor; no se reintenta ni se continúa automáticamente. El orden fijo y la aleatoriedad pueden influir: no se presenta la diferencia como efecto causal demostrado.

Criterios para considerar un candidato posterior: completar los ocho turnos sin errores, cero borradores en casos sin acción inmediata, las tres operaciones positivas del proveedor correctas (incluyendo las dos ediciones contextuales), preparación directa correcta y referencias/identidad conservadas. Se informa clasificación exacta aparte. Una configuración que solo se abstiene de todo no cumple. La promoción a autorización automática o a acciones físicas queda excluida, incluso si cumple este conjunto conocido.

El nuevo diagnóstico `provider_error_stage` es un enum cerrado: respuesta HTTP, envoltura JSON, límite de finalización o contrato de decisión. Solo acompaña a `invalid_response`; nunca contiene mensajes de excepción, cabeceras, contenido HTTP o razonamiento privado. `finish_reason=length` permite identificar una finalización limitada, pero no demuestra por sí solo qué componente consumió el presupuesto ni justifica elevarlo automáticamente.

La [referencia de Groq](https://console.groq.com/docs/api-reference) admite `low` y `medium` para este modelo. No se cambia facturación, proveedor, plan Free ni configuración del residente. Confirmaciones del evaluador requieren operación y plan completos correctos y solo producen simulación.
