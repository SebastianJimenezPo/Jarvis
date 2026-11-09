# Configuración

Archivo: `%LOCALAPPDATA%\JarvisCore\config.json`. `--data-dir RUTA` permite perfiles de pruebas aislados, pero el mutex sigue impidiendo dos propietarios del micrófono por usuario/sesión. Reinicia Jarvis después de editar la configuración. Los cambios de pausa desde la bandeja duran esta ejecución; `listening=false` desactiva la escucha al arrancar.

| Campo | Tipo y valor inicial | Rango / significado |
|---|---|---|
| version | entero, 1 | Solo 1 |
| listening | booleano, true | Escucha al iniciar |
| device | texto, auto | Predeterminado WASAPI o nombre WASAPI exacto no vacío |
| reference | texto, jarvis.rpw | Relativa a `references/` o ruta absoluta |
| threshold | número, 0.5 | 0.01–1; sin calibración de precisión todavía |
| avg_threshold | número, 0.2 | 0–1; prefiltro promedio |
| cooldown_seconds | número, 3 | 0–60, desde el final de la sesión |
| active_seconds | número, 10 | 1–300, sesión demostrativa |
| confirmation | booleano, true | Sonido de sistema asíncrono; puede ser silencioso si Windows no lo tiene configurado |
| log_level | texto, INFO | DEBUG, INFO, WARNING, ERROR |
| preroll_seconds | número, 1.5 | 0–5, retención de audio en RAM |
| queue_blocks | entero, 25 | 2–100 bloques de 20 ms |
| retry_initial_seconds | número, 1 | 0.5–60 |
| retry_max_seconds | número, 30 | 1–300 y no menor que el inicial |
| retry_limit | entero, 6 | 1–20 fallos consecutivos |

Los campos desconocidos, valores fuera de rango, tipos incorrectos y números no finitos producen un error con ubicación de registros. No se sustituye silenciosamente una configuración dañada. Para restaurar valores iniciales preservando el archivo anterior:

```powershell
.\.venv\Scripts\python.exe -m jarvis --reset-config
```

No existe una bandera `startup` desconectada de Windows: la fuente de verdad es la tarea registrada, y se gestiona con los scripts de instalación/eliminación. Las credenciales no se guardan.

Los diagnósticos del menú contienen el estado en vivo, tiempos por estado, errores y estadísticas. `--diagnostics` muestra disponibilidad y entorno sin capturar audio. CPU/GPU o latencias no medidas se representan como `null`, no como cero.
