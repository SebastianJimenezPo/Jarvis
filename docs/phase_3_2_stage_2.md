# Jarvis Next — piloto textual Groq y revisión contextual, 2026-11-14

Continuación autorizada de la primera etapa, base `cda3c5e`. La voz sigue en 3.1; no se habilitan herramientas físicas. La clave `GROQ_API_KEY` no estaba configurada al empezar: se prepara el piloto con HTTP falso y no se inventan resultados remotos.

## Proveedor elegido para el piloto

Candidato `openai/gpt-oss-20b`, no ganador de una comparación aún no realizada. La documentación oficial consultada lo incluye entre los modelos con JSON Schema estricto; ese modo requiere objetos cerrados y todas las propiedades obligatorias. Por eso se usa un contrato de transporte pequeño y cerrado, con valores opcionales como `null`, separado del contrato interno extensible. Las evidencias son citas exactas convertidas a índices localmente, sin pedir al modelo calcular posiciones Unicode. Fuentes: [salidas estructuradas](https://console.groq.com/docs/structured-outputs), [modelo](https://console.groq.com/docs/model/openai/gpt-oss-20b).

Una petición a Chat Completions, sin streaming, tools, búsqueda, código o fallback: límite de salida 1.024 tokens y razonamiento `low`, admitido para ese modelo según la [referencia API](https://console.groq.com/docs/api-reference). El plazo global del motor limita la espera. Se mantiene una conexión TLS verificada al host fijo `api.groq.com`; se descartan redirecciones y respuestas mayores de 64 KiB. No hay SDK ni dependencia nueva. La conexión puede reutilizarse entre turnos; un fallo la cierra y no se reintenta el turno.

Groq distingue Free de Developer y las cuotas exactas varían por organización. El cliente no puede verificar el plan de facturación con una API key. Antes de usarlo, el operador debe comprobar que la cuenta sigue en Free; no añadir pago ni actualizar de plan. No se promete cuota fija o gratuidad de una cuenta Developer. Fuentes: [límites](https://console.groq.com/docs/rate-limits), [facturación](https://console.groq.com/docs/billing-faqs).

Los mensajes contienen solo texto actual, plan operativo y cinco capacidades de simulación. No se envían audio, historial completo, pantalla, archivos, IDs de sesión innecesarios ni claves en el prompt. La clave va solo en la cabecera de autorización al host fijo; no se interpolan cuerpos o excepciones HTTP en errores. Los ajustes Data Controls del proveedor siguen siendo responsabilidad de la cuenta: su política permite retención temporal para fiabilidad/abuso y ofrece opciones de exclusión; no se presenta una promesa absoluta de retención cero. Fuente: [datos en GroqCloud](https://console.groq.com/docs/your-data).

## Límite de autorización

Un esquema válido o una cita literal no demuestran intención correcta. Las órdenes directas conservan su validación independiente. Las decisiones complejas se ofrecen para revisión de desarrollo; todavía no autorizan ejecución real ni se aplican automáticamente por venir de Groq. La revisión queda ligada a contenido, sesión, generación, revisión y caducidad del plan. Se comprobarán cambios de objetivo/valores, adiciones, cancelaciones selectivas y modificaciones atómicas con adaptadores falsos antes de publicar esta parte.

El contrato interno añade `ActionChange.target` opcional para corregir una aplicación sin inventar un nuevo ID. La modificación necesita un objetivo o parámetros; se revalidan juntos contra el registro. Se reprodujo antes de corregir que el destino modificado aún no se contrastaba, aunque la propuesta permanecía retenida: ahora un objetivo inventado produce rechazo, sin alterar el plan.
