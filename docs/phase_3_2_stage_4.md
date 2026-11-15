# Fase 3.2 — Etapa 4: alcance de la intención

Fecha: 14 de noviembre de 2026. Fase abierta; motor textual y herramientas simuladas. No se integra voz ni se habilitan acciones físicas.

## Primera exposición v2

Se congeló el motor en `a722c7b` y se sellaron 16 frases nuevas con criterios previos: 12 sin orden inmediata y cuatro órdenes positivas de contraste. Cada frase empezó en una sesión vacía. No se enviaron expectativas al proveedor. Es una evaluación interna del autor del código, con exclusión mecánica de duplicados textuales conocidos; persisten similitud semántica y sesgo de autor. Su distribución difiere de v1: **no permite comparar porcentajes como mejora general**.

Groq `openai/gpt-oss-120b`, razonamiento `low`, plazo 8 s, intervalo mínimo 20 s, máximo 1024 tokens de salida: 16 solicitudes, sin reintentos ni interrupciones. Ver [protocolo previo](evaluation/NEXT_SEMANTICS_V2_PROTOCOL.md), [datos sellados](evaluation/next_reserved_v2.json), [informe original](reports/next-reserved-v2-first.json) y [consolidación y aceptación](reports/next-reserved-v2-combined.json).

| Medida | Resultado antes del ajuste |
|---|---:|
| Operación y plan correctos | 12/16 |
| Negaciones | 4/4 |
| Citas y relatos | 2/3 |
| Aplazamientos | 2/3 |
| Hipótesis | 1/2 |
| Órdenes positivas de contraste | 3/4 |
| Abstenciones sin error ni borrador en casos sin acción inmediata | 10/12 |
| Borradores indebidos en esos casos | 1/12 |
| Cita rechazada por la política local | 1 |
| Decisiones del proveedor observables / referencias válidas | 16/16 · 16/16 |
| Propuestas con catálogo válido | 5/5 |
| Resultados de herramientas antes de revisión / ejecución física | 0 / 0 |

**La aceptación previa falló.** Abstenerse sin error no equivale a clasificar correctamente: una hipótesis se clasificó como conversación. La barrera local rechazó el imperativo citado que el modelo convirtió en orden, pero no bloqueó una orden subordinada al final de una instalación. Esa propuesta no se confirmó. También se perdió una petición afirmativa válida acompañada de una prohibición sobre otro objetivo.

Latencia observada de interpretación remota: mediana 0,832 s y p95 1,199 s en estos 16 turnos. Excluye intervalos entre solicitudes, voz y herramientas físicas; no es latencia de extremo a extremo ni garantía de rendimiento. Las comprobaciones aplicables de identidad o no mutación fueron 12/12; incluyen sesiones sin elementos activos.

## Decisiones y límites

Se conservó el informe original y se retiró v2 antes del ajuste mediante [estado de retirada](evaluation/next_reserved_v2.status.json). El ejecutor reservado rechaza su reutilización como evaluación nueva. Los cuatro errores pasan a regresión de desarrollo.

| Componente | Estado anterior | Cambio realizado | Motivo | Evidencia | Estado final |
|---|---|---|---|---|---|
| Evaluación | Resultado conjunto | Medidas separadas de abstención, clasificación, recuperación positiva y cobertura | No premiar errores o conjuntos incompletos | Pruebas del evaluador y aceptación v2 | Operativa |
| Instrucciones Groq | Prohibición podía dominar toda la frase; modalidades poco diferenciadas | Alcance por cláusula, cita frente a petición propia, hipótesis frente a aplazamiento | Cuatro fallos preservados | Regresión dirigida posterior | Ajuste acotado, sin garantía general |
| Política local | Veto conservador de citas/tiempos y revisión obligatoria | Se conserva | Evitar acumular una regla por paráfrasis | Una cita bloqueada y un aplazamiento no detectado | Autorización compleja automática pendiente |
| Residente, voz, modelos locales y herramientas físicas | Estado previo | Sin cambios | Respetar alcance | Cambios restringidos a proveedor, evaluación y documentación | No conectados a Next |

La confirmación local sigue siendo una autorización explícita para simular el borrador mostrado, no una prueba de comprensión. Un JSON con herramienta, valores e IDs válidos puede representar una intención incorrecta. Tampoco se activaron otros proveedores, facturación, memoria persistente o almacenamiento de audio.

## Validación y continuación

La suite completa posterior al ajuste pasa: **538 pruebas**. Se verifican también los criterios de aceptación frente a errores, informes incompletos, borradores indebidos y confusiones de clasificación sin acción. Las pruebas de fixture comprueban el evaluador y el reductor, no la comprensión de Groq.

El siguiente bloque recomendado es una aceptación textual con frases redactadas por el usuario y expectativas fijadas antes de ejecutar, incluyendo negaciones mixtas y secuencias contextuales. Esto aporta un origen distinto al de los conjuntos sintéticos del implementador. Mantener la revisión y la simulación; no conectar voz o acciones físicas basándose en el resultado de una regresión conocida. **La Fase 3.2 no se declara terminada.**

La [regresión dirigida posterior](reports/next-semantics-v2-regression-groq.json), sobre `c95f6f9`, acertó **2/4 fallos conocidos**: hipótesis y orden afirmativa con prohibición de otro objetivo. La cita siguió proponiéndose como orden y la política la bloqueó; el aplazamiento siguió ofreciendo un borrador indebido, que no se confirmó. No hubo resultados previos a revisión ni ejecución física. Fueron cuatro solicitudes adicionales, sin reintentos: **20 solicitudes remotas en todo el bloque**. No se recalcula el resultado reservado original ni se afirma que el motor completo alcance 14/16: no se volvieron a evaluar los otros doce casos.

El ajuste al prompt se conserva como aclaración del contrato de intención, con mejora dirigida parcial. No resuelve los dos fallos críticos restantes. Antes de ampliar funciones conviene auditar cómo el proveedor prioriza citas y condiciones dentro de solicitudes completas, y evaluar cualquier alternativa con un presupuesto fijado de antemano. No se añade una lista de sinónimos a la política para cubrir las frases fallidas.
