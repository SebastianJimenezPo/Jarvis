# Arquitectura de inteligencia

El núcleo conserva un único propietario de captura, Rustpotter y sus estados. El proceso de voz existente conserva VAD, Moonshine y Piper. Dentro de ese proceso se crea un proveedor de inteligencia persistente; `DialogueBridge` mantiene su interfaz y el proveedor de Fase 2 sigue disponible cuando la configuración deshabilita inteligencia.

## Recorrido de un turno

1. STT entrega texto final con identificadores de sesión y turno.
2. Guardas lingüísticas detectan cancelación, negación, hipótesis, futuro, preferencias y solicitudes no soportadas.
3. Ruta rápida interpreta el catálogo conocido, referencias y aclaraciones. La ruta semántica usa ONNX y calibración por intención; el LLM local resuelve los casos restantes o conversa.
4. Pydantic valida estructura. Un validador separado comprueba intención permitida, destino, parámetros, cláusula de origen, referencias y evidencia del texto. La similitud o un JSON válido no autorizan una acción.
5. `DryRunExecutor` registra propuestas únicamente en una colección acotada en RAM. No contiene adaptadores de ejecución del sistema.
6. Se actualiza contexto y se compone una respuesta que distingue simulación. Piper reproduce la respuesta por la infraestructura existente.

`contracts.py` separa interpretación, propuesta y decisión. `catalog.py` describe 19 intenciones y destinos permitidos; la versión legible por herramientas está en `simulated_action_catalog.json`. No se aceptan rutas arbitrarias, comandos shell ni herramientas inventadas por el modelo. Valores fuera de rango, números negativos inválidos y parámetros sin evidencia se rechazan.

## Contexto y aclaraciones

Hasta seis turnos recientes y doce referentes; caducidad predeterminada de 120 s. Los referentes distinguen una mención explícita de un estado propuesto en simulación: nunca se afirman estados físicos observados. Una corrección cambia la parte pertinente del plan sin perder acciones no relacionadas. «Como estaba» requiere información suficiente o genera aclaración.

Una aclaración almacena intención, parámetros, candidatos, datos faltantes y propuestas anteriores todavía no emitidas. Caduca a los 60 s o tras tres intentos y se descarta al cambiar de sesión. «Sí», «la segunda» o un color se interpretan solo dentro de una aclaración compatible. Las preferencias duran la sesión/contexto y no se guardan en base de datos.

El padre conserva una instantánea en RAM para recuperar referencias cuando vuelve a crearse el proceso de voz. Ese evento no se escribe al registro. Las instantáneas restauradas respetan caducidad; las aclaraciones no atraviesan sesiones. No se guarda audio. Los errores de validación también se redactan cuando el registro de texto está deshabilitado.

## Recursos, fallos y cancelación

Los modelos de voz/semántica se cargan bajo demanda en el proceso de voz, retenido por 90 s de inactividad. Ollama es un proceso externo, medido por separado; admite un modelo cargado y una petición a la vez en el servicio portable configurado. Cada petición solicita cuatro hilos, cero capas GPU, contexto 2048 y retención 90 s. No se carga un LLM por permanecer en `DORMANT`.

HTTP tiene límite de respuesta, plazo y cancelación. Se comprueba la identidad de sesión/turno antes de publicar resultados y modificar el plan. Cambiar modelo cancela la voz en curso. Al cerrar, el cliente solicita liberar solo los modelos que utilizó. La retención de Ollama cubre además la terminación forzada del proceso. La liberación no supone que todo el proceso servidor deje de consumir RAM.

Si faltan servicio, dependencias, modelos o calibración, las rutas disponibles siguen funcionando; no se descarga automáticamente ni se reintenta indefinidamente. El modelo alternativo solo se selecciona si no está instalada la etiqueta preferida. La salida libre tiene filtros contra algunas afirmaciones de ejecución o acceso a Internet; esos filtros no garantizan eliminar todas las alucinaciones.

## Límites

Las guardas y el catálogo son conservadores y dependen de expresiones lingüísticas conocidas. La conversación usa historia recortada por caracteres, una aproximación al presupuesto de tokens. La precisión end-to-end depende del STT: las pruebas sintéticas detectaron errores en frases cortas. La similitud semántica y los modelos crudos cometieron errores en las comparaciones; no se presentan como clasificadores fiables por sí solos. No hay memoria permanente, acceso a Internet conversacional, automatización real ni integraciones de Fase 4.
