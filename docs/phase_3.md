# Fase 3 — motor de comprensión local

Entrega del 10 de noviembre de 2026. Implementación preparada para aceptación física; la fase no se declara cerrada. Base de Fase 2: `f6ac68a`, conservada en `phase-2-baseline`. Desarrollo: `phase-3-intelligence`, versión 0.3.0.

Jarvis interpreta órdenes, propone acciones simuladas, solicita aclaraciones y conversa mediante un modelo local. **No abre aplicaciones, modifica volumen, controla luces ni ejecuta código.** Las respuestas de acciones indican expresamente la simulación. No existe un interruptor que habilite ejecución real.

## Uso en este equipo

Con el residente cerrado, desde la raíz del proyecto:

```powershell
.\.venv\Scripts\python.exe -m jarvis --enable-intelligence
.\.venv\Scripts\python.exe -m jarvis --set-llm qwen3:1.7b
.\.venv\Scripts\python.exe -m jarvis --set-semantic e5-small
Start-Process -FilePath '.\.venv\Scripts\pythonw.exe' -ArgumentList '"scripts\run_resident.pyw"' -WindowStyle Hidden
```

La bandeja permite cambiar entre los dos LLM instalados. Cambiar modelo cancela la sesión actual. Para conservar la voz de Fase 2 sin interpretación, usar `--disable-intelligence` y reiniciar. No se modificaron la selección de micrófono, la voz Piper ni los tiempos de activación para esta entrega.

Diagnóstico escrito, que muestra deliberadamente el texto introducido:

```powershell
.\.venv\Scripts\python.exe scripts\interpret_text.py --text "Pon las luces rojas" --text "No, mejor azules" --no-llm --no-semantic
.\.venv\Scripts\python.exe -m jarvis --diagnostics
.\.venv\Scripts\python.exe -m pytest -q
```

## Instalación reproducible

Requiere la instalación base de voz descrita en `phase_2.md`, Python 3.11 y el entorno del proyecto. Las descargas son explícitas y pueden ocupar varios GB:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-intelligence-lock.txt
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
.\.venv\Scripts\python.exe scripts\install_intelligence.py ollama minilm e5-small qwen3:1.7b qwen3.5:2b
.\.venv\Scripts\python.exe scripts\evaluate_semantics.py --help
```

El último comando muestra las opciones de comparación y calibración semántica. Las calibraciones generadas quedan junto a los modelos; sin calibración válida la ruta semántica no acepta propuestas. El instalador fija revisiones de embeddings y verifica el archivo portable de Ollama por SHA256; las etiquetas de modelos generativos pueden cambiar upstream, por lo que los digests medidos están en `reports/local-model-metadata.json`.

Modelos en `%LOCALAPPDATA%\JarvisCore\intelligence_models`, binario portable en `.tools\ollama`. Al iniciar con inteligencia habilitada se reutiliza Ollama local o se inicia el portable oculto. No se descarga nada durante una conversación. No se registra un servicio Windows nuevo. El protocolo HTTP solo admite loopback; el flujo normal no necesita Internet.

## Configuración

`%LOCALAPPDATA%\JarvisCore\intelligence.json` se valida y guarda atómicamente. Reiniciar tras editarlo. Los valores predeterminados del código dejan la inteligencia deshabilitada hasta activarla explícitamente.

| Campos | Predeterminado | Límites |
| --- | --- | --- |
| enabled / semantic_enabled / llm_enabled | false / true / true | booleanos |
| semantic_model | e5-small | e5-small, minilm |
| model / fallback_model | qwen3:1.7b / qwen3.5:2b | esos dos modelos |
| ollama_url | http://127.0.0.1:11434 | HTTP loopback |
| timeout_seconds / keep_alive_seconds | 12 / 90 | 0.1–120 / 0–300 |
| context_tokens / max_output_tokens | 2048 / 320 | 512–4096 / 64–1024 |
| cpu_threads / gpu_layers | 4 / 0 | 1–8 / 0–99 |
| temperature / conversation_temperature | 0.1 / 0.1 | 0–1 |
| conversation_max_output_tokens | 320 | 32–1024 |
| max_recent_turns / context_ttl_seconds | 6 / 120 | 1–12 / 1–600 |
| clarification_ttl_seconds / max_clarification_attempts | 60 / 3 | 1–180 / 1–5 |
| log_text / version | false / 1 | booleano / versión 1 |

El perfil medido usa CPU y cero capas GPU. No existe todavía un perfil gaming automático. Texto, referencias y preferencias son temporales; `log_text=false` conserva diagnósticos sin transcripciones ni consultas. Mantener también `voice.log_transcripts=false`.

## Aceptación física pendiente

1. Activar con «Jarvis» y probar «Pon las luces rojas»; comprobar que responde en simulación.
2. Continuar «No, mejor azules» y «Y que estén más suaves»; comprobar referencias y correcciones.
3. Probar «No abras Steam», «Si juego mañana, abre Steam» y «Abre una aplicación desconocida»: ninguna acción real y aclaración o respuesta apropiada.
4. Preguntar «¿Qué es una variable?» y después «Explícamelo más fácil»; comprobar continuidad, espera y naturalidad.
5. Cancelar, pausar y salir durante una respuesta; probar recuperación después de suspensión y reinicio.
6. Observar memoria y CPU durante reposo, conversación y juego; comprobar liberación de modelos tras inactividad.
7. Conversar sin nombrarlo para revisar las falsas activaciones pendientes de Rustpotter. El umbral actual es 0.55; esta entrega no acredita su precisión acústica.

Respetar la pausa de escucha después del tono que el usuario aceptó en Fase 2. La segmentación conserva 1200 ms de silencio final. Resultados y límites: `intelligence_validation.md`.
