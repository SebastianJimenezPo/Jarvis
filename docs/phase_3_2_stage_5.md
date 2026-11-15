# Fase 3.2 — Etapa 5: coherencia del tipo de petición

Fecha: 14 de noviembre de 2026. Continúa el desarrollo textual y simulado. La Fase 3.2 permanece abierta.

## Auditoría y decisión

Se revisaron la serialización HTTP, el prompt, el esquema remoto, la conversión a `Decision` y los fallos conservados de la etapa 4. El adaptador envía el texto completo, el contexto vigente y las instrucciones actuales; una prueba con transporte falso comprueba esa entrega. No se encontró evidencia de recorte de la solicitud que explique los fallos. No se capturaron cuerpos HTTP reales, cabeceras ni razonamiento privado del proveedor.

La [documentación de Groq](https://console.groq.com/docs/structured-outputs) distingue formato estructurado de corrección semántica. La [referencia de API](https://console.groq.com/docs/api-reference) admite esquema estricto y razonamiento `low` para el modelo usado. No se atribuye el fallo a un parámetro no soportado ni se afirma conocer la causa interna del modelo.

Se añade al contrato remoto un campo obligatorio `request_mode`, antes de `operation`, con ocho categorías: inmediata, aplazada, contenido relatado, hipótesis, prohibición, consulta informativa, ambigua y preferencia. Su descripción pide clasificar toda la solicitud antes de seleccionar herramientas. No es razonamiento libre ni una puntuación de confianza.

El adaptador comprueba que modo, operación y tiempo sean coherentes. Por ejemplo, contenido relatado solo puede convertirse en conversación, y una petición aplazada debe convertirse en `deferred`, sin herramientas inmediatas. Las contradicciones se rechazan como `invalid_response`; no se reparan inventando una intención ni se reintentan. El contrato neutral `Decision`, el gestor de planes y la ruta directa permanecen sin cambios.

| Componente | Estado anterior | Cambio realizado | Motivo | Evidencia | Estado final |
|---|---|---|---|---|---|
| Auditoría HTTP | Duda sobre recepción del prompt y texto | Verificación del contenido transmitido con transporte falso | Separar problemas de transporte de comprensión | Prueba del payload real del adaptador | Entrega íntegra comprobada localmente |
| Contrato Groq | Operación sin clasificación explícita de modalidad global | `request_mode` obligatorio y comprobación cruzada | Rechazar declaraciones contradictorias antes de mapear herramientas | Pruebas de modos, tiempos y traducción | Coherencia estructural reforzada |
| Autorización | Política local y revisión obligatoria | Se conservan | El modelo puede equivocarse de forma coherente | Propuestas falsas forzadas sin ejecución | No se confía en el modo declarado |
| Voz, residente y acciones físicas | Estado previo | Sin cambios | Respetar alcance | Cambios restringidos al adaptador, pruebas y documentación | No conectados |

## Pruebas y límites

La suite local completa pasa: **557 pruebas**. Se añadieron 19 comprobaciones, incluidas contradicciones entre modo y operación, modalidades no operativas, tiempos incompatibles y declaraciones falsas pero coherentes que siguen sin autorizar herramientas. Una cita reconocida mantiene su veto local; una condición no reconocida por ese veto todavía puede ofrecer un borrador si el modelo la declara falsamente inmediata. El test conserva explícitamente este límite, sin afirmar que se haya resuelto la semántica general.

El orden del esquema es una hipótesis de diseño, no una garantía sobre el orden efectivo de generación ni una explicación causal demostrada de cualquier diferencia de puntuación. El campo se valida y descarta al traducir la respuesta: no añade estado persistente, otra llamada remota, un segundo clasificador ni un modelo residente.

Para la comprobación real se fijó de antemano un [protocolo de desarrollo](evaluation/NEXT_REQUEST_MODE_PROTOCOL.md): ocho frases ya conocidas, cuatro de ellas fallos anteriores y cuatro controles. No es un conjunto reservado ni independiente. Mismo modelo `openai/gpt-oss-120b`, `low`, plazo 8 s, intervalo mínimo 20 s y límite de 1024 tokens; máximo ocho solicitudes sin reintentos. Las expectativas no se envían al modelo y solo se confirma un plan completamente correcto, exclusivamente en simulación.


## Resultado de desarrollo

El [informe completo](reports/next-request-mode-development.json), sobre `4b52c00`, registra **7/8 coincidencias** con ocho decisiones observables y ninguna interrupción. Se acertaron las cuatro órdenes positivas y tres de los cuatro casos sin acción inmediata. Entre los cuatro errores v2 anteriores se acertaron tres: cita, hipótesis y negación de un objetivo con orden afirmativa sobre otro.

El aplazamiento «Al acabar la instalación, deja el volumen del sistema al 37%.» volvió a convertirse en un plan inmediato y ofreció un borrador indebido. No se confirmó. Hubo **cero resultados previos a revisión y cero ejecuciones físicas**. La aceptación predefinida de cero borradores indebidos no se alcanzó. Los cinco conjuntos de herramientas propuestos eran válidos para el catálogo y las ocho referencias eran correctas: esto ilustra por qué esos controles no equivalen a comprensión.

Latencia de interpretación observada: mediana 0,999 s y p95 2,394 s en ocho turnos. Excluye intervalos entre solicitudes, voz y herramientas físicas. Se hicieron exactamente ocho solicitudes Groq, sin reintentos ni cambio de configuración. No se midieron reposo, memoria del residente, videojuegos o latencia de voz.

Los ocho casos son conocidos y escogidos para desarrollo. La diferencia respecto a la regresión anterior es descriptiva: no demuestra causalidad ni una tasa general. No se vuelven a puntuar los conjuntos reservados retirados. El contrato se conserva por su comprobación adicional de coherencia y el resultado dirigido parcial; no se habilita autorización automática.

## Siguiente bloque

El bloqueo principal sigue siendo la comprensión de condiciones temporales por el proveedor. Conviene comparar una única configuración alternativa de inferencia con presupuesto previo y controles positivos/contextuales, evitando repetir indefinidamente las mismas frases o ampliar listas locales de sinónimos. Cualquier candidato debe pasar después datos nuevos de origen distinto al implementador. No conectar voz o acciones reales basándose en este 7/8 de desarrollo. La Fase 3.2 sigue abierta.
