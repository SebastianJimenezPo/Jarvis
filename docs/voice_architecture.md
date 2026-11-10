# Arquitectura de voz

## Integración conservadora

`LifecycleManager` sigue siendo el único propietario de captura, conversión, Rustpotter y estado global. Se conserva `AWAKE` y se desactiva su plazo rígido únicamente cuando una sesión de voz consiguió arrancar. Si voz está deshabilitada o faltan modelos, se conserva el funcionamiento de Fase 1 y se expone el error de voz.

`VoiceSessionManager` supervisa un proceso Windows creado bajo demanda. Almacena IDs de generación/sesión, subestado y métricas; no importa modelos ni hace inferencia en el hilo de captura. El proceso incorpora STT, Silero, segmentación, DialogueBridge, Piper y reproducción. Se eligió un proceso, en lugar de mantener todas las bibliotecas en el residente, para que cerrar los modelos libere realmente su memoria nativa. Pertenece a un Job Object; pausa, suspensión, cambio de dispositivo y salida terminan el proceso. Se puede conservar 90 s después de la sesión para reducir arranques fríos; luego se cierra. Durante retención no se procesa audio.

La cola de entrada tiene capacidad aproximada de 40 s de PCM en bloques de 20 ms (~1,28 MB de payload, más overhead), más el pre-roll fijo de 1,5 s. La salida se limita a 128 eventos pequeños. Si se llena la entrada, la sesión se cancela explícitamente; no se finge haber conservado una frase completa. Los plazos del supervisor terminan procesos bloqueados. La fuente de captura no espera STT, VAD, síntesis ni reproducción.

## Límites de audio

En DORMANT solo se alimenta Rustpotter y el búfer reciente. Al detectar su nombre se entrega una única copia del pre-roll y después los bloques nuevos; el bloque que disparó la detección no se duplica. El proceso puede cargarse mientras los bloques se acumulan en la cola limitada. En AWAKE se alimenta el proceso de voz y no se procesan activaciones Rustpotter. Al finalizar se limpia el audio y se reinicia solo el auxiliar acústico, conservando el micrófono. Se corrigió la cola de respuestas del adaptador Rustpotter para que un EOF de la instancia anterior no contamine ese reinicio.

## Segmentación y STT

Silero ONNX CPU recibe frames de 512 muestras a 16 kHz y mantiene contexto/recurrent state. El segmentador confirma inicio tras 200 ms de probabilidad suficiente, conserva ~384 ms de pre-roll de turno, tolera pausas y finaliza tras 650 ms de silencio o duración máxima. Los tiempos de segmentación se calculan con cantidad de muestras, no con velocidad de procesamiento de un lote.

Moonshine tiene finalización de líneas y VAD interno. Se inspeccionó su API: esas líneas son parte del decodificador y no constituyen por sí solas el contrato de sesión/turno de ambos motores. Se usa Silero como criterio común y configurable para el benchmark operativo y para Whisper, que recibe lotes; Moonshine conserva su segmentación interna, pero sus callbacks se publican como parciales hasta el fin del turno externo. Esta duplicación limitada permite comparar los STT con la misma delimitación; no se ejecuta ningún VAD en reposo. Falta comparar físicamente umbrales y evaluar si puede eliminarse Silero en un modo exclusivo Moonshine sin degradar turnos.

Los contratos STT y TTS son Protocols. Moonshine usa `Transcriber.create_stream`, `start`, `add_audio`, listeners y `stop`, nunca `MicTranscriber`. El modelo streaming español se carga por ruta local y con proveedor CPU explícito. Whisper usa CTranslate2 CPU INT8, `local_files_only=True` y final único, sin fingir streaming.

`TranscriptManager` identifica sesión/turno, marca parciales/finales, timestamps monotónicos y motor, y descarta duplicados tras un final. Solo el final va al proveedor determinista. La limpieza elimina exclusivamente un prefijo textual «Jarvis» completo, nunca menciones internas ni sílabas aproximadas; pronunciaciones transcritas como «Carvis» no se eliminan arbitrariamente.

## Turnos y eco

Subestados: PREPARING, WAITING_FOR_SPEECH, LISTENING, FINALIZING_TRANSCRIPT, PROCESSING_RESPONSE, SPEAKING y WAITING_FOR_FOLLOWUP. ENDING se representa por el evento session_end y liberación/retorno a IDLE. Las esperas de 6/25 s solo se aplican cuando no existe voz activa. Un turno de ruido sostenido tiene tope de 20 s y la sesión tiene límite de 600 s para evitar permanencia infinita.

El semidúplex bloquea la admisión de audio mientras se finaliza una transcripción, se prepara una respuesta y se sintetiza/reproduce. Después descarta audio encolado cuyo timestamp precede al fin de reproducción + 400 ms, limpia el segmentador y abre seguimiento. Esto protege de eco sin afirmar cancelación acústica. La conversación puede perder palabras si el usuario habla durante la respuesta; las interrupciones por voz están deshabilitadas.

La reproducción usa un OutputStream independiente, nunca otro InputStream. Escribe bloques de unos 20 ms, cierra la salida al terminar y comprueba cancelación entre bloques. Una llamada ONNX ya iniciada no se puede interrumpir cooperativamente; pausa/salida pueden terminar el proceso. El dispositivo auto sigue la salida predeterminada al abrir el stream; cambios de endpoints reinician conservadoramente los recursos de la sesión. La ruta fija rechaza nombres ausentes/ambiguos.

## Recursos, métricas y privacidad

La máquina global sigue emitiendo eventos tipados de Fase 1. El proceso transmite eventos de voz estructurados con sesión, turno y reloj monotónico, que el supervisor filtra por ID activo antes de registrar. Diagnósticos incluyen carga STT, finalización, fin de voz→final, diálogo, primer chunk de síntesis, reproducción, duración del turno, errores, cancelaciones y vacíos. Los eventos permiten calcular inicio de voz→primer parcial; no hay un valor garantizado si el motor no produjo parcial. El muestreo de CPU/RAM del residente incorpora hijos.

Fases futuras pueden sustituir `Phase2ResponseProvider` a través de `DialogueBridge`, sin abrir audio ni modificar los estados desde herramientas. No hay acceso del proveedor a comandos de Windows, LLM o red.
