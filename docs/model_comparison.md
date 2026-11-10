# Comparación local — 2026-11-10

Informes completos en `reports/`. Son mediciones de este equipo y estímulos limitados, no estimaciones de precisión general. Se conservaron intentos iniciales y mediciones invalidadas para que los cambios puedan auditarse.

## Modelos generativos

Ollama portable 0.40.16, CPU, cuatro hilos, cero capas GPU, contexto 2048, thinking deshabilitado. Las etiquetas elegidas no tienen el mismo formato de cuantización:

| Modelo | Metadatos locales | Disco | Categorías correctas, 12 casos | JSON válido | Mediana |
| --- | --- | --- | --- | --- | --- |
| qwen3:1.7b | 2.0B, Q4_K_M | 1.359 GB | 4/12 | 12/12 | 6.125 s |
| qwen3.5:2b | 1.9B, Q8_0 | 2.683 GB | 4/12 | 11/12 | 10.403 s |

Ambos identificaron los cuatro casos de acciones; fallaron principalmente categorías no accionables. Ninguna propuesta insegura fue aceptada por la validación independiente en esa muestra pequeña. El ensayo inicial con esquema extendido funcionó peor y se conserva en `llm-comparison-initial.json`. La comparación usó plazo de 45 s; el funcionamiento normal limita cada petición a 12 s.

En tres turnos educativos conectados, Qwen3 tardó 7.391 / 2.137 / 3.093 s; Qwen3.5, 11.531 / 6.064 / 5.644 s. Se seleccionó provisionalmente Qwen3 por latencia y tamaño, sin atribuirle alta precisión de clasificación. La arquitectura híbrida resuelve negaciones y casos deterministas antes de consultarlo.

Contexto 1024 frente a 2048, dos turnos: 4.635/2.968 s frente a 4.596/2.981 s. Se conserva 2048 por margen; la muestra no acredita mejor razonamiento contextual. Digests, capacidades y cuantización exactos: `local-model-metadata.json`.

## Embeddings

Comparación en procesos aislados, mismo conjunto, normalización y prefijos query/passage de E5. Calibración de umbral y margen por intención solo con desarrollo; conjunto pequeño.

| Modelo | Carga | RSS del proceso | Consulta media / p95 | Mejor intención correcta en 12 positivos | Aceptaciones erróneas |
| --- | --- | --- | --- | --- | --- |
| MiniLM multilingüe ONNX int8 | 2.669 s | 447.95 MiB | 8.12 / 12.45 ms | 7/12 | 5 de 10 aceptaciones |
| multilingual-e5-small ONNX | 2.391 s | 778.63 MiB | 9.54 / 13.07 ms | 11/12 | 2 de 10 aceptaciones |

Se elige E5 provisionalmente por estos resultados, con mayor memoria activa. Ninguno autoriza acciones sin validación posterior. La calibración no es una probabilidad de confianza general. `semantic-initial-sequential.json` no permite comparar RAM por compartir proceso y se excluye de esa conclusión. Revisiones y hashes están en el registro local; licencias declaradas: MiniLM Apache-2.0, E5 MIT.

## Lenguaje y motor completo

Corpus principal: 279 casos, 303 turnos; desarrollo 40 y evaluación nominal 263 turnos. El corpus adicional contiene 49 casos, 60 turnos. Total: **328 casos / 363 turnos**, escritos y parcialmente basados en plantillas; no son grabaciones del usuario.

La evaluación principal inicial detectó un defecto crítico: normalizar «-10» eliminaba el signo. Se corrigió conservando signos y se añadieron regresiones. La versión revisada obtiene 100% sobre ese conjunto ya inspeccionado, por lo que no constituye validación independiente.

El conjunto adicional inicial sin LLM obtuvo 91.67% de categorías y 95.65% de parámetros. Tras revisar defectos, la variante degradada obtuvo 96.67% y 100%; la híbrida, 60/60 categorías y parámetros, sin propuestas críticas no autorizadas: 51 turnos rápidos y 9 LLM. Es también un conjunto revisado; **no demuestra 100% ni 95% de precisión en lenguaje nuevo**. La ruta LLM híbrida promedió 3.008 s, mediana 2.330 y p95 5.645. La ruta rápida principal revisada promedió aproximadamente 0.155 ms; excluye STT y síntesis.

## Consumo

Reposo real de 30 s, micrófono WASAPI, voz e inteligencia habilitadas, sin activaciones: CPU media del árbol Jarvis 0.309%, máximo muestreado 0.430%, RSS pico 89.36 MiB, sin pérdidas ni reinicios. Servicio Ollama externo separado: 59.08 MiB, ningún modelo cargado, delta CPU cero a la resolución medida. No se debe sumar o excluir silenciosamente ese servidor al comparar.

Una petición Qwen3 aislada: 2.460 s; Ollama y todos sus descendientes consumieron CPU media del 14.371% de la máquina de 16 procesadores lógicos, RSS pico conjunto 1651.75 MiB y VRAM reportada por API cero. Tras liberación, la lista de modelos cargados quedó vacía. No se midió utilización GPU sostenida ni una sesión de juego.

`phase3-idle-initial-shared-service-busy.json` se invalida para reposo porque otra comparación usaba el servicio. `llm-resource-server-only-invalid.json` se invalida para RAM activa porque excluía descendientes. Los informes corregidos son `phase3-idle-30s.json` y `llm-resource-sample.json`.
