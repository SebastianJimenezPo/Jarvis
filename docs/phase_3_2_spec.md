# FASE 3.2 — JARVIS NEXT: RECONSTRUCCIÓN DEL MOTOR DE INTELIGENCIA Y ARQUITECTURA DE ACCIONES

## 1. Contexto y decisión de arquitectura

Hemos terminado parcialmente la Fase 3.1, cuyo último punto de referencia es el commit `5337b86` de la rama `phase-3-1-hardening`.

Después de revisar los resultados, las limitaciones de comprensión, el consumo de recursos y la experiencia que busco obtener con Jarvis, he decidido cambiar considerablemente la dirección arquitectónica del proyecto.

No quiero continuar acumulando reglas, expresiones regulares, modelos semánticos y mecanismos de recuperación para compensar indefinidamente las limitaciones de un modelo de lenguaje pequeño ejecutado localmente.

Tampoco quiero reconstruir innecesariamente los componentes que ya funcionan.

La nueva decisión consiste en:

**Conservar el núcleo residente y las capacidades útiles de las fases anteriores, pero reconstruir el motor de inteligencia con una arquitectura más sencilla, eficiente, modular y orientada a acciones.**

Tienes autorización para eliminar componentes, reemplazar módulos completos, reorganizar paquetes, modificar contratos internos y abandonar decisiones técnicas anteriores cuando exista una razón fundamentada.

No tienes la obligación de conservar una implementación simplemente porque ya está desarrollada.

Las decisiones deberán justificarse por su aporte real a la precisión, latencia, consumo, seguridad, mantenibilidad o experiencia de usuario.

No inicies una reconstrucción completa del proyecto desde cero si podemos conservar componentes independientes que ya funcionan.

## 2. Nueva filosofía de Jarvis

A partir de ahora, Jarvis debe concebirse como:

**Un asistente personal residente para Windows y dispositivos conectados, orientado a ejecutar acciones mediante lenguaje natural, que permanece disponible continuamente y consume recursos de forma proporcional al trabajo que realiza.**

Los objetivos principales, en orden de importancia, son:

1. Permanecer disponible siempre que Windows esté funcionando y el micrófono esté habilitado.
2. Mantener un consumo mínimo de CPU, RAM y GPU durante el reposo.
3. Comprender instrucciones naturales en español, incluidas correcciones, referencias, excepciones y solicitudes de varios pasos.
4. Controlar el computador, aplicaciones, audio, multimedia y dispositivos inteligentes.
5. Ejecutar las acciones con baja latencia y verificar sus resultados.
6. Mantener un funcionamiento básico local cuando internet o los servicios remotos no estén disponibles.
7. Evitar interferir significativamente con videojuegos y otras aplicaciones exigentes.

La conversación general, explicaciones extensas, generación de textos, conocimientos enciclopédicos y funciones de chatbot son secundarias.

Jarvis no necesita ser un chatbot extraordinario.

Necesita entender suficientemente bien lo que quiero hacer, identificar las herramientas adecuadas y ejecutar las acciones correctamente.

Principio rector:

**Jarvis debe consumir recursos para hacer cosas, no simplemente para existir.**

## 3. Preservación del proyecto y estrategia de migración

Antes de comenzar:

- Revisa el estado actual del repositorio, el historial, `AGENTS.md`, los contratos, los informes de Fase 3.1 y las pruebas.
- Conserva el commit `5337b86` como punto de referencia reproducible.
- Mantén intacta la rama `phase-3-1-hardening`.
- Crea una nueva rama de desarrollo denominada `phase-3-2-jarvis-next`, o un nombre equivalente debidamente documentado.
- No sobrescribas ni elimines cambios locales del usuario.
- Si existen archivos locales no versionados o configuraciones personales, consérvalos.
- No realices una migración destructiva del entorno personal, las referencias de activación, el micrófono o las preferencias existentes.

El código nuevo puede desarrollarse inicialmente en módulos separados cuando facilite la comparación con la arquitectura anterior.

Sin embargo, evita mantener permanentemente dos arquitecturas completas dentro del runtime.

La arquitectura antigua puede permanecer disponible mediante Git, herramientas de evaluación o un adaptador temporal. No debe convertirse en una segunda infraestructura obligatoria que aumente el consumo de la nueva versión.

La nueva arquitectura deberá ser progresivamente la única ruta principal cuando haya demostrado que es superior.

## 4. Resultados de Fase 3.1 que deben orientar el rediseño

Toma como referencia los resultados documentados:

- 379 pruebas locales aprobadas.
- CI headless con 373 pruebas aprobadas, una omitida y cinco excluidas.
- Clasificación general del 86,7%.
- Precisión del 100% en las propuestas emitidas del conjunto evaluado.
- Recuperación de acciones esperadas del 86,4%.
- Exactitud de parámetros del 84,5%.
- Resolución contextual del 95,6% en su categoría específica.
- Nueve aclaraciones innecesarias.
- Una cancelación no reconocida.
- Cero propuestas indebidas en el conjunto crítico final de 104 escenarios y cero bypasses en 1.062 propuestas forzadas.
- Ninguna de las seis secuencias sintéticas de voz completada correctamente.
- Siete de 18 turnos de integración de voz correctos.
- Latencia mediana de integración sintética cercana a 6,94 segundos.

En recursos:

- Reposo de 30 segundos: CPU media aproximada del 0,365% y RSS pico del árbol residente de 89,3 MB.
- Ollama y descendientes: aproximadamente 1,7 GB de RSS cuando el modelo estaba activo.
- E5 aislado: aproximadamente 820 MB de RSS cargado.
- E5 no fue la ruta final de resolución de ningún turno de la evaluación general de 181 turnos.
- Qwen con dos hilos: propuesta JSON fría de aproximadamente 10,32 segundos de mediana y preparada de aproximadamente 3,98 segundos.

Estos resultados no constituyen garantías generales ni pruebas de estabilidad prolongada, rendimiento durante videojuegos o precisión con mi voz real.

No interpretes el número de pruebas aprobadas como evidencia suficiente de que Jarvis ya ofrece una buena experiencia de usuario.

La Fase 3.2 debe mejorar resultados prácticos, no solamente aumentar la cantidad de pruebas.

## 5. Nueva arquitectura general

Diseña Jarvis alrededor de cinco responsabilidades claramente diferenciadas.

### A. Núcleo residente

Responsable de:

- Activación con la palabra Jarvis.
- Captura mínima de audio.
- Bandeja de Windows.
- Inicio automático.
- Gestión de sesiones.
- Suspensión, reanudación y cierre.
- Prevención de instancias duplicadas.
- Activación y liberación de trabajadores.

Debe permanecer disponible sin mantener modelos pesados ejecutándose permanentemente.

### B. Reconocimiento de voz

Responsable de convertir una orden hablada en texto y proporcionar los indicadores de incertidumbre que realmente admita el motor utilizado.

Debe ser intercambiable.

El reconocedor no debe ejecutar acciones ni modificar el contexto operativo.

### C. Interpretación de intenciones

Responsable de transformar el texto y el contexto necesario en una decisión estructurada.

Debe disponer de dos rutas principales:

- Interpretación local mínima para órdenes inequívocas.
- Interpretación mediante un modelo más capaz para instrucciones naturales, contextuales o ambiguas.

La ruta remota será una opción experimental prioritaria.

### D. Gestor de acciones, contexto y políticas

Responsable de:

- Resolver referencias.
- Administrar planes.
- Aplicar correcciones.
- Mantener memoria operativa.
- Comprobar permisos.
- Validar parámetros.
- Verificar autorización.
- Gestionar cancelaciones.
- Evitar respuestas tardías y estados inconsistentes.
- Decidir si una operación puede ejecutarse, necesita confirmación o debe rechazarse.

Esta capa debe ser independiente del proveedor de IA.

### E. Herramientas y resultados

Responsable de:

- Consultar el estado de aplicaciones y dispositivos.
- Ejecutar acciones autorizadas.
- Verificar el resultado.
- Informar errores.
- Registrar los cambios necesarios para correcciones posteriores.
- Proporcionar resultados estructurados para generar confirmaciones breves.

En esta fase las herramientas continuarán inicialmente en simulación.

El diseño debe permitir integrar después herramientas reales sin reconstruir nuevamente toda la inteligencia.

## 6. Conservación y revisión de los componentes actuales

### Conservar inicialmente

- Rustpotter y su infraestructura de activación.
- Gestión residente de Windows.
- Bandeja y control de instancia única.
- Inicio automático.
- Captura de audio.
- Silero VAD.
- Piper.
- Gestión de ciclos de vida de procesos y modelos que haya demostrado utilidad.
- Las enseñanzas de la validación independiente.
- Las pruebas y corpus de regresión útiles.
- Los mecanismos de cancelación, revisiones y protección contra resultados tardíos.
- El CI.

No es obligatorio conservar exactamente sus implementaciones si una modificación mejora claramente el resultado.

### Reconstruir o simplificar

- `DialogueManager`.
- `FastPath`.
- El contrato de interpretación.
- La selección de rutas.
- La gestión de contexto de acciones.
- La autorización lingüística.
- La composición de respuestas.
- La integración con proveedores de modelos.

### Desactivar inicialmente en Jarvis Next

- E5 como componente obligatorio del flujo principal.
- Qwen como modelo principal obligatorio.
- La necesidad de tener Ollama instalado para usar Jarvis.

E5 puede conservarse temporalmente para comparaciones.

Qwen puede mantenerse como proveedor local opcional, pero deberá demostrar que aporta suficiente valor como alternativa offline.

La configuración principal debe poder funcionar sin E5 y sin modelos LLM locales.

No descargues modelos automáticamente ni mantengas Ollama cargado por defecto en el perfil remoto.

Si los componentes antiguos dejan de aportar valor tras las pruebas, puedes retirarlos de la distribución y de las dependencias activas.

## 7. Nuevo intérprete: eliminar complejidad innecesaria

El flujo anterior está demasiado condicionado por la combinación de:

- Expresiones regulares.
- Recuperación de fragmentos.
- Clasificación semántica.
- Qwen.
- Validaciones dependientes de vocabulario reconocido.

El nuevo motor no debe intentar reproducir toda la comprensión del español mediante expresiones regulares.

Diseña una ruta rápida pequeña, determinista y confiable.

Ejemplos apropiados:

- Abre Steam.
- Volumen al 30%.
- Pausa la música.
- Silencia el audio.
- Cancela.

Estas órdenes deben poder resolverse localmente sin consultar un LLM cuando sean realmente inequívocas y estén autorizadas.

La ruta rápida no debe apropiarse de una solicitud solamente porque contiene un verbo y una entidad conocidos.

Ejemplo:

«Abre Steam, pero no todavía; cuando termine la descarga».

No debe interpretarse como una apertura inmediata de Steam.

Ejemplo:

«¿Cómo puedo abrir Steam automáticamente?».

No debe interpretarse como una solicitud de ejecución.

La ruta directa deberá reconocer la totalidad de la solicitud dentro de su alcance admitido.

Si existe una estructura compleja, referencias ambiguas, exclusiones, correcciones, lenguaje indirecto o una parte significativa que no pueda interpretar, no debe producir una propuesta parcial sin autorización.

Debe delegar la comprensión al intérprete inteligente o solicitar aclaración.

El modelo inteligente se utilizará para entender frases como:

- «Arranca Steam, que voy a jugar».
- «Quiero que abras Spotify para escuchar música».
- «Tráeme al frente el navegador que estaba utilizando».
- «La música está un poco fuerte».
- «Deja las luces como estaban antes».
- «Mejor azules, pero conserva lo demás».
- «Prepara todo para jugar, excepto Discord».
- «Haz lo mismo que antes, pero con el volumen más bajo».

No mantengas una cadena obligatoria de FastPath, E5, Qwen y API para cada turno.

El objetivo es que una orden directa use la ruta local y una compleja utilice, normalmente, una única interpretación inteligente.

## 8. Proveedores de inteligencia intercambiables

Crea una abstracción de proveedor independiente de Ollama y de cualquier API concreta.

El resto de Jarvis no debe necesitar saber si la interpretación procede de:

- Groq.
- Gemini.
- Otro proveedor remoto.
- Ollama.
- Un proveedor simulado para pruebas.

Define una interfaz clara para:

- Recibir solicitudes estructuradas.
- Entregar respuestas validadas conforme al contrato.
- Cancelar o descartar solicitudes.
- Gestionar límites de tiempo.
- Informar errores normalizados.
- Exponer métricas de latencia y consumo de tokens cuando estén disponibles.
- Gestionar el ciclo de vida de la conexión.
- Declarar capacidades como salidas estructuradas.

No necesitas crear una infraestructura excesivamente abstracta ni un sistema de plugins complejo si una interfaz sencilla cumple los requisitos.

Evita acoplar el gestor de contexto al formato particular de un proveedor.

### Proveedor remoto inicial

Quiero que se evalúe primero GroqCloud por su enfoque de inferencia rápida.

También puede evaluarse Gemini Flash-Lite u otro modelo equivalente si ofrece ventajas de comprensión, disponibilidad, estructura de respuestas o latencia.

Antes de elegir modelos concretos, consulta la documentación oficial vigente del proveedor.

No asumas que un modelo mencionado en conversaciones anteriores sigue disponible gratuitamente, mantiene la misma cuota o admite el mismo formato de respuesta.

Prioriza modelos con:

- Acceso gratuito dentro de límites razonables.
- Buena comprensión del español.
- Respuestas estructuradas.
- Baja latencia.
- Capacidad suficiente para resolver referencias y planes pequeños.
- Posibilidad de limitar la longitud de la respuesta.
- Ausencia de necesidad de ejecutar un modelo grande en mi computador.

No quiero depender obligatoriamente de una API de pago.

No actives facturación, compres créditos ni utilices servicios de pago sin autorización explícita.

La disponibilidad del nivel gratuito puede variar, por lo que el proveedor debe ser reemplazable.

### Gestión de credenciales

Las claves deben proporcionarse mediante mecanismos locales seguros, como variables de entorno o un almacén de credenciales del sistema.

Nunca deben:

- Incorporarse al código.
- Aparecer en Git.
- Escribirse en informes.
- Registrarse en errores.
- Enviarse a otro proveedor.
- Incluirse en capturas o documentación pública.

Ten especialmente presente que el repositorio puede ser público.

Si necesitas una API key que no está configurada, explica claramente cómo debo obtenerla y configurarla. Mientras tanto, continúa el desarrollo mediante un proveedor falso y pruebas locales.

No inventes resultados de llamadas remotas que no se hayan realizado.

## 9. Política de funcionamiento remoto

Jarvis no debe consultar una API mientras está esperando su palabra de activación.

No debe mantener una conversación artificialmente activa con el proveedor.

No debe enviar grabaciones continuas de micrófono.

En la arquitectura inicial, el proveedor remoto de lenguaje recibirá únicamente texto y el contexto mínimo necesario.

La solicitud puede contener:

- Transcripción actual.
- Identificador de sesión y turno, cuando sea necesario para la coordinación local.
- Referentes activos relevantes.
- Plan actual pertinente.
- Pregunta pendiente.
- Estado operativo disponible y necesario.
- Preferencias explícitas relacionadas con la solicitud.
- Catálogo reducido de herramientas autorizadas.

No envíes todo el historial del usuario si no aporta información necesaria.

No envíes archivos personales, documentos, credenciales, contenido de pantalla, información sensible ni estados completos innecesarios.

Las instrucciones del usuario y los datos externos deberán tratarse como datos no confiables, no como instrucciones privilegiadas del sistema.

El modelo no tendrá acceso directo a Windows, Python, PowerShell, procesos o dispositivos.

Solo propondrá decisiones estructuradas.

### Latencia de la API

Optimiza mediante:

- Una solicitud por interpretación compleja cuando sea suficiente.
- Conexiones HTTP reutilizables durante las sesiones, si aportan ventajas.
- Prompts compactos.
- Catálogos reducidos a las herramientas pertinentes.
- Límites de salida acordes con planes pequeños.
- Desactivación de razonamiento prolongado cuando el modelo y el proveedor lo permitan y las pruebas demuestren que conviene.

No introduzcas streaming complejo únicamente porque está disponible.

Las propuestas de acciones deberán recibirse completas y validarse íntegramente antes de autorizar cualquier ejecución.

### Fallos y cuotas

Contempla:

- Ausencia de conexión.
- Timeout.
- Error de autenticación.
- Límite de solicitudes.
- Cuota agotada.
- Modelo retirado o no disponible.
- Respuesta malformada.
- JSON válido con interpretación incorrecta.
- Cancelación durante la consulta.
- Respuesta tardía perteneciente a una sesión anterior.

Establece límites de tiempo globales para evitar que una solicitud bloquee el asistente durante periodos excesivos.

Evita reintentos automáticos en cadena y fallbacks que multipliquen la latencia.

Utiliza una política de degradación controlada y un mecanismo sencillo de suspensión temporal del proveedor cuando existan fallos repetidos.

Si el proveedor no está disponible:

- Las órdenes directas locales deben seguir funcionando.
- Las solicitudes complejas pueden utilizar un proveedor local opcional si está habilitado y es adecuado.
- Cuando no exista una interpretación fiable, Jarvis debe pedir una aclaración o informar la limitación.

No cambies automáticamente a un servicio de pago.

## 10. Nuevo contrato de interpretación y decisiones

Reconstruye el contrato actual si es necesario.

El nuevo modelo debe expresar explícitamente qué pretende hacer el usuario con respecto a la sesión y al plan existente.

No es suficiente devolver exclusivamente una lista de acciones.

Debe ser posible representar:

- Crear una solicitud.
- Añadir acciones.
- Modificar una acción concreta.
- Reemplazar un plan.
- Eliminar una acción.
- Cancelar un subconjunto.
- Cancelar completamente.
- Retener o suspender la autorización.
- Responder una aclaración.
- Consultar un estado.
- Solicitar aclaración.
- Registrar una preferencia, si la capacidad está habilitada.
- Identificar una solicitud futura o condicionada.
- Rechazar una capacidad no disponible.
- Mantener una conversación que no autoriza acciones.

No es necesario implementar todas las funciones de ejecución correspondientes en esta fase.

Sí es necesario que el diseño no confunda estos tipos de decisiones.

Las operaciones sobre planes deberán poder referirse a identificadores estables de acciones.

Los identificadores válidos deben proceder del estado local, no ser inventados por el modelo.

Ejemplo conceptual:

```json
{
  "operation": "modify_plan",
  "expected_plan_revision": 4,
  "changes": [
    {
      "action_id": "light_color_01",
      "parameters": {
        "color": "blue"
      }
    }
  ],
  "add_actions": [
    {
      "intent": "set_light_brightness",
      "target": "main_light",
      "parameters": {
        "delta": -10
      }
    }
  ]
}
```

El ejemplo es orientativo. Define los contratos definitivos de acuerdo con la arquitectura.

Para cada acción, contempla:

- Identificador de intención o herramienta.
- Identificador de objetivo.
- Parámetros tipados.
- Evidencia en la solicitud.
- Referencias contextuales utilizadas.
- Dependencias cuando sean necesarias.
- Alcance temporal.
- Información de ambigüedad o aclaración.

Utiliza esquemas estrictos y validación local, preferiblemente mediante contratos tipados consistentes con el proyecto.

No aceptes propiedades arbitrarias, herramientas desconocidas o parámetros adicionales no autorizados.

Un JSON válido no significa que el usuario haya autorizado la acción.

Las propuestas del modelo deben considerarse datos no confiables hasta superar las políticas locales.

## 11. Reconstrucción de la memoria operativa

No quiero que el contexto de Jarvis dependa principalmente de almacenar conversaciones largas.

Quiero una memoria operativa que represente lo que está ocurriendo y qué operaciones estamos realizando.

Separa al menos cuatro conceptos.

### A. Contexto de sesión

Información temporal:

- Solicitud actual.
- Pregunta pendiente.
- Plan en elaboración.
- Última intención.
- Entidades mencionadas.
- Últimas respuestas relevantes.
- Confirmaciones y cancelaciones.

### B. Referentes operativos

Representa:

- Aplicación a la que me refiero.
- Reproductor de música activo.
- Luz o grupo de luces mencionado.
- Dispositivo de audio.
- Escena o modo seleccionado.

Los referentes pueden permanecer disponibles cuando sea razonable, incluso si termina una intervención hablada.

No deben considerarse válidos indefinidamente.

Establece reglas de expiración, sustitución y resolución de ambigüedad según su tipo.

No aumentes simplemente el TTL global esperando solucionar todos los problemas de contexto.

### C. Estado observado

Representa el estado real conocido de los recursos.

Ejemplos:

- Volumen actual.
- Estado de silencio.
- Aplicaciones abiertas.
- Ventana activa.
- Reproductor multimedia.
- Dispositivo encendido o apagado.
- Color y brillo de una luz.

Cada estado debe distinguir entre:

- Observado realmente.
- Informado por una herramienta.
- Último estado conocido, posiblemente desactualizado.
- Desconocido.
- Simulado.

Cuando una acción dependa del estado actual, deberá consultarlo o comprobar su vigencia.

No confundas una acción propuesta con un estado físico confirmado.

### D. Historial operativo y preferencias

Prepara una estructura para:

- Últimas acciones ejecutadas.
- Resultados.
- Estado anterior cuando sea necesario para revertir cambios.
- Alias de dispositivos.
- Modos personalizados.
- Preferencias explícitas.

Las preferencias persistentes pueden almacenarse posteriormente mediante SQLite u otro mecanismo local sencillo.

No incorpores una base vectorial de memoria ni un sistema de recuperación complejo sin demostrar su necesidad.

No guardes conversaciones completas permanentemente por defecto.

No deduzcas ni persistas hábitos privados sin autorización del usuario.

### Ejemplo de funcionamiento esperado

Usuario: «Pon la luz del escritorio azul».

Jarvis identifica el dispositivo y propone o ejecuta la acción según el modo habilitado.

Usuario: «Un poquito más suave».

Jarvis recupera el referente de la luz del escritorio, identifica la intención de reducir el brillo, conserva el color azul y consulta el brillo real antes de calcular el nuevo valor cuando exista ejecución real.

Usuario: «No, como estaba antes».

Jarvis deberá utilizar un estado anterior confirmado si existe.

Si ese estado nunca se observó, debe preguntar o explicar que no puede recuperarlo.

No debe inventarlo.

## 12. Gestión centralizada de planes y cancelaciones

Todos los intérpretes deben producir decisiones, pero no modificar directamente el estado definitivo.

Crea un gestor central que aplique las decisiones de forma consistente.

Conserva y aprovecha los principios de Fase 3.1:

- Revisiones.
- Copias de trabajo o transacciones equivalentes.
- Confirmación atómica.
- Control de sesión.
- Protección contra resultados fuera de orden.
- Cancelación.
- Validación previa.
- Límites de tamaño de planes.

La implementación concreta puede reconstruirse.

Corrige expresamente el defecto detectado en `DialogueManager`:

Una interpretación `Kind.CANCEL` puede establecer una operación de cancelación sin modificar efectivamente el contexto si el intérprete no lo hizo previamente.

La cancelación debe aplicarse mediante una operación centralizada, independientemente de si proviene de reglas, un modelo local, una API o la interfaz de bandeja.

Ejemplos obligatorios:

- «Cancela».
- «Olvida todo lo anterior».
- «Quita lo de las luces».
- «No canceles».
- «No quiero cancelar».
- «Todavía no hagas nada».
- «Olvida eso y abre Chrome».
- «Mejor no abras Discord».
- «Conserva Steam, pero quita lo de la música».

Distingue claramente:

- Cancelar una acción pendiente.
- Cancelar todo un plan.
- Retener una autorización.
- Reemplazar una solicitud.
- Negar una acción.
- Modificar una acción existente.
- Deshacer una acción ya ejecutada.

Cancelar una propuesta no equivale a revertir una operación física anterior.

Las respuestas tardías de la API nunca deben reactivar una solicitud cancelada.

Una confirmación pendiente debe asociarse a la revisión y al contenido concreto de la operación autorizada.

Si el plan cambia, una confirmación anterior no debe autorizar automáticamente el nuevo plan.

No mantengas planes antiguos ejecutables únicamente porque permanecen en memoria.

## 13. Rediseño de la validación y seguridad

Esta sección es especialmente importante.

La Fase 3.1 consiguió buenos resultados de seguridad, pero también demostró que la autorización basada excesivamente en vocabulario reconocido limita la comprensión.

No quiero conservar una lista cerrada de palabras permitidas como mecanismo central para decidir si una instrucción válida en español puede comprenderse.

Tampoco quiero que la solución sea eliminar las comprobaciones de seguridad y confiar completamente en el LLM.

Separa dos funciones:

### Comprensión semántica

Determinar qué quiere decir el usuario.

Puede apoyarse en un modelo de lenguaje más potente.

### Autorización de acciones

Determinar qué puede hacer Jarvis de manera segura con la solicitud interpretada.

Debe comprobarse localmente mediante políticas, contratos y evidencia suficiente.

Conserva mecanismos de protección contra:

- Negaciones.
- Condiciones futuras.
- Hipótesis.
- Citas de órdenes.
- Preguntas informativas.
- Cancelaciones.
- Acciones mencionadas pero no solicitadas.
- Instrucciones incrustadas.
- Cambios de contexto.
- Objetivos inventados.
- Parámetros fuera de rango.
- Herramientas no autorizadas.
- Reutilización indebida de confirmaciones.
- Respuestas de proveedores obsoletas o manipuladas.

La presencia de una palabra desconocida no debe ser, por sí sola, una razón suficiente para rechazar toda solicitud.

Sin embargo, si una parte desconocida de la instrucción puede modificar su alcance, temporalidad, intención o autorización, no se debe ignorar.

El sistema debe interpretar esa parte, pedir aclaración o abstenerse.

No sustituyas la validación lingüística anterior por un simple esquema JSON.

Un modelo podría devolver un JSON perfectamente válido que solicite una acción contraria a lo que dijo el usuario.

La política deberá considerar:

- Herramienta autorizada.
- Objetivo real disponible.
- Parámetros válidos.
- Evidencia explícita o referencia contextual fundamentada.
- Riesgo de la operación.
- Alcance completo de la solicitud.
- Temporalidad.
- Estado vigente.
- Consentimiento cuando corresponda.

Define niveles sencillos de riesgo.

Las futuras acciones de volumen, mute, iluminación o enfoque de ventanas pueden ser de bajo riesgo dentro de límites configurados.

Cerrar aplicaciones, modificar archivos, apagar equipos, realizar compras, acceder a información privada o ejecutar comandos arbitrarios requieren políticas distintas y no deben habilitarse en esta fase.

No permitas ejecución libre de código, PowerShell, shell o instrucciones generadas por el modelo.

No interpretes «tienes permiso para hacer cualquier cosa» como una autorización general.

## 14. Arquitectura de herramientas

Aunque todavía trabajaremos principalmente en simulación, quiero que el nuevo cerebro nazca orientado a herramientas reales.

Diseña un registro de capacidades sencillo y extensible.

Cada herramienta debería declarar:

- Identificador estable.
- Descripción.
- Parámetros admitidos.
- Tipo de recurso que controla.
- Operaciones de lectura disponibles.
- Operaciones de escritura disponibles.
- Nivel de riesgo.
- Requisitos de autorización.
- Disponibilidad.
- Resultado estructurado.
- Capacidad de verificar el resultado.
- Capacidad de revertirlo, cuando realmente sea posible.

Por ejemplo:

`system_audio.get_volume`

`system_audio.set_volume`

`system_audio.adjust_volume`

`system_audio.set_mute`

`applications.open`

`applications.focus`

`media.pause`

`media.next_track`

`lights.set_color`

`lights.set_brightness`

Estos nombres son ilustrativos. Puedes elegir nombres más consistentes con el diseño.

La interpretación no debe depender de un catálogo rígido de exactamente 19 intenciones.

Pero tampoco debe existir un mecanismo que permita a la IA inventar herramientas o ejecutarlas sin registro.

Las capacidades deben poder ampliarse sin modificar completamente el motor de comprensión.

Utiliza interfaces locales y APIs nativas antes que automatización visual cuando sean suficientes.

Para Windows, prioriza APIs apropiadas para audio, procesos, ventanas y sesiones multimedia.

Para dispositivos inteligentes, deja una capa de adaptadores intercambiables.

Más adelante se evaluarán integraciones directas, Home Assistant, MQTT u otros protocolos según los dispositivos reales.

No asumas que mis luces ofrecen una API local, ni instales un servidor de automatización doméstica completo sin demostrar que es necesario.

## 15. Verificación y respuestas del asistente

Jarvis debe diferenciar inequívocamente:

- Intención interpretada.
- Acción propuesta.
- Acción autorizada.
- Acción en ejecución.
- Acción completada.
- Resultado verificado.
- Error.
- Acción cancelada.

El modelo de lenguaje no puede confirmar que algo sucedió únicamente porque generó una respuesta.

La confirmación deberá proceder de un resultado de herramienta.

El código de Fase 3.1 contiene ejemplos de respuestas que afirman estados físicos inexistentes, como «Steam está arrancado», aunque no se haya ejecutado ninguna acción.

No quiero depender de una lista de expresiones regulares que intente detectar todas las formas posibles de afirmar una ejecución.

Diseña las respuestas de control principalmente a partir de resultados estructurados y plantillas fiables.

Ejemplos:

Simulación:

«En simulación, ajustaría el volumen al 30%.»

Ejecución verificada:

«Listo, volumen al 30%.»

Error:

«No pude cambiar el volumen.»

Estado desconocido:

«No puedo confirmar el estado de esa luz.»

La conversación libre puede mantenerse para preguntas sencillas, pero no debe presentar estados operativos no verificados como hechos.

Jarvis debe hablar poco cuando ejecuta acciones.

Prefiero una confirmación breve a explicaciones innecesarias.

No sintetices respuestas de una solicitud cancelada o reemplazada.

## 16. Sistema de voz: conservar, medir y sustituir si conviene

El reconocimiento de voz sigue siendo una limitación importante.

No atribuyas todos los fallos de comprensión al LLM.

Los informes de Fase 3.1 contienen errores acústicos importantes con estímulos sintéticos.

No representan todavía la precisión con mi voz real.

### Activación

Conserva Rustpotter inicialmente.

No cambies mi referencia personal de activación, micrófono o umbral sin una evaluación fundamentada.

La detección de Jarvis debe permanecer local.

No quiero enviar audio a internet continuamente.

### Reconocimiento STT

Mantén Moonshine como referencia, pero no lo consideres una decisión definitiva.

Diseña o aprovecha una interfaz que permita evaluar motores alternativos sin cambiar el resto del sistema.

Compara, cuando sea viable:

- Moonshine.
- Una configuración eficiente de faster-whisper o whisper.cpp.
- Otros motores locales multilingües que realmente sean adecuados para el hardware.
- Opcionalmente, transcripción remota bajo demanda.

No introduzcas cinco motores de voz permanentemente.

La evaluación debe decidir cuál merece permanecer.

La transcripción remota deberá requerir una habilitación explícita, porque implica enviar audio fuera del computador.

Si se prueba, deberá enviar únicamente las órdenes capturadas después de la activación, no un flujo de micrófono permanente.

No realices cargas de audio personal a servicios externos sin mi consentimiento.

### Pruebas de voz

Prioriza:

- Español natural.
- Nombres de aplicaciones.
- Steam, Spotify, Discord y Chrome.
- Colores.
- Números.
- Negaciones.
- Cancelaciones.
- Frases cortas.
- Correcciones de uno o dos términos.
- Órdenes compuestas.
- Referencias como «eso», «la otra», «más suave» y «como antes».
- Ruido ambiental y audio de videojuegos.

Mide tanto la calidad de transcripción como la conservación de elementos críticos.

Un error en una palabra secundaria no tiene la misma gravedad que perder un «no», modificar un número o confundir una aplicación.

No utilices sustituciones fonéticas indiscriminadas para convertir cualquier transcripción dudosa en una acción.

Si una transcripción es incierta, puede pedirse una aclaración dirigida.

Ejemplo:

«¿Te referías a Steam?».

### Detección del final de frase

Actualmente existe una espera de silencio de aproximadamente 1.200 ms.

Evalúa configuraciones alternativas únicamente si pueden medirse sin cortar pausas naturales.

No reduzcas arbitrariamente el tiempo para presentar una mejora artificial de latencia.

### Síntesis

Conserva Piper inicialmente.

Evita cargarlo permanentemente si el costo de preparación no lo justifica.

Evalúa confirmaciones breves, indicadores sonoros opcionales y reutilización temporal del trabajador de voz.

No introduzcas reproducción incremental compleja sin una mejora medible.

El sistema sigue siendo semidúplex salvo que se implemente y valide explícitamente una alternativa.

No afirmes que Jarvis escucha interrupciones habladas mientras reproduce audio si todavía no es cierto.

## 17. Gestión adaptativa de recursos

Este requisito tiene máxima prioridad.

Mi computador debe poder utilizarse normalmente, incluyendo videojuegos, mientras Jarvis permanece disponible.

No quiero mantener varios modelos pesados ocupando CPU, RAM o GPU en reposo.

Analiza el ciclo de vida actual y reutiliza los avances de las fases anteriores.

La arquitectura ideal debe separar:

- Residente ligero.
- Trabajador de reconocimiento de voz.
- Cliente de interpretación remota.
- Trabajador de síntesis.
- Herramientas locales cargadas cuando sean necesarias.

No crees procesos adicionales por principio si su coste supera el beneficio.

Mide antes de decidir.

### Reposo

En estado DORMANT deberían permanecer activos únicamente los componentes indispensables.

No deben ejecutarse:

- Inferencia de LLM.
- Embeddings.
- Transcripción continua.
- Síntesis.
- Consultas remotas periódicas de inteligencia.
- Observación continua costosa de aplicaciones.
- Bucles de consulta innecesarios.

No es necesario descargar todo de forma instantánea si una breve retención mejora considerablemente la experiencia de seguimiento.

Compara retención temporal frente a carga fría.

### Gaming

La configuración prioritaria será de bajo consumo.

No utilices GPU por defecto para modelos locales si puede interferir con el juego.

Si una configuración local acelerada por GPU demuestra ventajas y puede activarse de forma controlada, evalúala como alternativa, no como obligación.

No cambies automáticamente prioridades de procesos del sistema ni ajustes de rendimiento de otros programas sin autorización.

### Perfiles

Mantén o simplifica los perfiles existentes si aportan utilidad:

- Gaming.
- Equilibrado.
- Ahorro.

El nuevo perfil principal deberá funcionar sin Ollama ni E5.

No migres todo Jarvis a Rust, C++ u otro lenguaje solamente para reducir consumo teórico.

El residente actual ya tiene cifras prometedoras.

Solo considera una migración parcial a un ejecutable nativo si las mediciones demuestran que el runtime actual es un problema real.

## 18. Estado de Windows y dispositivos: preparar la siguiente etapa

Jarvis debe evolucionar de recordar conversaciones a conocer su contexto operativo.

Para ello, prepara interfaces de consulta de estado.

Ejemplos futuros:

- Volumen del dispositivo de salida.
- Sesión multimedia actual.
- Aplicación en primer plano.
- Aplicaciones abiertas.
- Dispositivo disponible.
- Estado de una luz.
- Escena activa.

Prioriza consultas bajo demanda y eventos del sistema cuando sean adecuados.

No incorpores vigilancia constante de pantalla, captura de imágenes, seguimiento de actividad personal o sondeos costosos.

Una petición como:

«Pausa la música».

Debe poder identificar el reproductor activo cuando exista una consulta fiable.

Una petición como:

«Bájale otro poquito».

Debe conservar el referente operativo pertinente.

Una petición como:

«Cuando termine de jugar, deja todo como estaba».

Debe distinguirse de una acción inmediata.

La programación de condiciones futuras podrá incorporarse después, cuando exista un mecanismo fiable para detectar el evento y gestionar estados anteriores.

No habilites automatizaciones diferidas inventando condiciones que el sistema todavía no puede observar.

## 19. Escenas, modos y personalización futura

La arquitectura debe facilitar rutinas como:

- Modo jugar.
- Modo estudiar.
- Modo película.
- Modo dormir.
- Modos definidos posteriormente por el usuario.

Una escena deberá representar un conjunto de acciones y configuraciones locales conocidas.

La IA interpretará la intención de activar la escena y las excepciones solicitadas.

Ejemplo:

«Activa el modo jugar, pero hoy no abras Discord y deja la música más suave».

El sistema deberá:

- Identificar el modo.
- Consultar su definición existente.
- Excluir Discord para esta solicitud.
- Ajustar la configuración de audio.
- Conservar las demás acciones.
- Validar individualmente el plan.

No debe inventar qué incluye un modo que nunca he configurado.

La modificación temporal de una escena no debe modificar automáticamente su configuración persistente.

Prepara los contratos necesarios, pero no amplíes excesivamente el alcance de esta fase implementando todas las escenas, dispositivos y preferencias.

## 20. Estrategia de desarrollo: construir una experiencia completa pequeña

Quiero evitar otro ciclo de desarrollo en el que aumenten las pruebas y las capacidades simuladas, pero todavía no pueda controlar ninguna función real.

La nueva fase se dividirá en etapas verificables.

### Etapa A — Base y decisiones

- Preservar la Fase 3.1.
- Auditar los componentes reutilizables.
- Documentar la nueva arquitectura.
- Definir contratos, interfaces y responsabilidades.
- Crear la nueva rama.
- Registrar una referencia de métricas actuales.

### Etapa B — Motor de inteligencia nuevo

- Ruta rápida mínima.
- Proveedor de interpretación intercambiable.
- Proveedor falso para pruebas.
- Integración remota experimental.
- Contrato estructurado.
- Comparación con Qwen.
- Desactivación inicial de E5.
- Funcionamiento sin Ollama obligatorio.

### Etapa C — Contexto y políticas

- Memoria operativa.
- Gestor central de decisiones.
- Correcciones y referencias.
- Operaciones explícitas sobre planes.
- Cancelaciones.
- Protección contra respuestas tardías.
- Validación de acciones y riesgos.
- Respuestas basadas en resultados.

### Etapa D — Validación textual y de voz

- Evaluación comparativa.
- Nuevos conjuntos reservados.
- Pruebas de seguridad.
- Diagnóstico por etapas.
- Comparación de STT cuando sea viable.
- Medición del reconocimiento con mi voz real cuando yo pueda realizar las pruebas físicas.
- Evaluación de consumo y latencia.

### Etapa E — Primera herramienta real candidata

Diseña una primera integración pequeña de volumen de Windows:

- Leer volumen actual.
- Establecer volumen.
- Ajustarlo relativamente.
- Consultar mute.
- Verificar resultado.

Es una capacidad adecuada para probar toda la arquitectura porque es observable y generalmente reversible.

No es necesario esperar a implementar todas las herramientas futuras para preparar esta primera integración.

Sin embargo, distingue claramente entre preparar el adaptador y habilitar su ejecución.

La implementación puede desarrollarse y probarse con adaptadores falsos.

No habilites acciones reales por defecto.

Antes de habilitar la primera acción física, exige superar las pruebas específicas de autorización, cancelación, parámetros y contexto, y solicita mi aprobación explícita.

Si se habilita posteriormente, deberá hacerse mediante una configuración experimental claramente identificada, limitada exclusivamente a las herramientas aprobadas.

No habilites aún apertura o cierre de aplicaciones, control general de dispositivos ni otras acciones reales como parte de una aprobación para volumen.

## 21. Evaluación comparativa de proveedores

No selecciones una API únicamente por el tamaño del modelo o porque su proveedor afirma tener baja latencia.

Quiero una evaluación comparativa reproducible.

Utiliza las mismas solicitudes, contexto, catálogo y condiciones para comparar:

- Arquitectura de Fase 3.1 como referencia.
- Nuevo intérprete local directo.
- Nuevo intérprete remoto.
- Proveedor local opcional, si aporta valor.
- Configuraciones con y sin E5, cuando sea pertinente.

La comparación deberá separar:

### Calidad del modelo

Qué tan correctamente interpreta una transcripción y el contexto.

### Calidad del router

Si selecciona la ruta adecuada o trata una orden como conversación.

### Calidad del validador

Si acepta propuestas válidas y rechaza las indebidas.

### Calidad de la aplicación contextual

Si modifica correctamente planes y referentes.

### Resultado final

Si la solicitud obtiene la acción esperada, la aclaración apropiada o la abstención necesaria.

No atribuyas automáticamente al modelo una decisión que fue rechazada por la política local.

No contabilices un JSON válido como una interpretación correcta si su contenido no coincide con la solicitud.

### Casos de evaluación

Incluye:

- Órdenes directas.
- Variaciones naturales.
- Expresiones coloquiales.
- Instrucciones indirectas.
- Negaciones.
- Solicitudes futuras.
- Citas.
- Preguntas.
- Correcciones.
- Referencias a acciones anteriores.
- Solicitudes compuestas.
- Exclusiones.
- Cambios de objetivo.
- Valores numéricos.
- Ambigüedades.
- Cancelaciones.
- Estados desconocidos.
- Respuestas tardías.
- Fallos de proveedores.

Añade ejemplos que reflejen mi uso real de Jarvis: jugar, escuchar música, controlar aplicaciones y cambiar iluminación.

No concentres la evaluación en conversación general.

Los corpus de Fase 3.1 que ya conocemos deben utilizarse como regresión y diagnóstico.

Para evaluar generalización, prepara casos nuevos después de congelar la implementación correspondiente.

No utilices los fallos de un conjunto reservado para modificar el motor y luego vuelvas a presentar ese mismo conjunto como evaluación independiente.

Conserva resultados fallidos y registra las limitaciones de la autoría y metodología.

### Cuotas y comparación remota

Evita desperdiciar solicitudes gratuitas mediante evaluaciones redundantes.

Puedes comenzar con un conjunto piloto de aproximadamente 30–50 turnos de alto valor, ampliarlo después y separar las pruebas de desarrollo de las reservadas.

Si no existe una clave configurada, deja el evaluador preparado y utiliza proveedores simulados para comprobar su funcionamiento.

No inventes latencias, precisión o resultados reales del proveedor.

## 22. Métricas y criterios de aceptación

Quiero que el progreso se mida por resultados prácticos.

### Comprensión

Objetivos iniciales de diseño:

- Clasificación general igual o superior al 95%.
- Recuperación de acciones válidas igual o superior al 95%.
- Exactitud de parámetros igual o superior al 95%.
- Comprensión contextual igual o superior a la referencia de Fase 3.1 en pruebas comparables, complementadas con casos más exigentes.
- Reducción de aclaraciones innecesarias.
- Cero afirmaciones falsas de ejecuciones o estados físicos en los casos evaluados.

Estos son objetivos propuestos, no resultados que debas declarar aprobados sin evidencia.

Si no se alcanzan, documenta la causa y la decisión correspondiente.

### Seguridad

Exige:

- Cero acciones indebidas en el conjunto crítico nuevo.
- Cero autorizaciones indebidas provocadas mediante propuestas forzadas contra las políticas.
- Cancelaciones efectivas.
- Protección contra resultados tardíos.
- Validación estricta de parámetros y herramientas.
- Conservación de las garantías relevantes de Fase 3.1.

No presentes estos resultados como garantía de seguridad universal.

Las pruebas deben intentar manipular también las respuestas del proveedor, los identificadores contextuales, las revisiones y los resultados de herramientas.

### Latencia

Mide por separado:

- Activación.
- Detección del final de frase.
- STT.
- Selección de ruta.
- Construcción del contexto.
- Petición remota.
- Validación.
- Aplicación de la decisión.
- Ejecución cuando esté habilitada.
- Verificación.
- Preparación de Piper.
- Tiempo hasta el inicio de la respuesta.

Registra medianas, p95, errores y timeouts.

Distingue cargas frías de preparadas.

No informes solamente el tiempo hasta el primer token.

Para Jarvis importa el momento en que existe una decisión completa y autorizable.

Objetivos iniciales:

- Interpretación local directa prácticamente inmediata una vez disponible la transcripción.
- Aproximarse a 1,5 segundos desde el final de la orden hasta el inicio de confirmación en órdenes directas, si la cadena de voz lo permite.
- Aproximarse a 3 segundos en muchas órdenes contextuales con proveedor remoto.
- Reducir claramente la mediana de integración completa respecto a los 6,94 segundos observados.

No sacrifiques precisión o seguridad para alcanzar estas metas.

### Recursos

Mide:

- CPU media y picos en reposo.
- RSS del árbol residente.
- Memoria de trabajadores por separado.
- Memoria del proveedor local, si existe.
- GPU y VRAM cuando sean relevantes.
- CPU durante STT, interpretación y TTS.
- Tiempo de liberación de recursos.
- Crecimiento sostenido de memoria.
- Consumo durante sesiones consecutivas.

Utiliza como referencia inicial la CPU media del 0,365% y el RSS pico de 89,3 MB de Fase 3.1.

La medición breve existente no debe presentarse como un objetivo ya demostrado durante horas.

Quiero mantener o mejorar esas cifras en reposo.

Además, realiza pruebas de estabilidad prolongada cuando el entorno lo permita.

### Videojuegos

Prepara un procedimiento para comparar:

- Juego sin Jarvis.
- Juego con Jarvis en reposo.
- Juego durante activación.
- Juego durante STT.
- Juego durante interpretación remota.
- Juego durante síntesis.
- Juego durante inferencia local, si todavía existe.

Mide FPS, frametime y consumo mediante condiciones comparables.

Si no puedes realizar estas mediciones sin mi participación, identifícalas como pendientes físicas.

No simules resultados de videojuegos.

## 23. Pruebas físicas y diagnóstico

Las pruebas automáticas no sustituyen mi experiencia utilizando Jarvis.

Conserva la guía física de Fase 3.1 como referencia y adáptala a Jarvis Next.

Prepara un procedimiento sencillo que me permita:

1. Activar Jarvis.
2. Dar instrucciones.
3. Observar qué transcribió.
4. Observar qué interpretación produjo.
5. Identificar si se equivocó el STT, el router, el modelo, el contexto o el validador.
6. Medir aproximadamente la demora.
7. Registrar errores voluntariamente.

Mantén la privacidad por defecto.

No guardes audio ni conversaciones completas de manera automática.

Permite informes locales optativos y redactados cuando sean necesarios.

Crea un conjunto corto de pruebas físicas prioritarias para que no tenga que realizar cientos de ejercicios manuales.

Incluye especialmente:

- «Abre Steam».
- «No, mejor Spotify».
- «Olvida todo lo anterior».
- «Pon las luces rojas».
- «Mejor azules».
- «Y un poco más suaves».
- «No hagas nada todavía».
- «Prepara el computador para jugar, pero no abras Discord».
- «La música está muy fuerte».
- «Un poquito más bajo».
- «Cancela».

Adapta las expectativas según las capacidades que estén realmente disponibles.

No consideres una prueba aprobada si Jarvis solamente respondió de manera convincente, pero interpretó incorrectamente la acción.

## 24. Estrategia de pruebas y CI

Conserva las 379 pruebas existentes como referencia importante, pero no conviertas cada implementación antigua en una restricción permanente.

Si un contrato se reemplaza, adapta las pruebas a la nueva arquitectura manteniendo el comportamiento y las garantías que realmente importan.

No elimines pruebas porque revelen un problema.

Si una prueba deja de ser aplicable:

- Explica por qué.
- Identifica qué garantía protegía.
- Sustitúyela por una prueba equivalente cuando la garantía siga siendo relevante.
- Conserva el historial y la evidencia anterior.

Añade pruebas de:

- Proveedores remotos simulados.
- Contratos.
- Esquemas inválidos.
- Fallos de conexión.
- Timeout.
- Cuotas.
- Cancelación.
- Concurrencia.
- Revisiones.
- Identificadores inventados.
- Planes parcialmente modificados.
- Contexto expirado.
- Confirmaciones reutilizadas.
- Estados desconocidos.
- Resultados falsos.
- Privacidad y ausencia de filtración de credenciales.
- Funcionamiento sin Ollama.
- Funcionamiento sin E5.
- Degradación offline.
- Liberación de recursos.

El CI normal debe seguir funcionando sin API keys, sin consumir cuotas externas y sin descargar modelos grandes.

Separa las pruebas externas y físicas de las pruebas automatizadas reproducibles.

No añadas secretos de producción al CI público.

## 25. Lo que NO quiero en esta fase

No quiero:

- Una reconstrucción total innecesaria de las fases 1 y 2.
- Un chatbot general como objetivo principal.
- Un sistema enorme de agentes autónomos.
- Un LLM ejecutando libremente comandos.
- Dependencia obligatoria de Ollama.
- E5 cargado por defecto sin evidencia de utilidad.
- Varias APIs consultadas consecutivamente para cada orden.
- Una base vectorial de memoria innecesaria.
- Un framework pesado de agentes si una interfaz sencilla resuelve el problema.
- Vigilancia permanente de pantalla.
- Grabación continua de audio.
- Facturación automática.
- Modelos locales consumiendo recursos en reposo.
- Incorporación prematura de una interfaz gráfica compleja.
- Automatización de todas las aplicaciones y dispositivos antes de validar una experiencia pequeña.
- Un aumento artificial de pruebas que oculte problemas prácticos.
- Afirmaciones de precisión, seguridad o latencia sin mediciones.
- Conservar código innecesario por miedo a perder avances.

Prefiero una arquitectura pequeña, comprensible y medible.

## 26. Documentación y entregables

Actualiza la documentación para reflejar la nueva dirección.

Crea un documento de arquitectura que explique:

- Qué se conservó.
- Qué se eliminó.
- Qué se reconstruyó.
- Qué responsabilidades tiene cada componente.
- Cómo fluye una orden directa.
- Cómo fluye una orden contextual.
- Cómo funcionan el contexto, la seguridad y los planes.
- Cómo se selecciona un proveedor.
- Qué ocurre si internet falla.
- Qué recursos permanecen activos en reposo.
- Cómo añadir herramientas futuras.
- Cómo regresar a la versión anterior.

Documenta también:

- Configuración de API.
- Configuración offline.
- Gestión de secretos.
- Procedimiento de evaluación.
- Pruebas de voz.
- Perfiles de consumo.
- Limitaciones pendientes.
- Cambios de dependencias.
- Instrucciones para ejecutar Jarvis Next.

Al terminar el trabajo, quiero un informe final con una tabla que contenga:

Componente | Estado anterior | Cambio realizado | Motivo | Evidencia | Estado final

Incluye además:

- Commit y rama.
- Resultados de CI.
- Resultados locales.
- Métricas comparativas.
- Resultados remotos realmente medidos.
- Consumo medido.
- Problemas encontrados.
- Decisiones arquitectónicas.
- Componentes retirados.
- Regresiones.
- Pruebas físicas pendientes.
- Capacidades disponibles.
- Capacidades todavía simuladas.
- Próximos pasos recomendados.

No cierres una etapa declarando que todo está listo si siguen existiendo bloqueos relevantes.

## 27. Forma de trabajo

Tienes libertad para tomar decisiones técnicas y simplificar el proyecto.

Antes de incorporar una dependencia nueva, pregúntate:

- ¿Qué problema real resuelve?
- ¿Puede resolverse con componentes existentes?
- ¿Cuánta memoria añade?
- ¿Cuánto aumenta la latencia?
- ¿Qué ocurre cuando falla?
- ¿Complica el mantenimiento?
- ¿Se utilizará realmente en mi experiencia diaria?

Si una implementación anterior ya no es adecuada, puedes reemplazarla completamente.

Prefiero una implementación nueva y sencilla a una adaptación extremadamente compleja de código obsoleto.

Sin embargo, conserva las garantías de seguridad y funcionamiento demostradas.

Trabaja mediante commits coherentes y verificables.

No mezcles indiscriminadamente cambios de arquitectura, voz, configuración y ejecución física en un solo commit.

Realiza primero una auditoría breve y un plan de implementación, pero no te limites a responder con un plan teórico.

Continúa con los cambios, las pruebas y la documentación que puedas realizar en el entorno disponible.

Si una parte requiere mis credenciales, mi voz, acceso físico al computador o pruebas durante videojuegos, deja preparada la infraestructura y explica exactamente qué debo hacer.

No detengas todo el desarrollo por una dependencia que pueda aislarse mediante adaptadores o pruebas simuladas.

No inventes los resultados pendientes.

## 28. Condición final de éxito

Consideraré que Jarvis Next representa una mejora real cuando pueda demostrar que:

1. El residente sigue siendo ligero y estable.
2. Jarvis comprende mejor instrucciones naturales.
3. Mantiene referencias y contexto operativo correctamente.
4. No necesita modelos LLM locales pesados para su funcionamiento principal.
5. Utiliza la API solamente cuando aporta valor.
6. Las órdenes directas siguen funcionando offline.
7. La latencia de la experiencia completa disminuye.
8. Las cancelaciones y las políticas de seguridad funcionan independientemente del intérprete.
9. Las respuestas no inventan ejecuciones.
10. La arquitectura permite incorporar herramientas reales de forma segura y sencilla.

La meta no consiste en conservar Qwen, Moonshine, E5, Groq o cualquier tecnología concreta.

La meta consiste en conseguir el mejor resultado posible para Jarvis.

**Si debemos eliminar o reconstruir parte del trabajo anterior para lograrlo, hazlo.**

**Si un componente funciona bien y no perjudica la arquitectura, reutilízalo.**

**Si una tecnología nueva no demuestra aportar valor, descártala.**

A partir de ahora, todas las decisiones deben alinearse con esta filosofía:

Jarvis permanece disponible, escucha cuando lo llamo, comprende lo que quiero, realiza acciones autorizadas, confirma sus resultados y vuelve a un estado de consumo mínimo.

Comienza la Fase 3.2 — Jarvis Next.