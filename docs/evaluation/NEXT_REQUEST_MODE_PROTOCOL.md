# Experimento de desarrollo: modo de petición

Base: `da37da3`, con cuatro fallos v2 conocidos y una regresión de prompt parcial. La inspección del adaptador y una prueba HTTP falsa verifican que se envían íntegros el prompt actual y el texto solicitado. No se observó un recorte del contexto que explique las confusiones. No se captura contenido HTTP real ni razonamiento privado del modelo.

El formato nuevo añade `request_mode` como primer campo, con una descripción de intención global. Distingue petición inmediata, aplazada, contenido relatado, hipótesis, prohibición, información, ambigüedad y preferencia. La adaptación rechaza combinaciones incompatibles de modo, operación y tiempo antes de producir `Decision`. Se mantiene una sola solicitud, el mismo proveedor y el contrato neutral del motor.

Esto es validación de coherencia de declaraciones del modelo, no verificación independiente de intención. Una declaración falsa pero coherente aún puede pasar el adaptador; siguen vigentes la política local y la revisión obligatoria. Las pruebas fuerzan también ese caso, incluida una orden aplazada que todavía puede ofrecer un borrador.

Antes de la ejecución se fijan ocho turnos **de desarrollo ya conocidos**: los cuatro errores v2 y cuatro controles. Cuatro turnos no piden acción inmediata y cuatro son órdenes positivas. Criterios: cero borradores en los primeros y cuatro planes positivos correctos; clasificación exacta y errores se informan aparte. Un error no cuenta como comprensión ni aprobación. No se presentan estos datos como otro conjunto reservado ni se extrapola su puntuación al resto.

Máximo ocho solicitudes Groq Free, `openai/gpt-oss-120b`, razonamiento `low`, plazo 8 s, intervalo mínimo 20 s, 1024 tokens de salida, sin reintentos ni cambio automático de modelo. La confirmación del evaluador requiere coincidencia de operación y plan completos y solo produce simulación. No se envía audio ni se cambian voz, micrófono o herramientas reales.

La documentación de [Structured Outputs de Groq](https://console.groq.com/docs/structured-outputs) distingue conformidad de formato de corrección semántica. La [referencia de API](https://console.groq.com/docs/api-reference) admite el esquema estricto y el presupuesto `low` para el modelo utilizado. El orden declarativo del nuevo esquema es una hipótesis de diseño; no se afirma que cause una mejora ni que el servidor garantice el orden efectivo de generación.
