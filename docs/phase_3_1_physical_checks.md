# Aceptación física pendiente — 0.3.1

Las pruebas de fases anteriores no sustituyen esta comprobación. Mantener micrófono actual, umbral 0.55, silencio final 1200 ms y perfil gaming. Las respuestas hablan de simulación; no deben abrir aplicaciones ni cambiar luces o volumen. No hace falta guardar audio ni conversaciones. Anotar frase, resultado observado y demora aproximada; si hay un fallo, conservarlo y continuar con los demás.

## A–F con voz real

Decir Jarvis y esperar a que termine el tono. Hablar cuando esté escuchando; durante inferencia y respuesta conserva semidúplex. Repetir cada secuencia tres veces, en sesiones separadas, sin reformular un fallo para contarlo como acierto.

| Secuencia | Frases en orden | Comprobar |
| --- | --- | --- |
| A | «Pon las luces rojas y abre Steam» → «No, mejor azules» → «Y que no alumbren tanto» → «Pero todavía no hagas nada» → «Bueno, olvida lo de las luces» | Corrección solo de luces, Steam conservado, reducción de brillo, ninguna autorización inmediata tras el veto y cancelación selectiva sin inventar estado físico. |
| B | «Abre una aplicación» → «No canceles» → «Steam» → «No, mejor Chrome» | Pregunta por aplicación; no canceles conserva la pregunta; Steam la resuelve; Chrome corrige la aplicación. |
| C | En sesiones separadas: «No abras Steam»; «Cuando termine de jugar, abre Steam»; «Abre Steam» | Solo la última permite propuesta inmediata simulada. Probar también «Abre Steam, pero no lo hagas todavía». |
| D | «Pon las luces azules» → «Cancela»; nueva sesión: «Abre una aplicación» → «No quiero cancelar» → «Spotify» | Cancela termina/cancela; no quiero cancelar mantiene pendiente. Durante pensamiento o voz probar cancelar desde bandeja: no debe aparecer una respuesta tardía en la siguiente sesión. |
| E | «¿Qué es la memoria RAM?» → «Explícamelo más sencillo» → «Dame un ejemplo» → «Gracias, hablamos luego» | Mantiene tema, respuestas breves, cierra y vuelve a reposo sin inventar mediciones del PC. |
| F | «Por favor pon la luz principal de color rojo» → «Mejor azules»; también «Ponla en lo principal de color rojo» | Reconocimiento corto; ante destino dudoso pide aclarar y conserva color. Nunca sustituye sonidos parecidos por órdenes supuestas. |

## Activación, estabilidad y recursos

1. Hacer diez llamadas etiquetadas con `scripts/diagnose_wakeword.py --attempts 10 --window 5 --noise-seconds 30`. En la ventana de ruido hablar sin decir Jarvis. Anotar intentos perdidos y falsas activaciones; no modificar umbral a partir de una sola anécdota.
2. Conversar con pausas naturales menores de un segundo; comprobar que se mantiene el comportamiento aceptado. Durante respuesta no se espera activación hablada. Probar bandeja: pausar/reanudar, salir, suspensión y reinicio. Confirmar una sola instancia.
3. Mantener 30 minutos en reposo: CPU baja, sin crecimiento sostenido de RAM ni modelo Qwen permanentemente cargado. Después de una consulta esperar fin de sesión más 20 s para salida de voz; Ollama tiene retención aproximada de 30 s tras su última solicitud. La memoria del servidor externo no llega a cero.
4. En el mismo juego, escena y ajustes, medir sin Jarvis, reposo, activación/STT, E5, Qwen y Piper. Repetir tres veces por condición y registrar FPS, frametime y CPU/RAM de Jarvis y árbol Ollama por separado. Ver [perfil y límites](phase_3_1_performance.md). No activar balanced antes de comparar gaming.
5. Audífonos o cambio de micrófono son una evaluación separada cuando el usuario elija dispositivo. El código separa captura y motores; esta fase conserva el dispositivo actual.

Si hay un fallo de reconocimiento, el [diagnóstico voluntario](phase_3_1_voice.md) permite separar transcripción, interpretación y síntesis. `--include-text` guarda texto solo en el informe local y es opcional. No subirlo automáticamente.
