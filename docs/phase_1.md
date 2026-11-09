# Calibración y uso

1. Cierra Jarvis desde la bandeja. El mutex impide calibrar mientras otro proceso está capturando.
2. Lista dispositivos con `python -m jarvis --list-devices` dentro del entorno. Para fijar uno: `python -m jarvis --select-device 'nombre WASAPI exacto'`. Para volver al predeterminado: `--select-device auto`.
3. Ejecuta `python -m jarvis --calibrate-wakeword --samples 6`.
4. Escribe `GRABAR` para autorizar las muestras. Cada pulsación de Enter inicia unos 2,2 segundos de captura: di «Jarvis» una vez con pronunciación habitual. Se admiten entre cinco y ocho muestras. Mantén la distancia normal, con poco ruido.
5. Las muestras silenciosas, demasiado cortas o saturadas se rechazan. El recorte por energía es una ayuda de calibración, no un VAD de conversación. Si hay ruido intenso puede recortar mal; vuelve a calibrar en mejores condiciones.
6. Se generan características acústicas Rustpotter, se comprueba que el detector puede cargarlas y se reemplaza la referencia de forma atómica. Los WAV temporales se borran al terminar normalmente, también ante excepciones controladas. Un apagado abrupto durante calibración puede dejar una carpeta `jarvis-calibration-*` en TEMP; revisa y elimina solo esa carpeta si ocurre.
7. Ejecuta el residente, di «Jarvis», comprueba `AWAKE` y espera el retorno a `DORMANT` tras diez segundos. La señal es un sonido de Windows, no TTS.

Repite la calibración para sustituir la referencia. Conserva solo la referencia acústica necesaria, que también deriva de tu voz y es un dato local. No se transmiten muestras. Para borrarla elimina el archivo configurado con Jarvis cerrado.

## Medir sensibilidad

Una referencia de pocas muestras puede ser menos precisa que un modelo entrenado con un conjunto amplio. Los umbrales iniciales no están validados para tu voz. Prueba, por separado: voz cercana, 1–3 metros, ruido, música, videojuegos, palabras parecidas, repeticiones y horas sin invocaciones. Anota aciertos, omisiones y falsas activaciones por hora.

Subir `threshold` suele hacer más estricta la detección; bajar facilita coincidencias y puede aumentar falsas activaciones. Modifica un parámetro cada vez y repite el mismo conjunto. Reinicia tras cambiar configuración.

Para evaluar archivos que hayas decidido grabar y conservar por separado:

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_audio.py '.\prueba.wav' --expected-end 1.2 4.7
# Archivo negativo: ninguna palabra esperada
.\.venv\Scripts\python.exe scripts\evaluate_audio.py '.\ruido.wav' --expected-end
```

Acepta WAV PCM de 16 bits; convierte canales a mono y remuestrea. `--expected-end` indica el final anotado de cada palabra. Empareja detecciones en una ventana de -0,3 a +1,5 s; reporta latencia relativa al audio, aciertos, omisiones y falsos positivos. Sin anotaciones esas métricas quedan ausentes. La ejecución fuera de línea no mide la latencia del micrófono/UI ni acredita precisión de uso real por sí sola.

La calibración interactiva y el conjunto de voz real permanecen pendientes de participación del usuario. No se ha creado una referencia «Jarvis» falsa en su perfil.
