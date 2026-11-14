# Rendimiento de Fase 3.1

Resultados locales del 10 de noviembre de 2026, CPU de 16 procesadores lógicos. No se midieron FPS ni interferencia real con juegos. Las mediciones anteriores se conservan; las nuevas no convierten promedios en topes garantizados.

Reposo posterior: 30 s con micrófono real, voz e inteligencia habilitadas y referencia de activación sintética de chirp (no la referencia personal). CPU media 0.365%, máximo muestreado 0.625%, RSS máximo del árbol residente 89.3 MB decimales. Cero activaciones, pérdidas o reinicios. Ollama externo separado: unos 25 MB residentes, sin modelos cargados antes/después y delta de CPU cero a la resolución medida. Informe `phase31-idle-30s.json`; no se presenta esta muestra corta como estabilidad prolongada.

## Qwen: 54 peticiones

`compare_phase31_performance.py` ejecuta tres repeticiones por perfil de 2/3/4 hilos, tres cargas (pregunta breve, pregunta con contexto fijo, JSON estructurado) y dos estados (carga fría tras descarga explícita y segunda petición preparada). Mismos prompts, contexto 2048, semilla 17, thinking deshabilitado y cero capas GPU. La caché del disco, orden y temperatura del equipo siguen siendo factores. El plazo de comparación es 45 s; el residente conserva 12 s.

Medianas de tres muestras, segundos:

| Hilos | Breve fría / preparada | Contexto frío / preparado | JSON frío / preparado |
| --- | --- | --- | --- |
| 2 | 5.138 / 1.571 | 6.861 / 1.032 | 10.321 / 3.977 |
| 3 | 4.906 / 1.261 | 6.375 / 0.850 | 8.795 / 3.267 |
| 4 | 4.783 / 1.198 | 5.846 / 0.816 | 8.316 / 2.956 |

CPU media de máquina durante generación preparada: aproximadamente 12.3–12.5%, 18.7% y 24.8–25.2%, respectivamente. Picos máximos muestreados por perfil: aproximadamente 15.2%, 21.2% y 31.3%. Árbol Ollama: unos 1.66–1.71 GB decimales de RSS pico, VRAM reportada cero. El proceso servidor y todos sus descendientes están incluidos; las páginas compartidas podrían contarse más de una vez. Sin errores de transporte y 18/18 respuestas estructuradas válidas en esquema; validez JSON no demuestra intención correcta.

`reports/phase31-performance.json` conserva respuestas, carga, prompt, generación, tokens por segundo, CPU media/máxima y memoria. No mide STT ni tiempo hasta voz: eso corresponde al informe de integración.

## Retención y streaming

La sonda adicional (`phase31-retention-streaming.json`) hizo dos solicitudes separadas por dos segundos con retención 0/30/60. Con cero, ambas tardaron aproximadamente 5.6–5.7 s. Con 30 o 60 s, la segunda tardó 1.6–1.7 s frente a 5.4–5.6 s iniciales. Se observó la lista de modelos vacía a los 30.375 s después de la última respuesta del perfil de 30. El de 60 se descargó explícitamente; no se afirma haber observado su caducidad completa. Una muestra por retención, sin estimación estadística.

La sonda conversacional streaming detectó contenido a los 0.074 s en dos peticiones preparadas, pero la primera frase completa llegó a los 1.527/1.545 s y el final a los 1.576/1.592 s. El ahorro disponible antes de una frase completa fue de unos 50 ms. No justifica añadir reproducción incremental compleja para este estímulo breve. La producción conserva respuestas completas y las propuestas JSON se validan íntegramente. No se sintetizan ni autorizan fragmentos parciales.

## Caché y fallos

Ollama mantiene solo metadatos de etiquetas/capacidades durante 15 s, nunca respuestas. Invalida ante cambio de modelo/servidor, refresco explícito de instalación con digest diferente, caducidad o error de modelo desconocido. Los cambios externos se detectan como máximo al próximo refresco; no se presume una notificación instantánea de instalaciones ajenas. No hay bucles de reintento ni descargas automáticas. Las pruebas verifican que cada solicitud sigue consultando al modelo y que los metadatos no se reutilizan indefinidamente.

## Memoria E5 y salida de procesos

En un proceso nuevo con LLM simulado para aislar ONNX: 44.7 MB de RSS antes de E5, 820.4 MB cargado, 78.2 MB después de descargarlo y 823.5 MB al recargarlo. La conversación posterior a una consulta semántica mantiene E5 hasta descargarlo o terminar el proceso. Se verifica descarga y recarga funcional y salida real del proceso.

El seguimiento de Python registró aproximadamente 0.1–1.3 MB de asignaciones participantes; eso no incluye toda la RAM de Python ni las bibliotecas nativas. No se resta tracemalloc de RSS para fingir una medición de memoria nativa o reservada. El informe conserva contadores Windows privados/pagefile sin confundirlos con reserva virtual. Ollama no forma parte de estas cifras y se mide aparte. `phase31-semantic-lifecycle.json` también comprobó un proceso real de voz con silencio: salió a los 22.64 s, incluyendo preparación, espera inicial y retención configurada de 20 s, sin error. No hubo micrófono ni reproducción en ese ensayo.

## Perfiles manuales

```powershell
.\.venv\Scripts\python.exe scripts\set_performance_profile.py gaming
.\.venv\Scripts\python.exe scripts\set_performance_profile.py balanced
.\.venv\Scripts\python.exe scripts\set_performance_profile.py saving
```

Reiniciar después de seleccionar uno. Gaming conserva dos hilos Qwen, retención LLM 30 s y voz 20 s. Balanced ofrece tres hilos y retención 60/30 s. Saving usa dos hilos y retención 0/0 s, con recargas más frecuentes. Voz sigue limitada a dos CPU lógicas; la comparación STT no mostró ventaja de precisión con cuatro en los estímulos utilizados. Micrófono, umbral, VAD, privacidad y habilitación de motores se conservan. No hay detección automática de videojuegos. El perfil actual de dos hilos se mantiene por la prioridad de consumo expresada por el usuario.

Pendiente físico: en el mismo juego/escena y ajustes, comparar sin Jarvis, reposo, STT, carga E5, Qwen y Piper; anotar FPS/frametimes y CPU/RAM/GPU con la misma herramienta. Repetir cada condición y esperar descarga entre pruebas. No atribuir a Jarvis diferencias de escenas distintas ni publicar conversaciones o audio en los informes.
