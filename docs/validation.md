# Validación — 2026-11-09

## Estado de entrega

**Validación funcional básica completada en este equipo**, con referencia personal calibrada y detecciones reales. Se comprobó el ciclo de activación, pausa/reanudación, inicio después de reinicio, suspensión/reanudación y salida. Quedan pruebas prolongadas, precisión acústica cuantitativa y confirmación del endpoint de los audífonos; no se declara superada esa validación restante.

## Comprobaciones ejecutadas

- Compilación real Rust release con 1.85.1 GNU; repetida con `--locked` satisfactoriamente. Ejecutable disponible localmente.
- Python 3.11.14 y todas las dependencias instaladas en `.venv`.
- Suite automática: estados y todas sus transiciones, sesiones antiguas, enfriamiento, configuración corrupta, cola limitada, búfer circular, conversión 16/44,1/48 kHz, mutex nativo, fallos simulados de captura, recuperación, pausa, suspensión simulada, límite de reintentos y cierre.
- Auxiliar Rust real: generación/carga de referencia sintética, detección de esa referencia, silencio, ruido pseudoaleatorio controlado, lecturas fragmentadas, longitud inválida, proceso terminado y watchdog de auxiliar bloqueado.
- Job Object real: se mata el proceso padre y se verifica que su hijo no permanece.
- Arranque real de la aplicación sin referencia: `DEGRADED`, reintentos espaciados y cierre completo.
- Enumeración real de dispositivos: micrófonos Realtek y AirPods disponibles, con WASAPI a 48 y 16 kHz respectivamente.
- Programador de tareas: construcción de acción, desencadenador, principal y ajustes con `-ValidateOnly`. No se registró tarea. Desinstalación con `-WhatIf` informó que no estaba instalada.
- Lanzador `pythonw.exe` ejecutado desde otro directorio, con perfil que contiene espacios y acentos: terminó correctamente y generó diagnóstico, con escucha desactivada para esta prueba.
- Bandeja Qt real con captura/detector simulados: acciones programáticas de pausa, reanudación, activación y salida recorrieron `PAUSED → DORMANT → AWAKE → STOPPING` y liberaron recursos.
- Resultado final: **62 pruebas superadas en 13,60 s**. Se comprobó que no quedaron procesos Jarvis ni auxiliares al finalizar.

El resultado final de pytest está guardado en `reports/pytest.txt`. Los ensayos simulados verifican control de flujo, no precisión acústica ni desconexión de hardware.

## Rendimiento medido

Proceso Python con bandeja Qt, captura WASAPI real y auxiliar Rustpotter real. Referencia de chirp sintético de seis muestras, temporal; no es la palabra Jarvis. Audio del micrófono solo en memoria. Las ejecuciones terminaron voluntariamente y cerraron recursos.

| Medición | 60 segundos | 30 segundos después de cambios |
|---|---:|---:|
| Tiempo DORMANT | 59,843 s | 29,860 s |
| CPU media sobre la máquina | 0,382 % | 0,416 % |
| CPU máxima de las muestras | 0,605 % | 0,565 % |
| RSS máximo muestreado, padre + auxiliar | 80,88 MiB | 80,69 MiB |
| Bloques perdidos / overflows | 0 / 0 | 0 / 0 |
| Reinicios / fallos de captura | 0 / 0 | 0 / 0 |
| Pico de cola | 1 bloque | 1 bloque |
| Inicialización de recursos del controlador | 0,375 s | 0,375 s |

Archivos originales: `reports/hardware-60s.json` y `reports/hardware-30s.json`. El segundo registra el micrófono Realtek a 48 kHz. `initialization_seconds` mide desde crear el controlador hasta recursos preparados, excluyendo arranque de intérprete e importaciones previas.

Metodología CPU: diferencias de tiempo CPU usuario+kernel del proceso y sus hijos entre muestras, divididas por tiempo de pared y por 16 procesadores lógicos. Muestreo cada cinco segundos; primera muestra sin delta se excluye. Se resume la media aritmética y máximo de los intervalos. La primera aparición y salida de hijos puede omitir su fracción de CPU en los bordes. No es un perfil de arranque ni una medición de picos instantáneos. RSS suma working sets y puede contar páginas compartidas más de una vez; el máximo solo refleja muestras, no todos los instantes.

Ambas mediciones quedaron dentro de los objetivos iniciales de CPU y RAM. Su duración y referencia no permiten extrapolar a horas de escucha, voz personal, ruido intenso o videojuegos. No se midieron GPU ni FPS; esos resultados permanecen ausentes. No se afirma que el consumo GPU sea cero solo porque no se cargó un modelo CUDA.

## Aceptación pendiente con el usuario

Actualización más reciente: el usuario confirmó inicio correcto después de reinicio, suspensión/reanudación, salida completa y consumo bajo observado en Administrador de tareas (sin nuevas cifras). Los registros corroboran `suspend`, `power_resume`, recuperación a DORMANT, una detección posterior y `shutdown_complete`. En la inspección posterior no quedaron procesos residentes Jarvis ni auxiliares. Al conectar audífonos hubo recuperación por `devices_changed`, pero todos los eventos `audio_ready` disponibles seleccionaron Realtek: no está confirmado que se utilizara el micrófono de los audífonos. Evidencia y distinción entre observación del usuario y registros: `reports/user-acceptance.json`. Las notas anteriores que siguen son el historial de validación.

Actualización posterior: el usuario confirmó que funcionaron pausa y reanudación. Se registró la tarea de inicio automático del usuario y se consultó de nuevo en el Programador: estado Ready, pythonw del entorno virtual, lanzador y directorio correctos, token interactivo y nivel limitado. No se reinició ni se cerró la sesión; la ejecución efectiva al iniciar sesión sigue pendiente.

Actualización tras la primera prueba de voz: el usuario completó la calibración y realizó una prueba en vivo. Se registraron tres detecciones acústicas reales (puntuaciones 0,6152; 0,6342; 0,6231), tres sesiones y tres retornos automáticos a DORMANT tras aproximadamente diez segundos. La referencia personal cargó correctamente. Evidencia: `reports/first-user-voice-test.json`. Esto comprueba el ciclo básico con su voz; no establece todavía tasa de precisión, latencia acústica ni falsos positivos por hora. La percepción de la señal sonora sigue sin confirmación explícita.

- Confirmar percepción de la señal de activación; calibración, detección real y retorno tras 10 s ya comprobados en la primera prueba.
- Medir falsos positivos por hora, omisiones, latencia de voz, distintas distancias, palabras similares, música y ruido. Las detecciones sintéticas no sirven como evidencia de esta precisión.
- Confirmar específicamente cambio al micrófono de los audífonos y desconexión/reconexión del dispositivo seleccionado. La conexión de audífonos se probó, pero los registros muestran captura Realtek.
- Suspensión/reanudación física e inicio tras reinicio: superados según el usuario; suspensión y recuperación corroboradas por registros.
- Sesiones de varias horas y juegos con comparación de FPS/latencia y consumo GPU.
- Revisión visual/interacción manual del icono y confirmación sonora. La ejecución y las acciones Qt pueden verificarse automáticamente, pero eso no sustituye la experiencia del usuario.

## Límites conocidos

Selección fija por nombre WASAPI, no endpoint ID persistente. Dependencia de reinicialización privada de sounddevice para refrescar inventario. Calibración por referencias y recorte energético sensibles al ruido. No hay instalador final ni actualización automática. El límite de reintentos necesita acción manual o un evento de dispositivo tras fallos persistentes. Un controlador de audio nativo bloqueado requiere diagnóstico físico; no se garantiza recuperación de todo fallo de driver.
