# Activaciones involuntarias: diagnóstico y ajuste inicial

El usuario reportó activaciones mientras conversaba sin decir Jarvis. Se revisaron estado, detector, configuración, código Rustpotter 3.0.2 y registros. Hay entradas `wakeword_detected` acústicas que abren sesiones desde DORMANT; por tanto, no todo se explica por los 25 segundos de seguimiento de una sesión anterior.

Umbral local previo: 0,50. Las últimas cinco detecciones registradas tenían puntuaciones 0,5855; 0,5210; 0,5060; 0,5434; 0,5330. Cuatro eran débiles respecto al nuevo umbral. No se conservó audio ni texto de esos sonidos: **no se puede etiquetar cada evento como falso positivo ni identificar la palabra que lo causó**. Una puntuación de similitud tampoco es una probabilidad de acierto. En todo el historial, 9 de 54 detecciones acústicas quedaron debajo de 0,55; algunas podrían ser invocaciones genuinas. Evidencia: `reports/wake-sensitivity-audit.json`.

Se aplicó un ajuste **provisional**, exclusivo del perfil del usuario: umbral 0,50 → **0,55**, con copia de configuración anterior. No se modificaron pre-roll, palabra de activación, señal, pausas, micrófono, ventana de seguimiento ni modelos STT. No se añadió transcripción continua. El valor predeterminado del código se conserva para no asumir que este ajuste sirve a cualquier voz.

También se añadió validación de puntuación en el controlador, antes de activar sonido/sesión, y diagnóstico por candidato: umbral usado, estado, puntuación media, cantidad de coincidencias parciales y similitud por referencia. Estos datos salen del detector local; no contienen grabaciones ni texto reconocido. La emisión de campos es compatible con el protocolo 1. El auxiliar se recompiló realmente.

## Cómo comprobar el ajuste

1. Con Jarvis dormido, decir Jarvis diez veces, dejando terminar cada sesión. Anotar aciertos y omisiones; no exigir que una única sesión activa vuelva a detectar el nombre.
2. Conversar normalmente 20–30 minutos sin invocarlo. Anotar la hora de cada tono/activación accidental. La observación de una sesión de seguimiento abierta debe distinguirse de una nueva activación desde reposo.
3. Comparar con música/juegos y con la misma distancia y micrófono. No cambiar varios parámetros a la vez.

No hay todavía una tasa de falsos positivos por hora ni una prueba real que demuestre que 0,55 sea suficiente. El nuevo umbral puede omitir invocaciones bajas, lejanas o pronunciadas de otra manera. Si ocurre, comparar 0,53/0,54; si persisten falsas activaciones, estudiar las coincidencias por referencia, recalibrar varias muestras consistentes o evaluar otro detector. No subir indefinidamente el umbral hasta que deje de detectar la voz.

Para ajustar explícitamente y después reiniciar:

```powershell
.\.venv\Scripts\python.exe -m jarvis --set-wake-threshold 0.55
```

El historial permite orientar, pero no sustituye un conjunto etiquetado de positivos y conversación negativa. Las grabaciones de pruebas requieren elección explícita del usuario; no se almacenó conversación ambiental durante este diagnóstico.

Referencia primaria sobre parámetros: [Rustpotter 3.0.2 DetectorConfig](https://docs.rs/crate/rustpotter/3.0.2/source/src/config.rs).
