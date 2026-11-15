# Fase 3.2 — Etapa 6: comparación de razonamiento y diagnóstico

Fecha: 15 de noviembre de 2026. Motor textual y simulado. Fase abierta; sin integrar voz ni acciones físicas.

## Cambios y alcance

Se añadió un diagnóstico cerrado para `invalid_response`, conservando su código público: `http_response`, `response_envelope`, `completion_limit` o `decision_contract`. La categoría pasa del adaptador al trabajador, al resultado del motor y al informe de evaluación. Las cadenas no reconocidas se descartan; los otros errores no aceptan esta categoría. No se guardan cuerpos HTTP, mensajes de excepción, cabeceras ni razonamiento privado del modelo.

`completion_limit` requiere observar `finish_reason=length`. Indica una finalización limitada, sin demostrar cómo se repartió el presupuesto entre razonamiento y salida visible. No provoca reintentos, una ampliación automática de tokens ni un cambio de modelo. `decision_contract` agrupa los rechazos al convertir la decisión, sin atribuirlos automáticamente a comprensión semántica.

La suite completa pasa: **564 pruebas**. Las siete nuevas comprobaciones cubren propagación de categorías, descarte de texto arbitrario o secretos, respuestas limitadas, envolturas inválidas, contradicciones de contrato y conservación de la regla de no reintentar. Se comprobó además que el diagnóstico llegue al informe del piloto con transporte falso.

| Componente | Estado anterior | Cambio realizado | Motivo | Evidencia | Estado final |
|---|---|---|---|---|---|
| Diagnóstico remoto | `invalid_response` sin fase observable | Enum cerrado propagado hasta evaluación | Distinguir límites de salida y contrato sin capturar contenido | Pruebas de transporte, motor y piloto | Operativo |
| Interpretación y política | Contrato de modo de petición de etapa 5 | Sin cambios semánticos durante la comparación | Aislar el presupuesto de razonamiento | Hashes del motor congelado | Revisión local obligatoria |
| Configuración remota | `low` y `medium` seleccionables explícitamente | Comparación con presupuesto previo | Evaluar el aplazamiento conservando contexto | Informes y protocolo fijados antes de llamadas | Sin promoción automática |
| Voz, residente y herramientas reales | Estado previo | Sin cambios | Respetar alcance | Archivos modificados limitados a diagnóstico/evaluación | Pendientes |

## Protocolo

Se fijaron [ocho turnos conocidos](evaluation/next_reasoning_comparison.json): cinco independientes y una secuencia contextual de tres turnos. La preparación contextual es directa; quedan siete posibles solicitudes remotas por configuración. Se conserva [el protocolo previo](evaluation/NEXT_REASONING_COMPARISON_PROTOCOL.md), con máximo global de 14 solicitudes y detención al primer error de proveedor en cada configuración, sin reintentos ni continuación automática.

Mismo motor `97f5a32`, modelo `openai/gpt-oss-120b`, prompt, esquema, plazo 8 s, salida máxima 1024 tokens e intervalo mínimo 20 s. Primero `low`, luego `medium`, con una pausa adicional de 20 s entre configuraciones. El [manifiesto](reports/next-reasoning-manifest.json) registra hashes del motor y del conjunto; se comprobaron antes y después de cada ejecución. La prueba con fixture acertó 8/8, evidencia de la orquestación, no del modelo.

La [referencia de API de Groq](https://console.groq.com/docs/api-reference) admite ambos presupuestos para el modelo utilizado. Las diferencias de orden, tiempo y muestreo pueden influir en el resultado: esta comparación pequeña no demuestra causalidad ni precisión general. Los datos ya eran conocidos, por lo que no se presentan como evaluación reservada.


## Resultados y decisión

| Medida | low | medium |
|---|---:|---:|
| Coincidencia exacta de operación y plan | 7/8 | 8/8 |
| Turnos del proveedor correctos, excluida preparación directa | 6/7 | 7/7 |
| Secuencia contextual completa, incluida preparación | 3/3 | 3/3 |
| Borradores indebidos | 1 | 0 |
| Errores de proveedor | 0 | 0 |
| Mediana remota | 0,881 s | 1,571 s |
| p95 remoto | 1,488 s | 2,476 s |
| Solicitudes remotas | 7 | 7 |

Fuentes: [low](reports/next-reasoning-low.json), [medium](reports/next-reasoning-medium.json), [resumen verificado](reports/next-reasoning-comparison.json) y [fixture](reports/next-reasoning-fixture.json). Los hashes de ambas fuentes y del motor se comprobaron al consolidar. Los dos informes corresponden al mismo commit congelado. En total se hicieron **14 solicitudes**, cumpliendo el límite previo.

`Low` volvió a proponer ejecución inmediata para la orden subordinada al fin de una instalación. `Medium` la clasificó como `deferred`, sin borrador, y acertó las otras siete comprobaciones. Ambos conservaron referencias e identidad aplicables de los tres turnos contextuales. No hubo resultados antes de revisión ni ejecuciones físicas. Las latencias corresponden exclusivamente a interpretación remota, sin intervalos de cuota, STT, TTS o ejecución física.

**Se selecciona `medium` como candidato experimental para una nueva validación**, porque satisface los criterios de este conjunto conocido. No se cambian los valores predeterminados, no se habilita autorización automática y no se presenta 8/8 como precisión general. El mayor tiempo de respuesta es un coste observado que debe medirse de nuevo con datos más amplios. No hubo respuestas truncadas en esta comparación: el diagnóstico nuevo está verificado por pruebas de transporte falsas, no por un fallo remoto observado aquí.

Para usar explícitamente el candidato en una sesión textual de simulación, con la credencial ya configurada:

```powershell
.\.venv\Scripts\python.exe -m jarvis.next --provider groq --allow-remote --free-tier --model openai/gpt-oss-120b --reasoning-effort medium --timeout 8 --review --interactive
```

La revisión sigue requiriendo `:confirm ID` para aplicar un borrador simulado. No se abren aplicaciones ni se modifica audio real.

## Siguiente bloque

Preparar una evaluación nueva y sellada con `medium`, incluyendo variaciones temporales, citas, negaciones mixtas y contexto. Preferir frases redactadas por el usuario u otro origen humano, con expectativas fijadas antes de ejecutar, para reducir el sesgo del implementador. Los datos de esta comparación quedan como desarrollo y no deben reutilizarse como evidencia independiente. La integración de voz será posterior a esa aceptación textual; las acciones reales siguen fuera de alcance. **La Fase 3.2 permanece abierta.**
