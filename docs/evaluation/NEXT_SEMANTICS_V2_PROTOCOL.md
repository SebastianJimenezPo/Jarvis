# Evaluación interna v2: contrastes semánticos

Motor congelado: `a722c7b`. Antes de modificar prompt o política se sellan 16 frases nuevas: cuatro negaciones, tres citas/relatos, tres órdenes aplazadas, dos hipótesis y cuatro órdenes positivas de contraste. Cada frase empieza sin contexto anterior. No se compara su porcentaje con v1: cambia la distribución y se conoce qué familias fallaban.

Es una evaluación interna del mismo autor del código, no una validación humana independiente. Se excluyen duplicados textuales normalizados de los informes, conjuntos y literales de pruebas conocidas. Persisten similitud semántica y sesgo de autor. Las etiquetas y expectativas nunca se envían al proveedor.

Criterios escritos antes de ejecutar: cero borradores para los doce casos sin orden inmediata, cero resultados antes de revisión y cero ejecución física; los cuatro contrastes positivos deben producir el plan correcto. Se informa la clasificación exacta aparte: confundir hipótesis con conversación puede abstenerse correctamente, pero no cuenta como clasificación correcta. Un error remoto permanece como error, nunca como comprensión demostrada.

Misma configuración de Groq Free ya autorizada: `openai/gpt-oss-120b`, `low`, plazo 8 s, intervalo mínimo 20 s, hasta 16 solicitudes sin reintentos. La revisión automática del evaluador confirma solo operación y plan completos que coincidan con la expectativa, exclusivamente en simulación. Ante un error remoto se conserva el resultado; cualquier continuación manual solo admite sesiones nunca intentadas. No se modifica el motor durante la primera exposición.

Después de leer los resultados para corregir el motor se retirará este conjunto a desarrollo antes de editarlo. Los resultados originales y el sello se conservan. La autorización automática, la integración de voz y las herramientas físicas siguen fuera de este bloque.
