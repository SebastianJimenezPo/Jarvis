# PROYECTO JARVIS
## DOCUMENTO MAESTRO DE ARQUITECTURA, FILOSOFÍA Y DESARROLLO
### Versión 1.0 — Construcción desde cero
### Instrucciones para Codex — Implementación inicial: Fase 1

---

# 0. INSTRUCCIÓN PRINCIPAL PARA CODEX

Actúa como arquitecto principal de software, ingeniero especializado en sistemas Windows, desarrollador de aplicaciones residentes de bajo consumo y experto en procesamiento de audio en tiempo real.

Tu responsabilidad es diseñar y desarrollar **JARVIS**, un asistente personal de voz para Windows, completamente nuevo, modular, eficiente y prioritariamente local.

No debes limitarte a modificar un proyecto anterior ni reproducir las decisiones técnicas de otra implementación.

Este documento representa la visión definitiva del producto.

Debes comprender el propósito completo del proyecto antes de escribir código, pero **en esta primera intervención implementarás exclusivamente la Fase 1: núcleo residente, activación por voz, administración del micrófono, gestión del ciclo de vida y ejecución automática con Windows**.

No implementes todavía un chatbot, control de Spotify, automatización de aplicaciones, inteligencia artificial generativa, síntesis de voz avanzada ni interfaz gráfica elaborada.

Sin embargo, diseña las interfaces internas necesarias para incorporar esas funcionalidades sin reconstruir el núcleo.

**La prioridad absoluta es crear una base real, ejecutable, estable, medible y ampliable.**

No quiero prototipos que simulen un funcionamiento inexistente, dependencias ficticias, funciones vacías presentadas como terminadas ni resultados de pruebas inventados.

Si encuentras una incompatibilidad técnica, debes investigarla, justificar la solución elegida e implementar la alternativa más adecuada.

---

# 1. EL ALMA DEL PROYECTO

## 1.1. ¿Qué es Jarvis?

Jarvis no será simplemente un programa que recibe comandos de voz.

Tampoco será un chatbot tradicional con acceso ocasional a algunas herramientas del computador.

**Jarvis será una extensión natural del sistema operativo: un asistente siempre disponible, capaz de comprender órdenes expresadas de forma cotidiana, utilizar el contexto y ejecutar acciones concretas de manera rápida y fiable.**

La idea es que el usuario pueda interactuar con su computador y con sus dispositivos conectados sin memorizar frases específicas ni abrir manualmente una aplicación.

El objetivo no es desarrollar una inteligencia artificial extremadamente avanzada.

Queremos desarrollar una inteligencia aplicada, eficiente y útil.

Jarvis debe dedicar sus recursos a tres tareas fundamentales:

1. Escuchar cuando sea necesario.
2. Comprender lo que el usuario realmente quiere.
3. Ejecutar correctamente la acción correspondiente.

Su capacidad de conversación será complementaria. Debe poder responder preguntas, mantener intercambios breves, recordar referencias y explicar situaciones, pero su principal propósito será actuar.

## 1.2. Filosofía de comportamiento

Jarvis debe cumplir los siguientes principios.

### Principio A: Siempre disponible, casi siempre dormido

Al encender el computador e iniciar sesión en Windows, Jarvis debe iniciarse automáticamente.

No debe abrir una consola ni mostrar una ventana principal.

Debe permanecer ejecutándose discretamente y mantener habilitado únicamente lo indispensable para detectar la palabra de activación.

Mientras nadie lo invoque, no debe realizar transcripciones continuas ni ejecutar inferencias de modelos de lenguaje.

Cuando el usuario diga «Jarvis», se activará y comenzará una sesión de interacción.

Cuando termine la conversación, volverá automáticamente a su estado de escucha pasiva.

### Principio B: Rapidez antes que complejidad

Una orden sencilla no debería requerir un modelo generativo.

Por ejemplo:

- «Jarvis, abre Chrome».
- «Sube el volumen».
- «Pausa la música».
- «Apaga la luz principal».

Cuando esas peticiones sean inequívocas y estén autorizadas, Jarvis deberá utilizar herramientas directas.

Reservaremos la inteligencia artificial generativa para interpretar frases complejas, resolver ambigüedades o conversar.

### Principio C: Lenguaje natural, no frases obligatorias

Jarvis no debe funcionar como un menú de comandos.

El usuario puede expresar una misma intención de muchas maneras.

Por ejemplo:

- «Baja el volumen».
- «Está muy fuerte».
- «Ponlo un poquito más bajo».
- «Bájale algo».
- «Se escucha demasiado duro».

Estas expresiones pueden representar una intención semejante cuando el contexto indica que se habla del sonido.

Pero Jarvis también deberá distinguir frases como «no bajes el volumen» o «cuando termine la canción, baja el volumen».

No debe ejecutar acciones únicamente porque reconoce palabras relacionadas con ellas.

### Principio D: Memoria práctica y contextual

Jarvis debe recordar cómo llama el usuario a sus dispositivos, aplicaciones, modos y preferencias.

Ejemplos:

- «La luz principal» puede significar la tira LED MrStar.
- «Modo jugar» puede representar una secuencia de iluminación, volumen y aplicaciones.
- «La música de siempre» puede significar una lista de reproducción configurada.
- «Ciérralo» puede referirse a la aplicación mencionada inmediatamente antes.

La memoria debe ser persistente cuando se trate de preferencias explícitas y temporal cuando se trate de referencias conversacionales.

### Principio E: Ejecutar únicamente lo autorizado

El modelo de lenguaje nunca tendrá acceso irrestricto a PowerShell, Python, el sistema de archivos o la ejecución de procesos.

Las acciones se realizarán a través de un catálogo de herramientas implementadas y autorizadas.

Las operaciones delicadas requerirán controles adicionales.

Jarvis no debe inventar capacidades ni afirmar que una acción se ejecutó si solamente se intentó.

### Principio F: Integración invisible

La interacción principal será por voz.

La interfaz gráfica existirá para representar los estados de Jarvis, mostrar diagnósticos y modificar configuraciones.

No deberá ser necesaria para utilizar el asistente normalmente.

### Principio G: Ligereza real

El funcionamiento en segundo plano debe ser apropiado para un computador que también se utiliza para jugar.

No se deben mantener modelos grandes en GPU mientras no son necesarios.

Se debe evitar cualquier procesamiento continuo que no tenga una justificación funcional.

### Principio H: Modularidad y evolución

Cada tecnología debe ser sustituible.

Si aparece un modelo de voz mejor que Moonshine, debe ser posible sustituirlo sin modificar la gestión de Windows.

Si cambia el modelo de lenguaje, no deben romperse las herramientas.

Si se integra una nueva luz, no debe ser necesario modificar el motor de conversación.

---

# 2. HARDWARE Y ENTORNO OBJETIVO

El computador principal dispone de:

- Sistema operativo: Windows, versión exacta pendiente de detección.
- Procesador: AMD Ryzen 9, serie 4000; verificar modelo exacto.
- Tarjeta gráfica: NVIDIA GTX 1660 Ti.
- VRAM: 6 GB.
- RAM: 16 GB.
- Idioma principal de interacción: español.
- Uso previsto: productividad, multimedia, videojuegos y control de dispositivos inteligentes.

Debes detectar el entorno real antes de realizar optimizaciones específicas.

No asumas que una biblioteca dispone de aceleración CUDA compatible simplemente porque el equipo tiene una GPU NVIDIA.

## 2.1. Objetivos de rendimiento

Durante reposo:

- Priorizar la CPU.
- Evitar inferencias de IA generativa.
- Mantener la GPU libre de modelos de Jarvis.
- Reducir actividad de disco.
- Evitar consultas periódicas innecesarias.
- Evitar crecimiento sostenido de memoria.
- Mantener el proceso disponible durante periodos prolongados.

Como metas iniciales de ingeniería, no como garantías:

- Consumo promedio de CPU idealmente inferior al 2 % durante reposo estable, medido sobre la máquina completa y especificando la metodología.
- RAM preferentemente inferior a 200 MB para el núcleo de Fase 1, si las dependencias elegidas lo permiten.
- Sin utilización sostenida de GPU atribuible a Jarvis durante reposo.
- Activación perceptiblemente rápida después de detectar su nombre.
- Cero ciclos de procesamiento intensivo cuando no existe audio relevante.

Estos valores deben medirse. Si no se alcanzan, documenta la causa real y el coste de cada componente.

No sacrifiques estabilidad para cumplir artificialmente un número.

---

# 3. VISIÓN DE LA ARQUITECTURA COMPLETA

Aunque solo implementaremos la Fase 1, el sistema deberá estar preparado para esta arquitectura futura.

**Capa 1 — Sistema residente**

Gestiona inicio automático, bandeja de Windows, estado, configuración, recuperación y cierre ordenado.

**Capa 2 — Audio**

Gestiona el micrófono, detección de la palabra de activación, detección de actividad vocal, transcripción y síntesis de voz.

**Capa 3 — Comprensión**

Clasifica intenciones, reconoce frases equivalentes, resuelve referencias conversacionales y consulta un modelo local cuando sea necesario.

**Capa 4 — Memoria**

Gestiona estado contextual temporal, preferencias persistentes, nombres alternativos, modos y resultados de acciones.

**Capa 5 — Herramientas**

Ejecuta operaciones autorizadas sobre Windows, aplicaciones, música, luces y otros dispositivos.

**Capa 6 — Interfaz**

Muestra los estados de Jarvis, su actividad, configuración y diagnósticos sin controlar directamente el funcionamiento del motor.

El flujo conceptual será:

Micrófono → Wake Word → Sesión activa → Reconocimiento de voz → Interpretación contextual → Validación → Ejecución → Respuesta → Reposo.

El motor residente no dependerá de que la interfaz esté visible.

---

# 4. TECNOLOGÍAS PREVISTAS

Las tecnologías principales seleccionadas son:

- Python 3.11 como núcleo de orquestación.
- Rustpotter como primera opción para detectar «Jarvis».
- Moonshine Voice como candidato principal de transcripción local en español.
- Faster-whisper como alternativa de transcripción.
- Silero VAD para detectar actividad vocal cuando sea necesario.
- Qwen3.5 2B, mediante Ollama, como primer candidato de interpretación generativa.
- Qwen3 1.7B como alternativa ligera.
- Piper como primera opción de síntesis de voz.
- SQLite para memoria persistente.
- APIs nativas de Windows para el control del computador.
- Interfaces multimedia de Windows para reproducción.
- Home Assistant como integración opcional.
- PySide6 para la interfaz.
- Programador de tareas de Windows para inicio automático.

**Importante: estas son elecciones arquitectónicas iniciales, no una orden de instalarlo todo ahora.**

En Fase 1 no necesitamos Moonshine, Whisper, Ollama, Qwen, Piper, Home Assistant ni Spotify.

Instalar componentes prematuramente aumentaría las dependencias y dificultaría el diagnóstico.

También debes revisar compatibilidad, licencias y mantenimiento antes de incorporar cualquier biblioteca externa.

---

# 5. ALCANCE EXACTO DE LA FASE 1

## Nombre de la fase

**JARVIS CORE — Always-On Wake Engine**

## Objetivo

Crear una aplicación residente en Windows que:

1. Se inicie automáticamente después de que el usuario inicie sesión.
2. No muestre ventanas o consolas innecesarias.
3. Mantenga una única instancia activa.
4. Gestione correctamente el micrófono.
5. Detecte la palabra «Jarvis» de manera local.
6. Cambie a un estado activo al detectarla.
7. Emita una confirmación mínima configurable.
8. Regrese automáticamente al estado dormido.
9. Permita pausar, reanudar y cerrar Jarvis desde la bandeja.
10. Se recupere de errores habituales del micrófono y del detector.
11. Registre información de diagnóstico.
12. Mantenga un consumo bajo durante reposo.
13. Esté preparado para integrar posteriormente reconocimiento, conversación y acciones.

## Exclusiones expresas

En esta fase NO se implementarán:

- Conversaciones con Qwen.
- Reconocimiento completo de órdenes.
- Control de Spotify.
- Apertura o cierre de aplicaciones mediante voz.
- Control de luces.
- Creación de modos personales.
- Memoria conversacional avanzada.
- Generación de respuestas con TTS neuronal.
- Interfaz flotante animada definitiva.
- Automatización autónoma de Windows.

El resultado esperado es un **motor de activación funcional**, no un asistente completo.

No debes presentar como implementadas funciones que todavía pertenecen a fases posteriores.

---

# 6. MÁQUINA DE ESTADOS

Implementa una máquina de estados explícita.

Los estados iniciales serán:

**STARTING**

Jarvis está cargando configuración, comprobando la instancia, preparando los recursos y seleccionando el micrófono.

**DORMANT**

Jarvis está esperando la palabra de activación.

Es su estado normal.

El procesamiento continuo debe limitarse a la adquisición de audio y detección ligera de wake word.

**AWAKE**

Se ha detectado correctamente «Jarvis».

En Fase 1 este estado solamente demuestra la activación y mantiene abierta una ventana breve de interacción.

En fases futuras permitirá pasar al motor de transcripción.

**PAUSED**

El usuario ha desactivado temporalmente la escucha.

No deben ejecutarse inferencias de wake word ni conservarse una captura activa del micrófono salvo necesidad técnica justificada.

**DEGRADED**

Existe una condición recuperable: micrófono desconectado, dispositivo no disponible o motor de detección reiniciándose.

Jarvis debe intentar recuperarse sin bloquear el sistema.

**STOPPING**

Se está cerrando de manera ordenada.

Debe liberar los dispositivos de audio, procesos secundarios y recursos.

## 6.1. Transiciones permitidas

STARTING → DORMANT, si los requisitos se cumplen.

STARTING → DEGRADED, cuando no se dispone del dispositivo o detector.

DORMANT → AWAKE, exclusivamente por detección válida de wake word o activación manual de diagnóstico.

AWAKE → DORMANT, cuando finaliza el tiempo de sesión.

DORMANT/AWAKE → PAUSED, por solicitud del usuario.

PAUSED → DORMANT, al reanudar.

DORMANT/AWAKE → DEGRADED, ante errores recuperables.

DEGRADED → DORMANT, cuando la recuperación se completa.

Cualquier estado operativo → STOPPING, cuando se solicita cerrar Jarvis.

No deben existir transiciones arbitrarias fuera del controlador de estados.

## 6.2. Temporizador inicial

En Fase 1, configura una ventana activa inicial de 10 segundos después de detectar «Jarvis».

Este valor debe ser configurable.

Como todavía no existirá transcripción ni diálogo, el temporizador no representa una conversación real. Es solamente una demostración del ciclo de activación.

En una fase posterior, sustituiremos la expiración simple por una ventana de conversación que se prolongue cuando exista actividad del usuario, una respuesta en curso o una aclaración pendiente.

---

# 7. MOTOR DE ACTIVACIÓN — RUSTPOTTER

## 7.1. Requisito funcional

La palabra de activación principal será:

**Jarvis**

El usuario debe poder pronunciarla en español sin añadir obligatoriamente «Hey».

El motor no puede basarse en reconocer la palabra dentro de una transcripción completa, porque eso implicaría mantener un motor STT procesando permanentemente.

Se requiere detección acústica específica de wake word.

## 7.2. Integración técnica

Rustpotter es una biblioteca desarrollada en Rust.

No asumas que existe un paquete oficial Python completamente compatible con la versión elegida.

Investiga e implementa una integración técnicamente verificable.

La arquitectura preferida es:

**Python Core ↔ Adaptador Wake Word ↔ Motor Rustpotter**

Si no existe una vinculación Python adecuada y mantenida, crea un pequeño proceso auxiliar escrito en Rust.

El núcleo Python deberá controlar su ciclo de vida.

No quiero dos componentes independientes abriendo el mismo micrófono simultáneamente.

El sistema Python administrará la fuente de audio y enviará fragmentos al detector mediante una interfaz definida.

Para un proceso auxiliar, puedes utilizar un protocolo local sobre stdin/stdout con audio PCM binario hacia el detector y eventos estructurados de regreso.

Mantén los mensajes de diagnóstico separados del flujo binario.

Debes definir:

- Formato y frecuencia de las muestras.
- Tamaño de bloques.
- Fronteras de cada mensaje.
- Manejo de lectura parcial.
- Control de presión cuando el consumidor sea lento.
- Comunicación de errores.
- Reinicio del proceso auxiliar.
- Identificación de versiones.
- Cierre ordenado.

Evita convertir el transporte de audio en una sucesión de mensajes JSON innecesariamente grandes.

No utilices sockets de red ni servicios externos si un mecanismo local es suficiente.

El proyecto Rust debe compilarse de manera reproducible para Windows.

## 7.3. Parámetros de audio

Rustpotter trabaja internamente con audio mono a 16 kHz.

Adapta la entrada del micrófono al formato exacto que requiere el detector.

No asumas que todos los micrófonos utilizan 16 kHz.

Muchos dispositivos funcionan a 44,1 o 48 kHz.

La conversión debe preservar una calidad suficiente para detectar la palabra y evitar un consumo excesivo de CPU.

La adquisición y conversión de audio deben estar desacopladas de las operaciones lentas.

## 7.4. Personalización de «Jarvis»

Prepara un procedimiento de configuración mediante el cual el usuario pueda grabar varias muestras de la palabra de activación.

Para el primer prototipo, contempla entre cinco y ocho grabaciones.

Las grabaciones se utilizarán para generar una referencia local de Rustpotter.

Debe existir un procedimiento claro para repetir la calibración, sustituir la referencia y probar la sensibilidad.

La calibración debe hacerse mediante una acción explícita del usuario.

No guardes grabaciones de voz permanentemente sin necesidad o consentimiento.

Documenta que un detector basado en referencias puede ser menos preciso que uno entrenado con un conjunto suficientemente grande de ejemplos.

## 7.5. Falsos positivos y falsos negativos

El sistema debe permitir configurar umbrales de detección y un periodo de enfriamiento posterior a la activación.

No debe entrar en ciclos de activación repetidos por un único sonido.

Debemos medir:

- Activaciones correctas.
- Activaciones perdidas.
- Falsas activaciones.
- Latencia de detección.
- Comportamiento a distintas distancias.
- Activación con ruido ambiental.
- Activación con música o videojuegos.

Ningún umbral debe considerarse correcto sin pruebas.

## 7.6. Alternativa de respaldo

Si Rustpotter presenta problemas relevantes de estabilidad, integración, mantenimiento o precisión, deja preparado un adaptador para sustituirlo por openWakeWord u otro motor local.

No implementes los dos motores completos desde el primer día si no hace falta.

El núcleo de Jarvis debe depender de una interfaz `WakeWordDetector`, no directamente de una biblioteca concreta.

---

# 8. ADMINISTRACIÓN DEL MICRÓFONO

Esta parte es crítica.

## 8.1. Una sola fuente de captura

Implementa un componente responsable de administrar la adquisición de audio.

El resto del sistema debe consumir sus bloques mediante interfaces controladas.

Evita que múltiples módulos compitan por abrir el dispositivo.

## 8.2. Selección del dispositivo

Durante el primer inicio:

- Detecta los micrófonos disponibles.
- Identifica el dispositivo predeterminado de comunicaciones o captura, según la política elegida.
- Permite seleccionar un dispositivo específico.
- Guarda la preferencia.

Debe soportar dos modos:

**Automático:** seguir el dispositivo predeterminado de Windows cuando cambie.

**Fijo:** utilizar un dispositivo elegido mientras esté disponible, con política explícita de recuperación.

## 8.3. Reconexión

Contempla los siguientes eventos:

- Desconexión de auriculares.
- Conexión de un micrófono USB.
- Cambio del dispositivo predeterminado.
- Deshabilitación del micrófono.
- Suspensión y reanudación del computador.
- Error de permisos.
- Fallo del controlador de audio.
- Cambio de frecuencia o formato del dispositivo.

Si ocurre un error recuperable, Jarvis debe entrar en estado DEGRADED y recuperar la entrada cuando sea posible.

No debe generar cientos de mensajes de error por segundo.

Utiliza reintentos con retroceso progresivo y un límite razonable.

No hagas bucles intensivos de reconexión.

## 8.4. Procesamiento no bloqueante

El callback de captura de audio debe hacer lo mínimo necesario.

No debe:

- Ejecutar operaciones de disco.
- Realizar inferencias pesadas.
- Esperar al modelo.
- Bloquearse esperando otro proceso.
- Ejecutar tareas de interfaz.
- Esperar un lock durante periodos prolongados.

Utiliza una cola limitada o un búfer circular.

Si el consumidor se retrasa, registra la pérdida de muestras de forma controlada y evita crecimiento ilimitado de memoria.

## 8.5. Búfer previo a la activación

Aunque en Fase 1 no habrá STT, crea la infraestructura de un búfer circular de audio reciente.

Configura inicialmente una retención aproximada de 1,5 segundos, ajustable según las pruebas.

En fases futuras este búfer ayudará a evitar que se pierda la primera parte de órdenes como:

«Jarvis, abre Spotify».

El búfer debe tener tamaño fijo y permanecer en memoria.

No debe grabar continuamente archivos en disco.

Todavía no es necesario implementar el envío del búfer al transcriptor, pero sí una interfaz preparada para esa operación.

---

# 9. EJECUCIÓN EN SEGUNDO PLANO

## 9.1. Comportamiento esperado

Al iniciar sesión en Windows, Jarvis debe ejecutarse automáticamente.

No debe aparecer:

- Consola de Python.
- Ventana de PowerShell.
- Pantalla de carga innecesaria.
- Interfaz principal.
- Diálogo modal sin motivo.

Se permitirá un icono discreto en la bandeja del sistema.

Jarvis debe seguir ejecutándose aunque el usuario no abra ninguna ventana.

## 9.2. Inicio automático

Utiliza preferentemente el Programador de tareas de Windows con un desencadenador al iniciar sesión en la cuenta del usuario.

No utilices un servicio de Windows de sesión 0 para controlar directamente el escritorio interactivo.

Crea scripts o comandos de instalación y desinstalación del inicio automático.

Estos deben:

- Registrar la tarea para el usuario apropiado.
- Utilizar rutas absolutas.
- Establecer el directorio de trabajo correcto.
- Evitar ventanas de consola visibles.
- No requerir privilegios de administrador si no son necesarios.
- Evitar registros duplicados.
- Permitir desactivar el inicio automático.
- Informar errores de configuración.
- Respetar los permisos del usuario.

El instalador debe explicar qué cambios realizará.

No modifiques configuraciones globales de Windows sin justificación.

## 9.3. Una sola instancia

Utiliza un mecanismo fiable de instancia única en Windows, preferentemente un mutex con nombre de ámbito local al usuario.

Si Jarvis ya está ejecutándose, un segundo inicio no debe crear otra captura de micrófono ni otro proceso completo.

Puede limitarse a informar del estado existente o abrir un panel de diagnóstico cuando sea solicitado.

No permitas que dos instancias compitan por el micrófono.

## 9.4. Bandeja del sistema

Implementa un icono de bandeja con PySide6 y `QSystemTrayIcon`, siempre que las pruebas de consumo justifiquen su uso.

En esta primera fase, el menú debe contener:

- Estado actual de Jarvis.
- Pausar escucha.
- Reanudar escucha.
- Probar activación manual.
- Abrir diagnósticos.
- Abrir ubicación de registros.
- Salir completamente.

Si PySide6 introduce una sobrecarga innecesaria en reposo, documenta la medición antes de considerar otra implementación.

No desarrolles todavía una interfaz gráfica compleja.

## 9.5. Cierre real

Seleccionar «Salir» debe finalizar completamente Jarvis.

Debe cerrar:

- Captura de audio.
- Motor wake word.
- Procesos auxiliares.
- Hilos y tareas asíncronas.
- Recursos de interfaz.
- Recursos de registro.

No deben permanecer procesos huérfanos ni un micrófono retenido.

---

# 10. CONTROL DEL CICLO DE VIDA

Crea un componente central `LifecycleManager`.

Será responsable de:

- Iniciar servicios.
- Determinar dependencias.
- Ordenar el cierre.
- Supervisar fallos.
- Ejecutar reinicios recuperables.
- Publicar transiciones de estado.
- Gestionar suspensión y reanudación.
- Evitar inicializaciones duplicadas.

## 10.1. Supervisión de procesos

Si el detector Rust se ejecuta como proceso auxiliar, debe estar supervisado.

Si termina inesperadamente:

1. Registrar el fallo.
2. Liberar recursos asociados.
3. Entrar en estado DEGRADED.
4. Esperar un intervalo de recuperación.
5. Reiniciar de forma controlada.
6. Restaurar el estado DORMANT cuando vuelva a estar operativo.

Evita reinicios infinitos de alta frecuencia.

Después de varios fallos consecutivos, mantén Jarvis en un estado de error visible desde la bandeja, con reintento manual disponible.

## 10.2. Fallos de componentes

El programa no debe cerrarse completamente por una excepción ordinaria del detector o del micrófono.

Pero tampoco debe ocultar errores graves y fingir que está funcionando.

Distingue entre:

- Recuperación completada.
- Error recuperable.
- Error persistente.
- Error fatal.

## 10.3. Reanudación tras suspensión

Cuando Windows vuelve de suspensión:

- Verifica si la captura sigue siendo válida.
- Revisa los dispositivos disponibles.
- Reinicia el flujo de audio si es necesario.
- Restablece el detector.
- Descarta bloques de audio obsoletos.
- Regresa a DORMANT cuando esté preparado.

No debe interpretar audio atrasado como una activación nueva.

---

# 11. EVENTOS Y DESACOPLAMIENTO

Implementa un mecanismo interno de eventos tipados.

Ejemplos:

- `SYSTEM_STARTED`
- `AUDIO_READY`
- `MICROPHONE_DISCONNECTED`
- `MICROPHONE_RECOVERED`
- `WAKEWORD_DETECTED`
- `SESSION_STARTED`
- `SESSION_TIMEOUT`
- `SYSTEM_PAUSED`
- `SYSTEM_RESUMED`
- `DETECTOR_FAILED`
- `SYSTEM_STOPPING`

Los eventos deben permitir que varios componentes observen la actividad sin depender directamente unos de otros.

No construyas un sistema de mensajería excesivamente complejo.

Para Fase 1, una implementación local y ligera es suficiente.

Evita eventos duplicados que produzcan transiciones repetidas.

Utiliza identificadores de sesión para distinguir activaciones y descartar resultados antiguos en el futuro.

La interfaz deberá observar el estado mediante eventos; no controlará directamente el detector.

---

# 12. CONFIGURACIÓN

Crea un sistema de configuración persistente, validado y versionado.

Utiliza los directorios apropiados del perfil de usuario de Windows.

No escribas datos modificables dentro de carpetas protegidas del sistema.

Una organización adecuada sería:

- Configuración del usuario.
- Referencias de wake word.
- Registros.
- Diagnósticos.
- Estado temporal.
- Recursos instalados.

No almacenes claves, tokens o datos sensibles en archivos públicos.

## 12.1. Parámetros configurables iniciales

Debemos poder modificar:

- Activar o desactivar escucha.
- Dispositivo de audio.
- Política de seguimiento del micrófono predeterminado.
- Referencia de wake word.
- Umbral del detector.
- Periodo de enfriamiento.
- Tiempo activo.
- Activar o desactivar señal de confirmación.
- Nivel de registro.
- Inicio automático.
- Política de reconexión.
- Tamaño del búfer de audio.

Cada parámetro debe tener:

- Tipo definido.
- Valor predeterminado.
- Rango aceptado.
- Validación.
- Descripción.
- Comportamiento en caso de configuración inválida.

No permitas que un archivo de configuración corrupto bloquee permanentemente el inicio sin proporcionar una forma de reparación.

Conserva una copia de recuperación cuando resulte útil.

---

# 13. PRIVACIDAD Y SEGURIDAD

La privacidad local es un requisito fundamental.

En reposo:

- El audio se procesa localmente.
- No se envía a servidores externos.
- No se guarda audio continuamente en disco.
- No se realiza transcripción.
- No se ejecutan herramientas del sistema.
- No se utiliza un LLM.

Las grabaciones para calibrar la palabra de activación serán opcionales y controladas por el usuario.

Los diagnósticos no deben contener audio grabado salvo autorización explícita.

## 13.1. Detener la escucha

El usuario debe disponer de una opción visible para pausar completamente la escucha.

Cuando se pausa, Jarvis debe liberar o detener la captura según corresponda.

Debe poder reanudarse desde la bandeja.

No debe dar una apariencia de privacidad que no corresponda a su funcionamiento real.

## 13.2. Autenticación

Reconocer la palabra «Jarvis» no equivale a reconocer quién está hablando.

La Fase 1 no implementará autenticación biométrica del hablante.

Documenta esta limitación.

En fases futuras, las operaciones sensibles tendrán confirmaciones adicionales y no dependerán únicamente de que alguien haya pronunciado «Jarvis».

---

# 14. CONFIRMACIÓN DE ACTIVACIÓN

Durante Fase 1, Jarvis no tendrá TTS neuronal.

Por eso utiliza una señal corta de confirmación configurable.

Puede ser un sonido breve, discreto y no invasivo.

Debe indicar que la activación fue reconocida.

No debe utilizar sonidos demasiado fuertes, frecuentes o prolongados.

La confirmación debe poder desactivarse.

También debe reflejarse la transición mediante el icono de bandeja o un indicador de diagnóstico.

No quiero que Codex instale un modelo TTS solo para pronunciar «Dime» durante esta fase.

La respuesta hablada completa se añadirá posteriormente.

---

# 15. DIAGNÓSTICOS Y OBSERVABILIDAD

Este proyecto debe ser fácil de depurar.

Quiero poder distinguir rápidamente si una falla proviene de:

1. El micrófono.
2. La captura.
3. La conversión de audio.
4. El detector.
5. La máquina de estados.
6. El gestor del ciclo de vida.

Implementa registros estructurados con marcas de tiempo y niveles.

## 15.1. Eventos a registrar

- Inicio de Jarvis.
- Versión de la aplicación.
- Dispositivo de audio seleccionado.
- Formato efectivo de audio.
- Detector cargado.
- Activación detectada.
- Puntuación del detector cuando esté disponible.
- Transiciones de estado.
- Errores de captura.
- Reconexiones.
- Reinicios del detector.
- Inicio y finalización de sesión.
- Pausa y reanudación.
- Cierre normal.
- Errores inesperados.

Evita registrar contenido de audio.

## 15.2. Métricas

Prepara mediciones de:

- Tiempo de inicialización.
- Latencia de detección en pruebas con audio de referencia.
- CPU promedio y máximo.
- Memoria residente.
- Número de activaciones.
- Número de reinicios.
- Número de desconexiones de micrófono.
- Bloques de audio perdidos.
- Longitud máxima de la cola.
- Tiempo acumulado en cada estado.

La medición de CPU debe documentar su interpretación y normalización para equipos multinúcleo.

La ausencia de datos debe mostrarse como tal, no reemplazarse por cero cuando sea engañoso.

No es necesario crear todavía un panel de monitorización sofisticado.

Un reporte JSON o textual reproducible será suficiente.

---

# 16. ESTRUCTURA DEL PROYECTO

Propongo crear inicialmente esta estructura.

```text
jarvis/
│
├── README.md
├── pyproject.toml
├── .gitignore
│
├── docs/
│   ├── vision.md
│   ├── architecture.md
│   ├── phase_1.md
│   ├── installation.md
│   ├── troubleshooting.md
│   └── future_roadmap.md
│
├── config/
│   └── defaults.toml
│
├── jarvis/
│   ├── __init__.py
│   ├── __main__.py
│   │
│   ├── core/
│   │   ├── lifecycle.py
│   │   ├── state_machine.py
│   │   ├── events.py
│   │   ├── config.py
│   │   ├── single_instance.py
│   │   └── logging.py
│   │
│   ├── audio/
│   │   ├── capture.py
│   │   ├── devices.py
│   │   ├── ring_buffer.py
│   │   ├── converter.py
│   │   └── wakeword_interface.py
│   │
│   ├── wakeword/
│   │   ├── rustpotter_adapter.py
│   │   ├── detector_supervisor.py
│   │   └── calibration.py
│   │
│   ├── interface/
│   │   ├── tray.py
│   │   └── diagnostics.py
│   │
│   └── system/
│       ├── windows_events.py
│       └── startup.py
│
├── rust/
│   └── wakeword_engine/
│       ├── Cargo.toml
│       └── src/
│           └── main.rs
│
├── scripts/
│   ├── install_startup.ps1
│   ├── uninstall_startup.ps1
│   └── run_diagnostics.ps1
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── audio/
│   └── performance/
│
└── assets/
    └── icons/
```

Puedes ajustar esta estructura si encuentras una razón técnica sólida.

No crees cientos de archivos vacíos simplemente para aparentar una arquitectura completa.

Los componentes de futuras fases deben quedar documentados, no necesariamente implementados.

---

# 17. REQUISITOS DE CALIDAD DEL CÓDIGO

El código debe ser mantenible, comprensible y fácil de ampliar.

Requisitos:

- Tipado explícito donde aporte claridad.
- Interfaces pequeñas.
- Separación de responsabilidades.
- Dependencias controladas.
- Gestión correcta de excepciones.
- Liberación determinista de recursos.
- Operaciones de audio no bloqueantes.
- Hilos y procesos con cierre supervisado.
- Configuración centralizada.
- Ausencia de rutas absolutas del desarrollador.
- Compatibilidad con espacios y caracteres especiales en rutas de Windows.
- Logs útiles, sin exceso.
- Pruebas automáticas.
- Documentación de instalación.
- Dependencias con versiones reproducibles.

Evita abstracciones innecesarias, frameworks pesados y patrones que compliquen el mantenimiento sin aportar beneficios reales.

La elegancia arquitectónica consiste en resolver bien el problema, no en tener la mayor cantidad de capas posibles.

## 17.1. Dependencias

Utiliza un entorno virtual independiente.

Define las dependencias principales y de desarrollo.

Comprueba compatibilidad real con Windows.

Si necesitas Rust, documenta cómo instalar la herramienta de compilación y cómo generar el ejecutable.

No asumas que `cargo`, un compilador de C++ o una versión determinada de CUDA ya están instalados.

Si falta un requisito externo, informa cuál es y cómo instalarlo.

No simules una compilación satisfactoria cuando no se haya producido.

## 17.2. Ejecución y depuración

Proporciona un modo de ejecución de desarrollo, con registros visibles, separado del modo residente sin consola.

Por ejemplo, define comandos equivalentes a:

```text
python -m jarvis --debug
python -m jarvis --diagnostics
python -m jarvis --calibrate-wakeword
```

La sintaxis exacta debe quedar implementada y documentada.

Debe ser posible ejecutar las pruebas sin tener que registrar primero Jarvis en el inicio automático de Windows.

---

# 18. PRUEBAS AUTOMÁTICAS

No consideres terminada la Fase 1 solo porque Jarvis muestra un icono en la bandeja.

Debemos verificar el funcionamiento completo.

## 18.1. Pruebas de máquina de estados

Comprobar:

- Inicio correcto.
- Activación válida.
- Retorno a reposo.
- Pausa.
- Reanudación.
- Cierre.
- Recuperación desde DEGRADED.
- Rechazo de transiciones inválidas.
- Cancelación de temporizadores anteriores.
- Ignorar eventos obsoletos.

## 18.2. Pruebas de audio

Comprobar:

- Inicialización de captura.
- Conversión entre frecuencias.
- Audio mono.
- Formato PCM correcto.
- Búfer circular.
- Límites de memoria.
- Desbordamiento de colas.
- Desconexión simulada.
- Recuperación de micrófono.
- Cierre de captura.

## 18.3. Pruebas del detector

Utiliza grabaciones controladas de prueba.

Comprobar:

- Audio con wake word.
- Audio sin wake word.
- Silencio.
- Ruido.
- Palabras semejantes.
- Repeticiones.
- Detección durante funcionamiento prolongado.
- Fallo del proceso auxiliar.
- Reinicio del detector.

No utilices grabaciones generadas artificialmente como única evidencia de precisión real.

## 18.4. Pruebas de Windows

Comprobar:

- Inicio manual.
- Segunda instancia.
- Cierre desde la bandeja.
- Ausencia de consola en modo residente.
- Scripts de inicio automático.
- Desinstalación del inicio.
- Rutas con espacios.
- Recuperación tras suspensión.

## 18.5. Pruebas sin hardware

Las pruebas unitarias deben poder utilizar un micrófono simulado y un detector simulado.

La lógica de estados debe poder comprobarse sin tener un micrófono conectado.

Sin embargo, superar estas pruebas no demuestra que la detección acústica real funcione.

Mantén separadas las pruebas simuladas y las pruebas físicas.

---

# 19. PRUEBA REAL DE ACEPTACIÓN

Una vez implementado el núcleo, quiero realizar esta prueba completa.

## Escenario 1 — Primer arranque

1. Ejecutar Jarvis manualmente.
2. Comprobar que carga la configuración.
3. Comprobar el estado del micrófono.
4. Comprobar que el detector está disponible.
5. Confirmar que queda en DORMANT.
6. Verificar que no aparece una consola no deseada.

## Escenario 2 — Primera activación

1. Decir «Jarvis».
2. Comprobar que el detector identifica la palabra.
3. Emitir confirmación breve.
4. Cambiar a AWAKE.
5. Esperar el temporizador de la sesión.
6. Regresar automáticamente a DORMANT.

## Escenario 3 — Inactividad

Mantener Jarvis sin interacción durante un periodo prolongado.

Verificar:

- CPU estable.
- Memoria estable.
- Ausencia de inferencias generativas.
- Sin creación continua de archivos de audio.
- Sin procesos auxiliares duplicados.
- Detector disponible al finalizar la prueba.

## Escenario 4 — Micrófono

Desconectar y conectar el dispositivo de entrada.

Verificar que Jarvis detecta la pérdida, informa el estado y recupera la captura cuando sea posible.

## Escenario 5 — Reinicio de Windows

Instalar explícitamente el inicio automático.

Cerrar sesión o reiniciar Windows.

Iniciar sesión nuevamente.

Comprobar que Jarvis aparece en la bandeja y queda preparado para detectar su palabra.

## Escenario 6 — Uso durante videojuegos

Mantener Jarvis en reposo mientras se ejecuta un videojuego.

Observar CPU, RAM, GPU, latencias y posibles problemas de audio.

No se debe afirmar que no afecta a los FPS sin realizar una comparación real.

## Escenario 7 — Suspensión

Suspender Windows.

Reanudar el equipo.

Confirmar que Jarvis restaura el funcionamiento del micrófono y del detector.

## Escenario 8 — Salida completa

Cerrar Jarvis desde la bandeja.

Verificar que no quedan procesos asociados, que se libera el micrófono y que no existe una instancia residual.

---

# 20. CRITERIOS PARA DECLARAR TERMINADA LA FASE 1

La Fase 1 podrá considerarse técnicamente terminada cuando:

- Existe una aplicación ejecutable en Windows.
- Tiene un núcleo modular.
- Puede iniciar sin mostrar una consola.
- Se mantiene residente.
- Dispone de un icono de bandeja funcional.
- Detecta realmente «Jarvis» mediante un motor local.
- Permite calibrar la palabra de activación.
- Administra correctamente el micrófono.
- Dispone de máquina de estados comprobable.
- Regresa automáticamente al reposo.
- Soporta pausa y reanudación.
- Evita instancias duplicadas.
- Tiene un mecanismo de inicio automático verificable.
- Libera recursos al cerrar.
- Gestiona errores recuperables.
- Genera diagnósticos útiles.
- Tiene pruebas automáticas.
- Incluye documentación completa.
- Se ha realizado una evaluación de rendimiento.

Si algunas pruebas físicas no pueden ejecutarse en el entorno de Codex, deben quedar claramente identificadas como pendientes de validación en mi computador.

No declares que una prueba de micrófono, reinicio de Windows o consumo de GPU ha sido superada si no se ha ejecutado realmente.

---

# 21. HOJA DE RUTA POSTERIOR

La arquitectura debe contemplar las siguientes fases sin implementarlas todavía.

## Fase 2 — Conversación por voz

Integración de reconocimiento en español, detección de final de turno, TTS local y una ventana de conversación donde no sea necesario repetir «Jarvis».

Se evaluarán Moonshine Voice y faster-whisper.

Se incorporará una voz breve, natural y cancelable.

## Fase 3 — Comprensión inteligente

Router híbrido de intenciones.

Comandos directos, coincidencia semántica, memoria contextual y Qwen mediante Ollama.

El modelo interpretará solicitudes complejas, pero no tendrá permiso directo para ejecutar código arbitrario.

Se probarán negaciones, condiciones futuras, correcciones y referencias.

## Fase 4 — Herramientas reales

Control de:

- Aplicaciones.
- Ventanas.
- Volumen del sistema.
- Reproducción multimedia.
- Spotify cuando las integraciones disponibles lo permitan.
- Iluminación.
- Funciones autorizadas de Windows.

Cada herramienta tendrá validación, permisos y resultados verificables.

## Fase 5 — Memoria y personalización

SQLite para preferencias, alias, dispositivos, escenas y rutinas.

Aprendizaje mediante frases naturales.

Ejemplo:

«Jarvis, recuerda que cuando diga luz de escritorio me refiero a la tira MrStar».

Otro ejemplo:

«Jarvis, crea un modo película: luces moradas al 20 %, volumen en 25 y abre Netflix».

## Fase 6 — Experiencia final

Interfaz minimalista flotante.

Animaciones de escucha, procesamiento y habla.

Ejecución invisible en segundo plano.

Perfil Gaming, gestión dinámica de modelos y optimización de CPU/GPU.

Instalador y configuración simplificados.

Pruebas prolongadas de estabilidad.

---

# 22. VISIÓN DE EXPERIENCIA DEL USUARIO

Cuando todo el proyecto esté terminado, espero esta experiencia:

Enciendo el computador.

Windows inicia sesión.

Jarvis se ejecuta automáticamente, sin mostrar su interfaz.

Sigo utilizando el equipo normalmente.

Puedo abrir programas, estudiar, escuchar música o jugar.

Jarvis permanece dormido, con un detector ligero prestando atención únicamente a su palabra de activación.

Digo:

«Jarvis».

El asistente responde brevemente o emite una señal de activación.

Digo:

«Voy a jugar, abre Steam y pon las luces como siempre».

Jarvis interpreta que quiero abrir Steam y ejecutar el modo de iluminación que previamente configuré.

Mientras la conversación siga activa, puedo decir:

«Pero hoy prefiero las luces rojas».

Jarvis comprende que estoy modificando el color de las luces, no el modo completo.

Después digo:

«Y baja un poco la música».

Interpreta la referencia contextual y ajusta el volumen correspondiente.

Cuando dejo de hablar, espera un breve periodo y vuelve a su estado dormido.

Durante todo el proceso no tuve que utilizar el teclado, abrir la interfaz, memorizar un comando exacto ni repetir constantemente el nombre de Jarvis.

Esta es la experiencia que debe orientar todas las decisiones técnicas.

---

# 23. REGLAS DE TRABAJO PARA CODEX

Debes trabajar de manera incremental y verificable.

Antes de empezar:

1. Inspecciona el directorio de trabajo.
2. Verifica las herramientas instaladas.
3. Identifica las limitaciones del entorno.
4. Establece las dependencias necesarias para la Fase 1.
5. Define un plan breve de implementación.
6. Comienza a construir el proyecto real.

Si existe un proyecto Jarvis anterior en otra carpeta, no lo sobrescribas ni lo utilices automáticamente como nueva base.

El nuevo proyecto deberá tener su propio directorio y su propio entorno virtual.

Puedes consultar código anterior para recuperar conocimientos técnicos, pero no trasladar funcionalidades sin pruebas.

Durante el desarrollo:

- Implementa componentes reales.
- Ejecuta pruebas después de cada bloque significativo.
- Corrige errores detectados.
- Conserva el proyecto ejecutable.
- No añadas funciones futuras por iniciativa propia.
- No sacrifiques el rendimiento por comodidad de implementación.
- No ocultes fallos.
- No inventes resultados.

Si una dependencia resulta problemática:

- Identifica el problema.
- Comprueba si existe una solución razonable.
- Evalúa el coste de la solución.
- Utiliza una alternativa compatible si está justificado.
- Documenta cualquier desviación del diseño.

No quiero que detengas todo el desarrollo por una decisión menor que puedas resolver técnicamente.

Si necesitas información imposible de determinar desde el entorno, deja una configuración segura y explícita para completarla durante la validación real.

---

# 24. ENTREGABLES OBLIGATORIOS

Al finalizar la implementación inicial deberás proporcionar:

**1. Código fuente completo de Fase 1.**

Todos los componentes necesarios para ejecutar el motor residente.

**2. Instrucciones de instalación.**

Comandos reales, dependencias, compilación de Rust si corresponde y configuración de Python.

**3. Procedimiento de calibración.**

Instrucciones para registrar mi voz y configurar la palabra «Jarvis».

**4. Inicio automático.**

Scripts de instalación y eliminación de la tarea de Windows.

**5. Guía de uso.**

Cómo iniciar, pausar, reanudar, ver diagnósticos y cerrar Jarvis.

**6. Pruebas automatizadas.**

Con resultados reales de las pruebas que hayas ejecutado.

**7. Diagnóstico de rendimiento.**

Mediciones disponibles de CPU, RAM, estado de procesos y estabilidad.

**8. Limitaciones conocidas.**

Aspectos que no hayan podido verificarse, incompatibilidades, riesgos o errores pendientes.

**9. Informe de arquitectura.**

Qué componentes implementaste, cómo se comunican y cómo se incorporarán las siguientes fases.

**10. Registro de cambios y decisiones.**

Documenta decisiones importantes para evitar que en las próximas sesiones de Codex se pierda el contexto del proyecto.

---

# 25. INSTRUCCIÓN DE EJECUCIÓN INMEDIATA

Ahora comienza el desarrollo real.

Tu tarea inmediata es implementar **JARVIS FASE 1 — ALWAYS-ON CORE**.

Orden de trabajo:

### Paso 1
Crear el proyecto nuevo, el entorno Python, los archivos de configuración y la estructura inicial.

### Paso 2
Implementar la máquina de estados, el administrador del ciclo de vida y el sistema de eventos.

### Paso 3
Implementar la administración del micrófono, selección de dispositivos, captura de audio y búfer circular.

### Paso 4
Integrar Rustpotter mediante una solución compatible y verificable con Windows.

### Paso 5
Crear el procedimiento para generar y cargar una referencia de activación «Jarvis».

### Paso 6
Conectar los eventos de wake word a la máquina de estados y comprobar el retorno a reposo.

### Paso 7
Implementar bandeja del sistema, pausa, reanudación, activación de diagnóstico y cierre ordenado.

### Paso 8
Implementar prevención de múltiples instancias, tratamiento de errores y recuperación de dispositivos.

### Paso 9
Crear y verificar los scripts de inicio automático con Windows.

### Paso 10
Ejecutar pruebas automatizadas, producir el informe de rendimiento disponible y documentar las comprobaciones físicas pendientes.

**No pases a la Fase 2 automáticamente.**

La primera fase debe quedar terminada, probada y documentada antes de continuar.

---

# 26. PRINCIPIO FINAL DEL PROYECTO

Quiero que cada decisión de ingeniería responda a esta pregunta:

**¿Esta implementación hace que Jarvis sea más rápido, natural, fiable, ligero y fácil de utilizar?**

Si una biblioteca añade complejidad sin mejorar estos atributos, no debería utilizarse.

Si un modelo grande responde mejor pero ralentiza las acciones cotidianas, no debería ser el encargado de todas las solicitudes.

Si una función consume recursos continuamente y solo se utiliza ocasionalmente, debe activarse bajo demanda.

Si una acción puede ejecutarse mediante una herramienta fiable de Windows, no necesitamos que una inteligencia artificial manipule visualmente el escritorio.

Si un componente falla, Jarvis debe poder recuperarse sin comprometer todo el sistema.

Y si existe incertidumbre sobre lo que el usuario quiere, es preferible solicitar una aclaración breve antes que ejecutar algo equivocado.

**Jarvis debe ser inteligente por su comportamiento, no por la cantidad de recursos que consume.**

No estamos construyendo una demostración de inteligencia artificial.

Estamos construyendo un asistente personal que deberá funcionar todos los días, durante años, como una parte natural del computador.

Ese es el estándar de calidad que debe guiar todo el desarrollo.

**Comienza ahora con la Fase 1. Construye código funcional, verifica lo que puedas comprobar realmente y entrega un resultado ejecutable, no solo una explicación del diseño.**