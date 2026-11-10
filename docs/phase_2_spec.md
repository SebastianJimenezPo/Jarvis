# PROYECTO JARVIS
## DOCUMENTO MAESTRO DE DESARROLLO — FASE 2
### Motor de escucha, reconocimiento de voz, síntesis de voz y gestión de conversaciones
**Versión 2.0 — Continuación del proyecto existente**

---

# 0. INSTRUCCIÓN PRINCIPAL PARA CODEX

Actúa como arquitecto de software especializado en asistentes de voz locales, procesamiento de audio en tiempo real, aplicaciones residentes de Windows y optimización de modelos de inteligencia artificial.

Vamos a desarrollar la **Fase 2 de JARVIS**, continuando el proyecto cuya Fase 1 ya fue implementada y validada.

Tu objetivo es transformar un sistema que actualmente detecta su nombre y entra en un estado activo durante diez segundos en un sistema capaz de:

1. Detectar «Jarvis» mediante el motor Rustpotter existente.
2. Comenzar a escuchar inmediatamente al usuario.
3. Reconocer frases completas en español.
4. Convertir esas frases en texto.
5. Identificar cuándo comienza y termina una intervención.
6. Producir respuestas habladas mediante síntesis de voz local.
7. Mantener una sesión con varios intercambios sin exigir repetir «Jarvis».
8. Volver automáticamente a su estado de reposo cuando termina la interacción.
9. Evitar interpretar su propia voz como una nueva intervención del usuario.
10. Mantener un consumo reducido de CPU, RAM y GPU, especialmente mientras el usuario juega.

**No debes reconstruir la Fase 1. Debes utilizarla como fundamento y preservar sus funcionalidades y pruebas.**

En esta fase todavía no implementaremos interpretación avanzada de intenciones, control de aplicaciones, automatización de Windows, Spotify, luces, memoria conversacional inteligente ni modelos de lenguaje generativos.

Esas capacidades pertenecen a las siguientes fases.

Sin embargo, debes desarrollar una arquitectura que permita incorporarlas sin rehacer el motor de voz.

Tu responsabilidad es implementar código real, ejecutarlo cuando el entorno lo permita, crear pruebas automatizadas, comprobar su rendimiento y documentar las limitaciones.

No declares funcionalidades terminadas cuando solo hayas implementado simulaciones.

---

# 1. CONTEXTO Y ESTADO ACTUAL DEL PROYECTO

## 1.1. Qué existe actualmente

La Fase 1 dispone de:

- Aplicación residente en Windows.
- Icono de bandeja.
- Ejecución sin consola.
- Inicio automático al iniciar sesión.
- Protección contra múltiples instancias.
- Captura única del micrófono.
- Conversión de audio.
- Búfer de audio.
- Rustpotter integrado y calibrado con la voz del usuario.
- Detección local de «Jarvis».
- Activación temporal y retorno a reposo.
- Pausa y reanudación.
- Cierre completo.
- Recuperación de dispositivos.
- Recuperación tras suspensión.
- Configuración persistente.
- Registros y diagnósticos.
- Máquina de estados.
- Supervisión de componentes.

## 1.2. Validación disponible

Se han reportado:

- 62 pruebas automáticas aprobadas.
- Detección correcta de «Jarvis» con la voz real del usuario.
- Retorno correcto a reposo.
- Inicio automático después de reiniciar Windows.
- Recuperación tras suspensión.
- Cierre limpio.
- CPU media de 0,38 % durante una medición de 60 segundos.
- Memoria máxima muestreada de 80,9 MiB.
- Sin bloques de audio perdidos en dicha prueba.

Estas son nuestras referencias iniciales, no garantías para versiones posteriores.

Las pruebas prolongadas durante videojuegos y el funcionamiento específico del micrófono de los audífonos todavía están pendientes.

## 1.3. Primera tarea obligatoria

Antes de modificar el código:

1. Inspecciona el repositorio existente.
2. Lee `README.md`.
3. Lee `docs/validation.md`.
4. Examina la arquitectura real.
5. Identifica cómo se administran el micrófono, los estados, los eventos, el búfer y el detector Rustpotter.
6. Comprueba cómo se ejecutan las pruebas.
7. Registra el estado inicial en Git.
8. Ejecuta las pruebas actuales.
9. Identifica los puntos exactos donde se integrará la Fase 2.

No supongas que el código coincide literalmente con los nombres de archivos de una especificación anterior. Inspecciona la implementación real.

Crea una rama de desarrollo identificable como `phase-2-voice` si el repositorio utiliza Git.

No sobrescribas la implementación funcional de la Fase 1 sin posibilidad de recuperación.

---

# 2. FILOSOFÍA DE LA FASE 2

El objetivo no es crear un programa que transcriba audio.

Queremos crear el **sistema auditivo y vocal definitivo de Jarvis**, sobre el cual se apoyarán las futuras capacidades inteligentes.

La experiencia debe ser natural:

**Usuario:** «Jarvis».

Jarvis se activa.

**Usuario:** «Hola, ¿me escuchas?».

**Jarvis:** «Sí, te escucho».

**Usuario:** «Perfecto».

**Jarvis:** «Listo».

El usuario deja de hablar.

Jarvis espera brevemente y vuelve a reposo.

Durante todo este intercambio, el usuario solamente necesitó decir «Jarvis» una vez.

La interacción debe ser por turnos, fluida y sin depender de botones.

## 2.1. Principios fundamentales

**Escucha selectiva:** no ejecutar reconocimiento completo de voz continuamente en reposo.

**Respuesta rápida:** comenzar a preparar el reconocimiento desde el momento de activación.

**Audio sin pérdidas:** no perder las palabras que el usuario pronuncia inmediatamente después de «Jarvis».

**Naturalidad:** detectar el final de una frase mediante actividad de voz, no mediante un temporizador rígido.

**Control de recursos:** utilizar CPU y descargar componentes pesados cuando no se necesitan.

**Privacidad local:** no enviar audio a servicios externos.

**Modularidad:** permitir cambiar el motor de transcripción o síntesis sin reconstruir el núcleo.

**Veracidad:** no afirmar que Jarvis comprende o ejecuta órdenes que todavía no están implementadas.

---

# 3. ARQUITECTURA DE LA FASE 2

La arquitectura debe funcionar así:

```text
                  WINDOWS
                     |
              Jarvis Core Fase 1
                     |
               AudioManager
                     |
              Micrófono único
                     |
               Búfer circular
                     |
                Rustpotter
                     |
             Detecta "Jarvis"
                     |
              SessionManager
                     |
          +----------+----------+
          |                     |
      VAD / voz            Preparación STT
          |                     |
          +----------+----------+
                     |
               Audio por turno
                     |
              STT Engine
                     |
          Transcripción final
                     |
              DialogueBridge
                     |
          Respuesta determinista
                     |
               TTS Engine
                     |
              Audio de salida
                     |
             SessionManager
                     |
         ¿Otra intervención?
              /          \
             Sí          No
             |            |
        Escuchar       DORMANT
```

## 3.1. Componentes nuevos

Implementa los siguientes componentes lógicos, adaptando los nombres a la estructura existente:

**VoiceSessionManager**

Coordina sesiones de interacción y turnos de voz.

**SpeechActivityDetector**

Detecta la presencia de voz humana y ayuda a delimitar las intervenciones.

**SpeechTurnSegmenter**

Determina dónde comienza y termina una frase, administrando silencios, duración máxima y búferes.

**SpeechRecognitionEngine**

Interfaz abstracta para los motores STT.

**MoonshineAdapter**

Implementación inicial de STT mediante Moonshine Voice.

**FasterWhisperAdapter**

Implementación alternativa para comparación y recuperación.

**TranscriptManager**

Gestiona transcripciones provisionales y finales.

**DialogueBridge**

Conecta la transcripción con una futura inteligencia conversacional.

**Phase2ResponseProvider**

Proporciona respuestas controladas para verificar el sistema durante esta fase.

**SpeechSynthesisEngine**

Interfaz abstracta para síntesis de voz.

**PiperAdapter**

Implementación inicial del TTS.

**SpeechPlaybackManager**

Controla la reproducción, cancelación y estado del audio de Jarvis.

**VoiceResourceManager**

Administra carga, retención y liberación de modelos.

No crees procesos o servicios innecesarios. Usa componentes ligeros y responsabilidades bien definidas.

---

# 4. CONSERVAR LA CAPTURA ÚNICA DEL MICRÓFONO

Este requisito es innegociable.

La Fase 1 ya dispone de un sistema de captura.

No debemos permitir que Moonshine, Silero, Rustpotter y otros componentes abran micrófonos independientes.

El flujo correcto será:

**Una fuente de captura → distribución de audio a los consumidores autorizados.**

El `AudioManager` existente debe continuar siendo el propietario del dispositivo de entrada.

## 4.1. Integración específica con Moonshine

La biblioteca Moonshine Voice incluye una clase llamada `MicTranscriber` que abre el micrófono directamente.

**No debes utilizar `MicTranscriber` como fuente de audio de Jarvis.**

Utiliza la clase `Transcriber`, que admite audio proporcionado desde una captura externa mediante `add_audio()`.

Investiga la API exacta de la versión instalada y úsala de acuerdo con su documentación oficial.

El adaptador debe:

- Cargar un modelo local español.
- Iniciar una sesión de transcripción.
- Recibir audio desde el `AudioManager`.
- Entregar fragmentos de audio al motor.
- Recibir actualizaciones parciales.
- Identificar segmentos finalizados.
- Finalizar correctamente el turno.
- Detener la sesión.
- Liberar recursos cuando corresponda.

No debe crear una segunda instancia de captura.

## 4.2. Distribución de audio según estado

En DORMANT:

- Audio hacia Rustpotter.
- No audio hacia STT.
- No inferencias de Silero salvo necesidad técnica justificada.

En AWAKE:

- Rustpotter deja de autorizar activaciones repetidas.
- Audio hacia el sistema de detección de voz.
- Audio hacia el sistema de reconocimiento según el diseño elegido.
- El búfer conserva las muestras necesarias para no perder palabras.

En RESPONDING:

- El sistema de captura se mantiene bajo control del núcleo.
- No debe autorizar nuevas transcripciones de la propia voz de Jarvis.
- Se aplicará la política de protección contra eco descrita más adelante.

Al volver a DORMANT:

- Se detiene la transcripción activa.
- Se limpian las colas de la sesión.
- Se restablece Rustpotter.
- Se conserva el estado global.
- No se reinicia toda la aplicación.

---

# 5. RECONOCIMIENTO DE VOZ — COMPARACIÓN DE MOTORES

No elegiremos el motor únicamente por popularidad.

Debes implementar una comparación reproducible entre Moonshine y faster-whisper.

## 5.1. Motor principal candidato: Moonshine Voice

Utiliza la versión actual y estable que resulte compatible con nuestro entorno Windows y Python.

La documentación del proyecto contempla modelos de español de streaming:

- Spanish Tiny Streaming, aproximadamente 34 millones de parámetros.
- Spanish Small Streaming, aproximadamente 123 millones de parámetros.

Empieza probando el modelo pequeño, pero mide si el modelo Tiny proporciona suficiente precisión con menor latencia y consumo.

Prioriza CPU.

No utilices GPU en la implementación inicial si la CPU proporciona un rendimiento aceptable.

El procesador disponible es un Ryzen 9 de la serie 4000.

## 5.2. Integración en tiempo real

Moonshine puede generar transcripciones provisionales durante una intervención.

Necesitamos distinguir claramente:

**Transcripción parcial**

Texto todavía susceptible de cambios.

Se utiliza para diagnóstico y, eventualmente, preparar procesamiento futuro.

**Transcripción final**

Texto estabilizado al concluir una intervención.

Es el único que debe enviarse al componente de respuesta durante esta fase.

Ejemplo:

```text
Parcial 1: "abre"
Parcial 2: "abre el"
Parcial 3: "abre el navegador"
Final:    "Abre el navegador"
```

Las transcripciones parciales no deben provocar acciones.

No ejecutes una respuesta por cada actualización.

## 5.3. Alternativa: faster-whisper

Implementa un adaptador independiente para faster-whisper.

Prueba inicialmente modelos ligeros en CPU mediante INT8.

Puedes evaluar `base` y `small`, considerando su calidad real con español y el consumo observado.

No instales modelos innecesariamente grandes.

El adaptador deberá exponer el mismo contrato que Moonshine, incluso si internamente necesita esperar a recibir una frase completa.

Es aceptable que el adaptador por lotes emita solamente un resultado final.

No simules streaming si el motor no lo proporciona de esa manera.

## 5.4. Contrato común

Ambos motores deberán cumplir una interfaz conceptual equivalente a:

```python
class SpeechRecognitionEngine:
    def load(self) -> None: ...
    def start_turn(self, turn_id: str) -> None: ...
    def feed_audio(
        self,
        samples,
        sample_rate: int
    ) -> None: ...
    def finish_turn(self) -> None: ...
    def cancel_turn(self) -> None: ...
    def unload(self) -> None: ...
```

La interfaz podrá utilizar métodos asíncronos cuando sea necesario.

Las transcripciones se comunicarán mediante eventos tipados que incluyan:

- Identificador de sesión.
- Identificador de turno.
- Texto.
- Tipo parcial o final.
- Marcas de tiempo.
- Motor utilizado.
- Indicador de error cuando corresponda.

No obligues a todos los motores a usar internamente el mismo mecanismo de segmentación.

## 5.5. Preparación y descarga de modelos

Debes medir cuánto tarda:

- La carga inicial del modelo.
- La primera transcripción.
- Una transcripción posterior con modelo cargado.
- La descarga de recursos.
- La nueva carga tras un periodo de inactividad.

Inicialmente prioriza una arquitectura que cargue STT cuando comienza una sesión y lo descargue después de inactividad.

Sin embargo, como el usuario puede comenzar a hablar inmediatamente después de «Jarvis», la captura de audio debe continuar acumulando las muestras de su primera frase mientras el modelo se prepara.

No pierdas las palabras pronunciadas durante un arranque frío.

Mantén un búfer de activación y otro búfer acotado para audio pendiente de procesar.

Los límites deberán impedir crecimiento indefinido de RAM.

## 5.6. Descargas de modelos

Las descargas de modelos deben ser operaciones explícitas de instalación o configuración.

Después de instalarlos:

- Deben funcionar sin conexión a internet.
- Deben disponer de rutas conocidas.
- Debe poder verificarse su integridad.
- Debe identificarse su versión.
- No deben intentar descargarse silenciosamente mientras el usuario está jugando.

Si un modelo no está instalado, informa del problema mediante diagnósticos en lugar de iniciar una descarga inesperada.

---

# 6. DETECCIÓN DE VOZ — SILERO VAD

La transcripción no es suficiente.

Jarvis debe identificar cuándo el usuario está hablando, cuándo realiza una pausa y cuándo terminó su intervención.

Para ello utilizaremos un detector de actividad vocal, inicialmente Silero VAD mediante ONNX Runtime en CPU.

Antes de añadirlo, verifica si Moonshine ofrece una señal de finalización de intervención suficientemente fiable para nuestro caso.

No ejecutes dos sistemas redundantes si uno resulta innecesario.

## 6.1. Qué debe detectar

El sistema debe distinguir operativamente entre:

- Silencio.
- Comienzo de actividad vocal.
- Voz en curso.
- Pausa breve.
- Final probable de intervención.
- Tiempo máximo excedido.

El VAD detecta características de voz, pero no identifica quién habla ni garantiza que una frase tenga sentido completo.

Por eso debe combinarse con temporizadores y eventos del sistema de transcripción.

## 6.2. Parámetros iniciales

Configura valores de partida:

- Tiempo para detectar inicio de voz: aproximadamente 150–300 ms de actividad compatible, sujeto a pruebas.
- Silencio para finalizar una intervención: inicialmente 650 ms.
- Tiempo máximo de espera para comenzar a hablar después de activar Jarvis: 6 segundos.
- Duración máxima inicial de una intervención: 20 segundos.
- Tiempo adicional para finalizar transcripción: configurable.
- Umbral de probabilidad del VAD: configurable y calibrable.

Estos valores son hipótesis de ingeniería.

Debes probarlos y ajustarlos según el audio real.

No los codifiques como constantes rígidas dispersas por el proyecto.

## 6.3. No cortar frases prematuramente

Ejemplo:

«Jarvis, quiero que... [pausa breve] ...me escuches».

No debemos cortar la frase solamente porque existe una pausa natural.

Debemos comparar varios umbrales de silencio.

La segmentación debe priorizar no perder información, sin introducir latencias excesivas.

## 6.4. Ruido de videojuegos

Silero puede detectar voces procedentes de:

- Discord.
- Videos.
- Juegos.
- Música.
- Personas cercanas.

No asumas que VAD equivale a identificación del usuario.

En esta fase utilizaremos la activación inicial y el estado de sesión para limitar el procesamiento.

Las mejoras de identificación del hablante y cancelación acústica se evaluarán posteriormente.

---

# 7. PROBLEMA CRÍTICO: NO PERDER LA PRIMERA ORDEN

El usuario debe poder decir:

«Jarvis, abre Chrome».

Sin necesidad de esperar a que termine una animación o se cargue el modelo.

Es especialmente importante porque la activación de Rustpotter puede completarse cuando el usuario ya empezó a pronunciar las palabras siguientes.

## 7.1. Solución

Debes aprovechar el búfer circular de Fase 1.

Cuando se detecte «Jarvis»:

1. Registrar el instante aproximado de activación.
2. Crear una nueva sesión de voz.
3. Conservar las muestras relevantes anteriores y posteriores.
4. Continuar capturando audio mientras se prepara el motor STT.
5. Entregar el audio acumulado al transcriptor cuando esté disponible.
6. Continuar con el audio en vivo.
7. Evitar duplicar o perder segmentos por errores en los límites del búfer.

El tamaño del búfer de espera debe calcularse según la latencia real de carga del motor.

El búfer de 1,5 segundos de Fase 1 no debe considerarse suficiente por definición para cubrir cualquier arranque frío.

## 7.2. Evitar incluir innecesariamente «Jarvis»

El motor STT debe recibir preferentemente la orden posterior a la palabra de activación.

Sin embargo, no cortes audio de manera agresiva si eso provoca pérdida de palabras.

Si el texto final todavía incluye «Jarvis», se puede eliminar el prefijo de activación mediante una transformación controlada.

No elimines palabras arbitrariamente.

## 7.3. Activación sin solicitud inmediata

Si el usuario dice solamente:

«Jarvis».

Debe activarse y quedar preparado para escuchar.

No debe interpretar el silencio posterior como una orden válida.

La primera fase ya dispone de una confirmación sonora. Puedes conservar esa señal durante la transición a la escucha.

No debe ser obligatorio producir una frase hablada completa por cada activación.

---

# 8. NUEVA GESTIÓN DE SESIONES Y TURNOS

La Fase 1 utiliza una ventana activa de diez segundos.

Ese comportamiento debe evolucionar.

No queremos que Jarvis vuelva a dormirse diez segundos después de activarse si el usuario sigue hablando.

## 8.1. Dos conceptos independientes

**Sesión**

Periodo durante el cual el usuario puede hablarle sin repetir «Jarvis».

**Turno**

Una intervención individual del usuario o una respuesta de Jarvis.

Una sesión puede contener varios turnos.

## 8.2. Estados internos de la sesión

Dentro del estado global AWAKE, incorpora subestados:

- PREPARING
- WAITING_FOR_SPEECH
- LISTENING
- FINALIZING_TRANSCRIPT
- PROCESSING_RESPONSE
- SPEAKING
- WAITING_FOR_FOLLOWUP
- ENDING

No es necesario reemplazar toda la máquina de estados global.

Utiliza una máquina de estados anidada o un controlador de sesión separado.

## 8.3. Secuencia normal

1. Rustpotter activa Jarvis.
2. Se crea un `session_id`.
3. Se prepara o reutiliza el modelo STT.
4. Jarvis comienza a escuchar.
5. El usuario habla.
6. El VAD detecta la intervención.
7. Se identifica el final de turno.
8. Se obtiene la transcripción final.
9. El proveedor de respuesta genera texto.
10. El TTS reproduce la respuesta.
11. Se abre una ventana para escuchar una nueva intervención.
12. Si el usuario habla, se crea otro turno.
13. Si transcurre suficiente tiempo sin actividad, termina la sesión.
14. Jarvis vuelve a DORMANT.

## 8.4. Tiempo de conversación

Configura inicialmente:

- Espera de primera intervención: 6 segundos después de quedar preparado.
- Espera de seguimiento después de una respuesta: 25 segundos.
- Cierre de sesión por inactividad real: configurable.
- Duración máxima de turno: configurable.

El temporizador de inactividad debe reiniciarse cuando exista una intervención válida o un evento de conversación que lo justifique.

No debe expirar mientras:

- El usuario está hablando.
- Se está finalizando una transcripción.
- Se está generando una respuesta.
- Jarvis está hablando.
- Existe un proceso de voz todavía activo que requiere finalizar ordenadamente.

Tampoco debe mantenerse activa indefinidamente por ruido que el sistema confunda con voz.

## 8.5. Varias intervenciones consecutivas

Ejemplo:

Usuario: «Jarvis».

Usuario: «Hola».

Jarvis: «Hola».

Usuario: «¿Me escuchas bien?».

Jarvis: «Sí, te escucho».

Usuario: «Gracias».

Jarvis: «Con gusto».

Si deja de existir interacción, Jarvis regresa a reposo.

No debe requerir una nueva activación entre esas frases.

---

# 9. SÍNTESIS DE VOZ — PIPER TTS

La voz de salida será local.

Utiliza inicialmente Piper, mediante la implementación disponible en `piper-tts`.

No implementes una integración con servicios de pago ni una API de voz remota.

## 9.1. Idioma y características

Queremos una voz:

- Masculina preferentemente, si existe una opción adecuada.
- En español.
- Clara.
- Natural.
- Rápida de sintetizar.
- Comprensible incluso con volumen moderado.
- Con poca carga computacional.

Prueba las voces disponibles en español, incluyendo opciones de español latinoamericano y de España.

No asumas que una voz existe con un nombre específico sin verificar el catálogo instalado.

Selecciona la mejor combinación de naturalidad y latencia.

Verifica la licencia de la voz elegida.

## 9.2. Motor independiente

Implementa una interfaz conceptual como:

```python
class SpeechSynthesisEngine:
    def load(self) -> None: ...
    def synthesize(self, text: str): ...
    def cancel(self) -> None: ...
    def unload(self) -> None: ...
```

La reproducción física del audio debe gestionarse por separado.

No acoples directamente la síntesis al controlador de conversación.

## 9.3. Reproducción

Jarvis debe poder:

- Reproducir una respuesta.
- Detectar cuándo termina.
- Cancelarla.
- Evitar reproducciones duplicadas.
- Controlar su volumen.
- Seleccionar dispositivo de salida.
- Recuperarse de cambios de dispositivo.
- Liberar recursos correctamente.

La reproducción no debe bloquear el hilo principal ni congelar la bandeja del sistema.

## 9.4. Respuestas breves

Para esta fase, usa respuestas deterministas de prueba.

Ejemplos:

- «Hola» → «Hola».
- «¿Me escuchas?» → «Sí, te escucho».
- «¿Cómo estás?» → «Estoy funcionando correctamente».
- «Gracias» → «Con gusto».
- «Adiós» → «Hasta luego», finalizando la sesión.

Estas respuestas no constituyen un motor de interpretación general.

Son pruebas controladas de la conversación por voz.

Si el usuario dice «abre Chrome», todavía no deberá abrir Chrome.

Podrá responder:

«Te escuché, pero todavía no tengo habilitado el control de aplicaciones».

Evita afirmar que ejecutó una acción que no existe.

## 9.5. Respuestas de diagnóstico

Implementa un modo de diagnóstico opcional en el que Jarvis pueda repetir la frase que reconoció.

Ejemplo:

Usuario: «Estoy haciendo una prueba de reconocimiento».

Jarvis: «Escuché: estoy haciendo una prueba de reconocimiento».

Esta función es para evaluar STT, no para el comportamiento normal definitivo.

No es necesario responder verbalmente a cada transcripción si el usuario no ha solicitado una respuesta.

---

# 10. PROBLEMA CRÍTICO: JARVIS NO DEBE ESCUCHARSE A SÍ MISMO

Este problema debe tratarse como un requisito técnico central.

Cuando Jarvis reproduce una respuesta por los altavoces, el micrófono puede capturar su propia voz.

Sin protección, esto puede provocar:

- Transcripciones falsas.
- Respuestas repetidas.
- Sesiones que nunca terminan.
- Activaciones no deseadas.
- Consumo de CPU innecesario.

## 10.1. Primera solución: conversación semidúplex

Para Fase 2, implementa inicialmente una política segura:

Cuando Jarvis está hablando:

- No se aceptan nuevas transcripciones del usuario.
- Se bloquea la ejecución de respuestas derivadas de ese audio.
- Se controla el estado de reproducción.
- Al terminar el sonido, se espera un periodo corto de estabilización.
- Se reactiva la escucha del usuario.

Esto puede implementarse sin cerrar necesariamente el micrófono.

Lo importante es que el audio reproducido no provoque nuevos turnos.

## 10.2. Interrupciones

Diseña el controlador para permitir interrupciones futuras.

En esta fase implementa, como mínimo, cancelación de respuesta desde un control de diagnóstico o la bandeja.

Puedes habilitar una interrupción por voz solamente si consigues demostrar que funciona con suficiente fiabilidad, sin confundir la voz del propio Jarvis con la del usuario.

No implementes una cancelación de eco improvisada y luego afirmes que está resuelto el problema.

Una verdadera conversación full-duplex con interrupciones habladas requerirá pruebas adicionales de cancelación acústica y reproducción.

La arquitectura debe permitir incorporarla después.

## 10.3. Auriculares

Con audífonos puede existir menos fuga acústica, pero no asumas que desaparece completamente.

Prueba altavoces y auriculares por separado.

La gestión de salida debe identificar cambios de dispositivo cuando sea posible.

---

# 11. DIÁLOGO DE PRUEBA SIN INTELIGENCIA GENERATIVA

La Fase 2 debe introducir un `DialogueBridge`, pero no un chatbot definitivo.

Su propósito será separar la adquisición de voz del procesamiento del significado.

## 11.1. Flujo

El STT entrega una transcripción final.

El `DialogueBridge` recibe el texto y el contexto mínimo de la sesión.

El proveedor de respuestas de Fase 2 determina una respuesta controlada.

La respuesta se entrega al TTS.

En la siguiente fase, reemplazaremos ese proveedor por un sistema híbrido de intención, contexto y modelo local.

## 11.2. Contrato futuro

Define estructuras claras.

Una entrada de diálogo podría incluir:

```python
@dataclass
class UserUtterance:
    session_id: str
    turn_id: str
    text: str
    language: str
    timestamp: float
```

Una respuesta podría ser:

```python
@dataclass
class AssistantReply:
    text: str
    end_session: bool = False
    should_speak: bool = True
```

Puedes ajustar los campos y tipos de tiempo según el sistema real.

El objetivo es que la Fase 3 no tenga que modificar el transcriptor para proporcionar inteligencia conversacional.

## 11.3. No crear comprensión falsa

No implementes cientos de reglas para aparentar que Jarvis comprende lenguaje natural.

La comprensión avanzada será responsabilidad de la siguiente fase.

Aquí solamente verificaremos que el audio entra, se transforma en texto, genera una respuesta controlada y sale como audio.

---

# 12. ADMINISTRACIÓN DE RECURSOS

El usuario dispone de:

- Ryzen 9 serie 4000.
- GTX 1660 Ti con 6 GB de VRAM.
- 16 GB de RAM.

Jarvis debe funcionar incluso durante videojuegos.

## 12.1. Política inicial

En DORMANT:

- Rustpotter activo.
- STT sin procesar audio.
- VAD sin procesar audio.
- TTS sin sintetizar.
- Sin LLM.
- Sin ocupación de GPU por nuevos modelos de Jarvis.

En AWAKE:

- Preparar los modelos necesarios.
- Procesar audio en CPU inicialmente.
- Mantener el contexto de sesión.
- Liberar recursos después de inactividad.

## 12.2. Modelos preparados

La mejor configuración debe decidirse mediante pruebas.

Compara:

**Opción A:** cargar STT desde cero después de cada activación.

**Opción B:** conservar STT cargado durante un periodo corto después de terminar la sesión.

**Opción C:** mantener un modelo STT pequeño preparado en RAM, sin inferencias cuando está dormido.

Mide:

- Tiempo de activación.
- Latencia de la primera frase.
- RAM en reposo.
- Consumo de CPU.
- Memoria del proceso.
- Tiempo de carga.
- Comportamiento tras varias sesiones.

No elijas la opción A únicamente porque consume menos RAM, si hace que cada conversación resulte incómodamente lenta.

Tampoco elijas C si consume recursos excesivos en relación con sus ventajas.

## 12.3. TTS

Aplica una estrategia semejante al sintetizador.

Puede permanecer cargado durante una sesión activa.

Después, utiliza una política de retención configurable.

No cargues y descargues el modelo para cada frase de una misma conversación.

## 12.4. Prioridad al juego

No introduzcas todavía detección compleja de videojuegos.

Primero garantiza que los motores de voz funcionen razonablemente en CPU.

Si existe una opción de aceleración GPU, impleméntala como alternativa configurable y mide su impacto.

No permitas que el sistema seleccione automáticamente GPU sin pruebas.

---

# 13. CONFIGURACIÓN NUEVA

Amplía el sistema persistente de configuración de Fase 1.

Incorpora parámetros equivalentes a:

```toml
[voice]
enabled = true
language = "es"
session_followup_seconds = 25
initial_speech_timeout_seconds = 6
max_utterance_seconds = 20

[stt]
engine = "moonshine"
model = "spanish-small"
device = "cpu"
retain_model_seconds = 90
partial_transcripts = true

[vad]
engine = "silero"
enabled = true
end_silence_ms = 650
speech_start_ms = 200

[tts]
engine = "piper"
enabled = true
voice = "configured-spanish-voice"
volume = 0.75
retain_model_seconds = 90

[dialogue]
provider = "phase2_test"

[audio]
barge_in = false
echo_guard = true
```

Este ejemplo representa una intención de configuración.

Debes adaptar claves y valores a los motores y modelos realmente instalados.

No consideres `spanish-small` ni `configured-spanish-voice` identificadores oficiales sin verificarlos.

El sistema debe validar tipos, rangos, compatibilidad y existencia de recursos.

Si STT o TTS no están disponibles, informa del estado degradado y conserva la funcionalidad de Fase 1.

---

# 14. CAMBIOS EN LA INTERFAZ DE BANDEJA

Conserva el icono existente.

Amplía sus opciones de diagnóstico.

Debe permitir consultar:

- Estado actual.
- Micrófono seleccionado.
- Motor STT activo.
- Modelo STT.
- Motor TTS.
- Voz seleccionada.
- Sesión activa.
- Última transcripción, si el registro de texto está permitido.
- Tiempo de transcripción.
- Tiempo de síntesis.
- Uso de recursos.

Agrega controles básicos para:

- Activar o desactivar respuestas habladas.
- Probar el TTS.
- Probar una transcripción.
- Cambiar entre motores STT.
- Abrir diagnósticos.
- Cancelar una respuesta en curso.
- Pausar Jarvis.
- Salir.

No conviertas esta fase en un proyecto de diseño de interfaz.

La prioridad es el motor de voz.

---

# 15. REGISTROS Y DIAGNÓSTICOS

Es necesario que cada frase pueda rastrearse técnicamente.

Queremos distinguir:

1. Cuándo terminó Rustpotter de detectar la activación.
2. Cuándo quedó preparado el reconocimiento.
3. Cuándo comenzó a hablar el usuario.
4. Cuándo terminó de hablar.
5. Cuándo se obtuvo la transcripción final.
6. Cuándo comenzó la síntesis.
7. Cuándo empezó a reproducirse el sonido.
8. Cuándo terminó la respuesta.
9. Cuándo se reanudó la escucha.
10. Cuándo terminó la sesión.

Utiliza marcas de tiempo monotónicas para medir intervalos.

No utilices solamente la hora del sistema para calcular latencias internas.

## 15.1. Métricas principales

Registra:

- Tiempo de carga del motor STT.
- Tiempo entre detección de voz y primera transcripción parcial.
- Tiempo desde fin de voz hasta transcripción final.
- Tiempo de respuesta del proveedor de diálogo.
- Tiempo de síntesis.
- Tiempo hasta comenzar la reproducción.
- Tiempo completo del turno.
- CPU y RAM.
- Audio perdido.
- Reinicios.
- Transcripciones vacías.
- Errores del motor.
- Cancelaciones.
- Sesiones abiertas y cerradas.

Los registros de texto reconocido deben poder desactivarse por privacidad.

No almacenes audio de forma permanente sin autorización.

---

# 16. BANCO DE PRUEBAS DE RECONOCIMIENTO

Esta fase debe tener un banco de pruebas real.

No quiero elegir Moonshine por intuición.

## 16.1. Herramienta de evaluación

Implementa un comando para evaluar archivos de audio contra varios motores.

Debe permitir:

- Seleccionar un directorio de grabaciones.
- Seleccionar motores.
- Ejecutar transcripciones.
- Medir latencias.
- Comparar resultados contra textos de referencia.
- Generar un informe.

Usa exactamente los mismos audios para comparar los modelos.

## 16.2. Frases de evaluación

Prepara al menos 50 frases y preferiblemente 100.

Incluye expresiones como:

- «Jarvis, abre Chrome».
- «Jarvis, quiero escuchar música».
- «Jarvis, ¿me escuchas?».
- «Jarvis, baja un poquito el volumen».
- «Jarvis, no apagues las luces».
- «Jarvis, cuando termine la canción, apaga la luz».
- «Jarvis, quiero escuchar Come As You Are».
- «Jarvis, abre Discord».
- «Jarvis, pon el modo jugar».
- «Jarvis, no, mejor pon las luces azules».
- «Jarvis, cierra el navegador».
- «Jarvis, después de esto abre Spotify».
- «Jarvis, ¿qué hora es?».

Las frases deben incluir:

- Español colombiano.
- Voz rápida y pausada.
- Distintas distancias al micrófono.
- Nombres propios.
- Nombres de programas.
- Títulos de canciones en inglés.
- Frases largas y cortas.
- Negaciones.
- Ruido moderado.
- Silencios naturales.

## 16.3. Grabaciones reales

Crea una herramienta para grabar voluntariamente un conjunto de pruebas.

No reutilices automáticamente grabaciones privadas de calibración si el usuario no ha autorizado ese uso.

Los audios del banco de pruebas deben guardarse solo cuando el usuario elija hacerlo.

## 16.4. Medidas

Calcula:

- WER: tasa de error de palabras.
- CER: tasa de error de caracteres.
- Latencia promedio.
- Latencia mediana.
- Percentil 95.
- Tiempo de carga.
- Memoria consumida.
- Velocidad de procesamiento relativa a la duración del audio.
- Número de transcripciones vacías.
- Alucinaciones durante silencios.

El informe debe distinguir errores del STT de errores del VAD.

No mezcles los resultados de un motor con los de otro.

## 16.5. Elección final del motor

Mi preferencia inicial es Moonshine.

Sin embargo, conserva faster-whisper cuando:

- Reconozca mejor la voz del usuario.
- Produzca menos errores con canciones y aplicaciones.
- Sea más estable.
- Ofrezca un equilibrio superior de latencia y consumo.

No decidas la elección definitiva sin observar los resultados.

---

# 17. PRUEBAS DEL CICLO DE CONVERSACIÓN

Necesitamos pruebas específicas para evitar comportamientos artificiales.

## 17.1. Activación y frase inmediata

Decir:

«Jarvis, ¿me escuchas?».

Esperado:

- Detecta Jarvis.
- Conserva las palabras posteriores.
- Transcribe la pregunta.
- Produce respuesta.
- No requiere segunda activación.

## 17.2. Activación con pausa

Decir:

«Jarvis».

Esperar un momento.

Decir:

«Hola».

Esperado:

- Mantiene la sesión abierta.
- Reconoce la frase.
- Responde.

## 17.3. Varios turnos

Decir:

«Jarvis».

«Hola».

«¿Me escuchas?».

«Gracias».

Esperado:

- Una sola activación.
- Tres intervenciones reconocidas.
- Respuestas individuales.
- Sin duplicaciones.
- Regreso a reposo tras la inactividad.

## 17.4. Frase con pausa interna

Decir:

«Jarvis, necesito que... [pausa] ...me confirmes que estás escuchando».

Esperado:

- No perder información.
- No responder prematuramente si el silencio es inferior al umbral configurado.
- Finalizar correctamente cuando concluye la frase.

## 17.5. Silencio

Decir solamente «Jarvis».

Permanecer callado.

Esperado:

- Jarvis se activa.
- Espera la primera intervención.
- No inventa una transcripción.
- Vuelve a reposo.

## 17.6. TTS y eco

Utilizar altavoces.

Hacer que Jarvis responda.

Esperado:

- No transcribe su propia voz como una nueva intervención.
- No responde a sí mismo.
- No entra en un bucle infinito.

## 17.7. Auriculares

Repetir pruebas utilizando el micrófono de los audífonos.

Verificar cambios de dispositivo y salida.

## 17.8. Cancelación

Cancelar una respuesta durante su reproducción.

Esperado:

- La reproducción termina.
- El estado se actualiza.
- No queda una tarea de audio bloqueada.
- La sesión se recupera o finaliza de forma coherente.

## 17.9. Suspensión

Suspender el computador y reanudarlo.

Esperado:

- No procesar audio obsoleto.
- Recuperar micrófono y salida.
- Recuperar los motores cuando sea necesario.
- Regresar al estado correcto.

---

# 18. RENDIMIENTO Y CRITERIOS DE ACEPTACIÓN

No establezcas objetivos de rendimiento imposibles.

Nuestro objetivo será medir y optimizar.

## 18.1. Metas iniciales

**Activación:** conservar la rapidez y fiabilidad de Rustpotter.

**Primera transcripción:** minimizar el tiempo desde que termina de hablar el usuario hasta que aparece el resultado final.

**Transcripciones posteriores:** aprovechar modelos cargados cuando resulte conveniente.

**TTS:** iniciar respuestas breves idealmente en menos de un segundo desde que recibe texto, con el modelo preparado.

**Conversación:** evitar pausas largas entre turnos.

**Reposo:** aproximarse lo máximo posible al comportamiento ligero de Fase 1, con cualquier aumento de memoria documentado y justificado.

**GPU:** no ocuparla de forma persistente en reposo.

Estas son metas, no valores garantizados.

## 18.2. Estabilidad

Realiza pruebas de:

- 20 activaciones consecutivas.
- 20 ciclos de conversación.
- 50 transcripciones.
- Repetidas cargas y descargas de modelos.
- Cambios de micrófono.
- Cancelaciones de TTS.
- Cierre durante procesamiento.
- Reanudación tras suspensión.

Ejecuta las pruebas prolongadas que permita el entorno.

No declares superada una prueba física sin haberla realizado.

## 18.3. Regresión

Las 62 pruebas de Fase 1 deben continuar aprobándose, salvo que exista un cambio justificado y documentado en sus contratos.

Añade pruebas nuevas.

No borres pruebas antiguas para que los resultados aparezcan correctos.

---

# 19. ESTRUCTURA SUGERIDA

Amplía el proyecto existente de forma coherente.

Una organización posible sería:

```text
jarvis/
│
├── core/
│   ├── lifecycle.py
│   ├── state_machine.py
│   ├── events.py
│   ├── voice_session.py
│   └── resource_manager.py
│
├── audio/
│   ├── capture.py
│   ├── devices.py
│   ├── ring_buffer.py
│   ├── vad.py
│   ├── turn_segmenter.py
│   ├── speech_recognition.py
│   ├── speech_synthesis.py
│   └── playback.py
│
├── speech/
│   ├── moonshine_adapter.py
│   ├── faster_whisper_adapter.py
│   ├── piper_adapter.py
│   └── model_manager.py
│
├── dialogue/
│   ├── bridge.py
│   ├── phase2_responses.py
│   └── models.py
│
├── diagnostics/
│   ├── speech_benchmark.py
│   ├── voice_metrics.py
│   └── voice_validation.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── audio/
│   ├── speech/
│   └── performance/
│
└── docs/
    ├── phase_2.md
    ├── voice_architecture.md
    ├── stt_benchmark.md
    └── voice_validation.md
```

Adapta la estructura a la organización real del repositorio.

No crees archivos duplicados si ya existen componentes que cumplen la misma función.

---

# 20. ORDEN DE IMPLEMENTACIÓN

Quiero que desarrolles esta fase progresivamente y mantengas el programa funcional entre cambios.

## Etapa 1 — Auditoría del proyecto

- Inspeccionar Fase 1.
- Ejecutar pruebas existentes.
- Identificar interfaces.
- Diseñar integración de audio.
- Registrar línea base de rendimiento.

## Etapa 2 — Administrador de sesiones

- Crear `VoiceSessionManager`.
- Incorporar subestados de conversación.
- Reemplazar el temporizador rígido de diez segundos por temporizadores dependientes de actividad.
- Añadir identificadores de sesión y turno.
- Crear pruebas de transición.

## Etapa 3 — Detección de voz

- Integrar VAD.
- Implementar detección de inicio y final.
- Manejar pausas.
- Implementar límites de duración.
- Probar audio simulado y real.

## Etapa 4 — Reconocimiento Moonshine

- Instalar dependencias.
- Descargar explícitamente el modelo español.
- Integrar `Transcriber` con el micrófono existente.
- Implementar transcripciones parciales y finales.
- Probar frases inmediatamente después de «Jarvis».
- Medir consumo y latencias.

## Etapa 5 — Faster-whisper

- Implementar adaptador alternativo.
- Crear banco de comparación.
- Ejecutar pruebas equivalentes.
- Documentar resultados.
- Seleccionar motor predeterminado provisional.

## Etapa 6 — Piper TTS

- Instalar Piper.
- Seleccionar voz española.
- Implementar síntesis.
- Implementar reproducción.
- Añadir cancelación.
- Integrar protección contra eco.
- Medir tiempos.

## Etapa 7 — Diálogo de prueba

- Crear `DialogueBridge`.
- Implementar respuestas deterministas.
- Habilitar varios turnos.
- Comprobar que no es necesario repetir «Jarvis».
- Validar cierre automático.

## Etapa 8 — Optimización

- Reducir latencias.
- Configurar retención de modelos.
- Comparar carga fría y caliente.
- Comprobar uso de CPU.
- Comprobar RAM.
- Revisar procesamiento durante reposo.

## Etapa 9 — Validación final

- Ejecutar pruebas de Fase 1.
- Ejecutar pruebas de Fase 2.
- Realizar pruebas de audio físico cuando sea posible.
- Actualizar documentación.
- Registrar limitaciones.
- Preparar informe final.

---

# 21. ENTREGABLES OBLIGATORIOS

Al finalizar la Fase 2 debes entregar:

**1. Código funcional**

Reconocimiento de voz, gestión de turnos, síntesis y diálogo de prueba.

**2. Integración con Fase 1**

Rustpotter y la aplicación residente deben seguir funcionando correctamente.

**3. Motor STT intercambiable**

Moonshine y faster-whisper disponibles a través de una interfaz común.

**4. Motor TTS**

Piper integrado, con reproducción y cancelación.

**5. Sesiones de voz**

Varios turnos de conversación sin repetir «Jarvis».

**6. Protección contra eco**

Comportamiento semidúplex seguro y documentado.

**7. Herramientas de diagnóstico**

Visualización de transcripciones, tiempos y errores.

**8. Pruebas automáticas**

Incluyendo regresión de Fase 1.

**9. Benchmark de reconocimiento**

Comparación reproducible de modelos, siempre que existan audios de referencia suficientes.

**10. Informe de rendimiento**

CPU, RAM y tiempos medidos, distinguiendo carga fría y caliente.

**11. Documentación actualizada**

Instalación, configuración, uso, problemas conocidos y arquitectura.

**12. Informe de validación**

Separar funcionalidades comprobadas, pruebas simuladas y verificaciones físicas pendientes.

---

# 22. DEFINICIÓN DE FASE 2 COMPLETADA

No consideres terminada la Fase 2 hasta que se haya demostrado que:

- Jarvis continúa iniciándose con Windows.
- Conserva Rustpotter.
- Detecta su palabra de activación.
- Puede escuchar una frase inmediatamente después de «Jarvis».
- Convierte frases españolas en texto.
- Distingue resultados provisionales y finales.
- Detecta el final de intervención.
- No termina sesiones mientras el usuario sigue hablando.
- Puede responder mediante voz local.
- Puede mantener varios turnos sin repetir «Jarvis».
- Puede cerrar la sesión por inactividad.
- Evita responder a su propia voz en el modo operativo seleccionado.
- Puede pausar y reanudar.
- Puede recuperarse de errores habituales.
- Puede cancelar una respuesta.
- No ejecuta órdenes de Windows todavía.
- Tiene pruebas automáticas y diagnósticos.
- Conserva la funcionalidad validada de Fase 1.
- Dispone de mediciones de rendimiento.
- Documenta cualquier requisito que no pudo comprobarse físicamente.

No confundas completar la implementación con validar completamente el comportamiento real.

---

# 23. EXPERIENCIA FINAL ESPERADA DE LA FASE 2

Cuando esta fase termine, quiero poder realizar el siguiente experimento sin usar el teclado:

Enciendo el computador.

Jarvis inicia automáticamente y queda dormido.

Digo:

**«Jarvis».**

Jarvis emite su señal de activación.

Digo:

**«Hola, ¿me escuchas bien?».**

Jarvis reconoce mi pregunta y responde:

**«Sí, te escucho».**

Sin repetir su nombre, digo:

**«Perfecto, estoy probando tu reconocimiento de voz».**

Jarvis identifica la frase correctamente.

En modo de diagnóstico puede confirmar el texto reconocido.

Después digo:

**«Gracias, Jarvis».**

Jarvis responde:

**«Con gusto».**

Dejo de hablar.

Después del periodo de inactividad configurado, Jarvis regresa automáticamente al estado dormido.

Su consumo de recursos vuelve a aproximarse al nivel de reposo de Fase 1.

Si vuelvo a decir «Jarvis», comienza una nueva sesión.

Todo el proceso debe funcionar localmente, sin depender de servicios externos.

---

# 24. EL ALMA DE ESTA FASE

La Fase 2 no consiste únicamente en agregar Whisper, Moonshine o Piper a un programa.

Consiste en construir la capacidad de Jarvis para **escuchar y hablar como un sistema coherente, con administración de turnos y conciencia de su propio estado**.

No quiero que Jarvis:

- Se duerma mientras hablo.
- Responda antes de que termine una frase.
- Se active repetidamente por su propia voz.
- Pierda las primeras palabras de una orden.
- Abra varios micrófonos.
- Consuma la GPU permanentemente.
- Mantenga modelos grandes ejecutándose sin motivo.
- Se bloquee cuando una transcripción falle.
- Necesite que repita su nombre constantemente.
- Confunda una transcripción parcial con una instrucción definitiva.

Quiero una experiencia fluida, eficiente y predecible.

El sistema debe parecer sencillo desde la perspectiva del usuario, incluso si internamente hay varios componentes especializados.

La sofisticación debe estar en la ingeniería, no en obligar al usuario a aprender cómo funciona Jarvis.

---

# 25. INSTRUCCIÓN FINAL PARA CODEX

**Comienza ahora la implementación de JARVIS FASE 2 — VOICE ENGINE.**

Primero inspecciona el repositorio y ejecuta las pruebas de Fase 1.

Después implementa progresivamente el reconocimiento de voz, la detección de turnos, las respuestas habladas, la gestión de sesiones y los diagnósticos.

Trabaja con Moonshine como primer candidato, pero conserva la posibilidad de utilizar faster-whisper y selecciona el motor según los resultados medidos.

Utiliza Piper para la síntesis de voz local.

Conserva la captura única del micrófono.

No introduzcas un LLM en esta fase.

No implementes todavía acciones sobre Windows, Spotify o dispositivos inteligentes.

No reescribas Rustpotter ni el núcleo residente que ya funcionan.

Corrige los problemas que encuentres, realiza pruebas y conserva evidencia de los resultados.

Si una prueba depende de mi micrófono, altavoces o sesión interactiva de Windows y no puedes ejecutarla realmente, prepara el procedimiento exacto para que yo la realice.

Actualiza el README y el informe de validación.

**No avances a la Fase 3 hasta que la Fase 2 esté implementada, probada y expresamente aprobada.**

El resultado que quiero es un Jarvis que ya pueda escuchar, transcribir, hablar y continuar una interacción por turnos de forma natural, manteniendo el consumo de recursos controlado.

**Empieza a desarrollar el código real ahora.**