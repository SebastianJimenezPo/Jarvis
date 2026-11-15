# Prueba física breve de Jarvis Next

Perfil experimental, **todo en simulación**. No abre aplicaciones ni cambia el volumen real. Conserva tu micrófono, activación, pausas y voz actuales. La integración sintética todavía falla en transcripciones; esta prueba con tu voz sigue pendiente.

## Abrirlo

Si tienes otro Jarvis abierto, usa su menú **Salir completamente**. Desde PowerShell en la carpeta del proyecto:

```powershell
.\scripts\start_next.ps1
```

Abre el perfil Next con Groq 120B Medium bajo demanda, plazo 4 s y la cuenta Free ya autorizada. La clave se lee del almacén de Windows; no se pega en comandos. La preparación de voz puede hacer lenta la primera respuesta. Espera a que Jarvis termine de hablar antes de responder.

Para probar solo órdenes locales sin red:

```powershell
.\scripts\start_next.ps1 -Offline
```

## Seis comprobaciones

1. Di **«Jarvis, abre una aplicación»**. Debe preguntar cuál. Responde **«Spotify»**: debe describir una simulación para Spotify. Si no reconoce el nombre, anota lo que ocurrió; no se considera aprobada por funcionar con otra frase. En otra pregunta puedes probar **«el segundo»**, que selecciona Steam del orden anunciado.
2. Di **«Abre Steam, pero todavía no hagas nada»**, luego **«Mejor Spotify»**. Debe conservar la propuesta **retenida**. Un «sí» aislado no la autoriza. Di **«Autoriza la simulación»**, escucha la propuesta completa y luego **«sí»**: solo entonces debe confirmar su simulación.
3. Di **«No abras Steam»**, luego **«Cuando termine de jugar, abre Steam»**. Debe abstenerse en el primer caso y decir que todavía no puede programar la solicitud futura en el segundo. No debe ofrecer abrirlo inmediatamente.
4. Di **«Volumen al 30%»**, luego **«Cancela»**, y después **«sí»**. Debe simular, descartar lo pendiente y rechazar la confirmación sin propuesta vigente. El volumen físico debe permanecer igual.
5. Prueba **Cancelar respuesta** en la bandeja durante una petición; también pausar y reanudar la escucha. No debe hablar una respuesta anterior ni aceptar su confirmación después. La suspensión real de Windows queda para tu comprobación física; no se declara aprobada por las pruebas de software.
6. Deja terminar la sesión y espera unos 20 s adicionales. El trabajador de voz debe descargarse. Abre **Diagnósticos** para consultar CPU/RAM y tiempos; prueba también salir completamente. No se ha modificado el inicio automático anterior.

Indica por cada prueba la frase dicha, la respuesta y si ocurrió en la primera activación o con el trabajador ya caliente. No hace falta grabar ni enviar audio. Si necesitas escuchar qué entendió STT, el menú **Repetir reconocimiento (diagnóstico)** repite la transcripción localmente, sin tratarla como orden; desactívalo al terminar. El registro de transcripciones permanece desactivado salvo que lo habilites explícitamente.

## Comparación local de reconocimiento, solo si hace falta

No se ha cambiado tu reconocedor. Existe una alternativa ya instalada para una sesión de comparación, sin guardar la selección:

```powershell
# Cierra primero la instancia anterior.
.\scripts\start_next.ps1 -Offline -Stt whisper-base
```

Prueba las mismas frases en ambos perfiles. La comparación sintética no justificó sustituir Moonshine. Para comparar grabaciones que hayas creado y autorizado localmente, prepara en `build` un JSON con hasta ocho elementos `{"audio":"ruta.wav","text":"referencia"}` y ejecuta:

```powershell
.\.venv\Scripts\python.exe scripts\compare_next_stt.py --dataset build\mis_clips.json --output build\mi_comparacion_stt.json
```

Solo acepta WAV mono de 16 bits, hasta 20 s por clip. No captura micrófono, descarga modelos ni envía audio o texto a un servicio. Los archivos y el informe personal deben quedar en `build`, fuera de Git.
