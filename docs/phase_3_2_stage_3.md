# Fase 3.2 — Etapa 3: evaluación y barreras de revisión

Fecha: 14 de noviembre de 2026. Fase abierta; Next continúa textual y simulado, sin conectar el residente de voz.

## Primera exposición conservada

Se congeló el motor en `4ca6910` antes de redactar 32 turnos nuevos y un control conocido. El conjunto es interno, del mismo autor que el código: no es una prueba humana independiente. Se descartaron duplicados textuales normalizados conocidos, no toda similitud semántica. Expectativas y etiquetas no se enviaron al proveedor.

Se usó Groq `openai/gpt-oss-120b`, razonamiento `low`, plazo 8 s, intervalo mínimo 20 s y salida máxima 1024 tokens. Hubo 32 solicitudes remotas en la primera exposición. Un error interrumpió la ejecución; la continuación manual solo procesó sesiones todavía intactas. No se repitieron casos ni se modificó el motor entre partes.

| Medida | Resultado original |
|---|---:|
| Coincidencia conjunta de operación y plan, turnos nuevos | 23/32 |
| Contexto, excluyendo control conocido | 14/15 |
| Grupo crítico | 5/12 |
| Capacidad / ambigüedad / observación | 1/2 · 1/1 · 2/2 |
| Decisiones del proveedor observables | 31/32 |
| Operación correcta entre decisiones observables | 23/31 |
| Propuestas con catálogo válido | 12/12 |
| Referencias, identidad de plan y revisión válidas del proveedor | 31/31 |
| Comprobaciones aplicables de identidad o ausencia de mutación | 23/23 |
| Borradores indebidos en casos críticos | 2 |
| Resultados de herramientas antes de revisión / ejecuciones físicas | 0 / 0 |

Estas medidas separan estructura, semántica, política y estado; no constituyen una precisión general del modelo. Algunas comprobaciones de identidad son ausencia de mutación sin elementos activos. La marca de preparación fallida indica comprobaciones previas fallidas, no necesariamente estado corrupto.

Los dos borradores críticos aparecieron para una petición futura y una orden citada. También se confundieron retención de autorización con negación, algunas hipótesis/prohibiciones y capacidad desconocida con ambigüedad. Un `invalid_response` no llegó como respuesta interna observable: no hay evidencia suficiente para atribuir su causa al modelo. No se publicaron cuerpos HTTP.

Fuentes inalteradas: [datos y sello](evaluation/next_reserved_v1.json), [primera parte](reports/next-reserved-v1-first.json), [continuación](reports/next-reserved-v1-continuation.json), [consolidación](reports/next-reserved-v1-combined.json) y [protocolo](evaluation/NEXT_RESERVED_PROTOCOL.md).

## Correcciones posteriores, exclusivamente de desarrollo

El conjunto se retiró mediante un archivo de estado antes de modificar el motor. El ejecutor reservado rechaza reutilizarlo como prueba nueva. Se conservan datos, sello y fallos originales.

| Componente | Estado anterior | Cambio realizado | Motivo | Evidencia | Estado final |
|---|---|---|---|---|---|
| Evaluador | Métrica conjunta | Observación separada, referencias e identidad; continuación sellada | Evitar atribuciones y repeticiones engañosas | Informes originales y pruebas del evaluador | Infraestructura operativa |
| Barrera de revisión | Una propuesta válida podía ofrecer órdenes citadas o futuras | Veto para comandos completos conocidos entre comillas y marcadores temporales explícitos | Bloquear dos familias detectadas | Pruebas fallan antes y pasan después | Conservadora, cobertura limitada |
| Proveedor Groq | Prohibiciones descritas de forma demasiado amplia | Distinguir suspender autorización del plan de negar una acción | Confusión hold/negated | Regresión dirigida, separada de primera exposición | Sin autorización automática |
| Contrato contextual | Rechazaba hold sin cita superior incluso con plan exacto | Aceptar referencia contextual ya validada para revisión local | La cita superior es opcional en el contrato | Prueba de retención e identidad | Sigue requiriendo confirmación local |
| Voz y herramientas reales | Residente 3.1 | Sin cambios | Respetar alcance | Cambios restringidos a Next/evaluación/documentación | Pendientes |

Las barreras nuevas no interpretan todo el español: reconocen comandos completos de la gramática mínima dentro de comillas y algunos marcadores de futuro. No cubren todas las paráfrasis y pueden retener solicitudes válidas que mencionen esas expresiones incidentalmente. No se añadió una lista global de palabras admitidas. Las comillas alrededor de un nombre, el pasado y un «cuando» subordinado no quedan bloqueados por los casos comprobados.

En 49 combinaciones forzadas de desarrollo, los borradores ofrecidos pasan de 36 a 21; los resultados sin revisión y las mutaciones permanecen en cero. No son 49 nuevas frases independientes ni una garantía para herramientas futuras. Ver [antes](reports/next-policy-boundaries-v1.json) y [después](reports/next-policy-boundaries-after-scope.json). La confirmación humana del borrador sigue siendo obligatoria para simular propuestas complejas.

## Comprobación y siguiente bloque

La suite local completa pasa: **531 pruebas**, incluidas **152 de Next**. Ocho fallos específicos se reprodujeron antes de las correcciones y pasan después; se comprueban además excepciones para no convertir el veto en una lista global de vocabulario. CI ejecuta Next sin modelos ni credenciales, junto con la matriz forzada.

El siguiente bloque recomendado es ampliar la validación semántica de negaciones, citas, hipótesis y tiempos con datos nuevos y criterios previos. Hace falta otra evaluación reservada distinta para estimar la calidad posterior. No corresponde conectar todavía acciones físicas ni declarar terminada la Fase 3.2. No se midieron cambios de voz, FPS, CPU o memoria del residente.

La [regresión dirigida con Groq](reports/next-hold-after-scope.json), sobre `3755f54`, acertó la retención «Aún no autorices este plan» con una preparación directa conocida. Fueron dos turnos, **una sola solicitud remota**, sin repetir el caso ni cambiar modelo. Conservó acciones e identidad al confirmar la retención simulada. No es otra prueba reservada ni una tasa general posterior. Total de este bloque: 33 solicitudes remotas (32 de primera exposición y una de regresión), sin reintentos automáticos ni servicios de pago.

La matriz posterior se ejecutó con los cambios aún sin confirmar sobre `cc1202a`; el campo `commit` original refleja esa base. Se añade la referencia del motor ya confirmado en `3755f54` y sus hashes para identificar el código probado.
