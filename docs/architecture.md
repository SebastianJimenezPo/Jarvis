# Arquitectura de Fase 1

## Propiedad y concurrencia

El hilo principal ejecuta Qt y la bandeja. Un `LifecycleManager` en hilo propio es el único propietario del estado, captura, conversión y detector. La interfaz envía comandos por cola limitada; observa los cambios mediante eventos tipados y una señal Qt encolada. Las notificaciones COM de dispositivos y los mensajes de energía de Windows solo envían comandos, sin abrir dispositivos desde callbacks.

El callback PortAudio copia bloques mono float32 de 20 ms y los deposita sin esperar en una cola de 25 bloques. Si se llena, descarta el bloque nuevo y cuenta la pérdida. No hace inferencia, acceso a disco ni trabajo de UI. Los bloques con más de 500 ms de antigüedad se descartan. Una ausencia de audio de tres segundos se considera fallo de captura.

El controlador usa `soxr.ResampleStream` HQ para convertir de la frecuencia efectiva del dispositivo a 16 kHz. La continuidad del filtro se conserva entre bloques. Satura y convierte a PCM s16le. El búfer previo retiene como máximo 1,5 s (48.000 bytes por defecto), en memoria, y expone `snapshot()`; aún no se envía a un transcriptor.

`WakeWordDetector` permite sustituir Rustpotter. El adaptador concreto administra un auxiliar Rust sin acceso a dispositivos. Un hilo lector recibe sus respuestas. Hay una sola trama en vuelo, un plazo de respuesta de dos segundos y una cola de cuatro respuestas. El inicio tiene plazo de 15 s. El auxiliar pertenece a un Job Object Windows con `KILL_ON_JOB_CLOSE`; se comprobó que no sobrevive al cierre abrupto del padre.

## Protocolo 1

- Comando: `jarvis-wakeword.exe detect REFERENCIA UMBRAL UMBRAL_PROMEDIO`.
- Salida inicial JSONL: `ready`, `protocol=1`, `engine=rustpotter-3.0.2`, `sample_rate=16000`, `encoding=s16le`, `frame_bytes`.
- Entrada: longitud `u32` little-endian seguida de exactamente esa cantidad de bytes PCM mono. El tamaño debe coincidir con el negociado por Rustpotter; Python admite hasta 2048 bytes por trama.
- Rust usa `read_exact`, por lo que soporta fragmentación del encabezado y payload. Un tamaño inválido termina con un error explícito.
- Cada trama produce una respuesta JSONL pequeña `result` con `detected` y, si existe, `score`. El audio nunca viaja en JSON.
- EOF entre tramas o longitud cero: cierre normal. EOF dentro de un mensaje: error. Los errores se comunican en JSONL y stderr, nunca mezclados con audio.
- Python valida versión, formato y tamaño. Limita cada línea a 4096 bytes. Una respuesta ausente, proceso muerto o protocolo corrupto pasa a recuperación.
- Cierre: cerrar stdin, esperar un segundo, terminar forzosamente si es necesario, recoger el proceso y unir el lector. No se usan sockets.

Se prefirió una confirmación por trama para hacer verificable el watchdog y limitar presión. A 16 kHz el coste medido quedó por debajo del objetivo de CPU en pruebas cortas; se puede optimizar el protocolo más adelante con mediciones que lo justifiquen.

## Estados, sesiones y recuperación

La máquina rechaza transiciones no autorizadas. `AWAKE` tiene un plazo monotónico de 10 s y no representa una conversación. El enfriamiento comienza al finalizar la sesión. Los IDs de sesión y generación descartan eventos antiguos. No se mantienen temporizadores de sesión independientes que puedan dispararse después de una pausa.

Se permiten además `STARTING → PAUSED`, `DEGRADED → PAUSED` y `PAUSED → DEGRADED`: son necesarias para inicio con escucha desactivada, pausa ante fallo y reanudación que no consigue recuperar recursos. Se documenta esta extensión al diagrama original.

Los fallos cierran captura y detector, limpian búferes y entran en `DEGRADED`. Los reintentos predeterminados esperan 1, 2, 4, 8 y 16 s; el sexto fallo suspende los reintentos. El contador se restablece tras 30 s operativos o un reintento manual/evento de dispositivo. Pausa cancela cualquier reintento pendiente. El retorno de suspensión respeta una pausa previa del usuario.

La selección automática sigue el dispositivo de captura WASAPI predeterminado de consola, no el rol de comunicaciones. Las notificaciones `IMMNotificationClient` detectan cambios sin sondear continuamente dispositivos. Se reinicia PortAudio únicamente con la captura cerrada, porque su inventario es una caché. El modo fijo usa nombre WASAPI exacto y rechaza nombres duplicados; no cambia silenciosamente a otro micrófono.

## Configuración y futuras interfaces

Configuración JSON versionada y validada, persistencia atómica, registros JSONL rotativos (2 MB × 4 archivos). Las referencias y diagnósticos viven en el perfil. El mutex es local a la sesión y al usuario, compartido por residente y calibración.

Fase 2 podrá suscribirse a `SESSION_STARTED` y consumir el búfer reciente. Comprensión, memoria y herramientas no deben abrir el micrófono ni cambiar directamente el estado. No se implementaron clases vacías de chatbot ni herramientas ficticias.
