# PROYECTO JARVIS
## DOCUMENTO MAESTRO DE DESARROLLO — FASE 3.1
### Estabilización, seguridad, comprensión contextual, integración de voz y optimización
**Versión 3.1 — Instrucciones técnicas para Codex**

---

# 0. INSTRUCCIÓN PRINCIPAL PARA CODEX

Actúa como arquitecto principal de software, ingeniero de sistemas de inteligencia artificial local, especialista en procesamiento de lenguaje natural y auditor técnico de aplicaciones residentes de Windows.

Vamos a desarrollar **JARVIS FASE 3.1 — INTELLIGENCE HARDENING & OPTIMIZATION**.

Esta fase es una continuación directa del proyecto existente en GitHub:

**Repositorio:** `SebastianJimenezPo/Jarvis`

**Rama actual:** `phase-3-intelligence`

**Commit de referencia:** `fed3f113455c6e867283b4959a5f21bdd0c35d4b`

La Fase 3 ya incorpora un sistema híbrido de comprensión mediante reglas, E5 y Qwen3, contexto conversacional, aclaraciones y propuestas simuladas.

El objetivo de la Fase 3.1 no es añadir más capacidades, sino **conseguir que todo lo implementado sea fiable, consistente, rápido, eficiente y suficientemente seguro para conectar herramientas reales en la siguiente fase**.

Las revisiones del código y los informes de integración identificaron problemas concretos que debemos analizar y corregir.

Tu trabajo será:

1. Auditar los problemas identificados.
2. Reproducirlos mediante pruebas cuando sea posible.
3. Determinar su causa técnica.
4. Implementar correcciones pequeñas y verificables.
5. Reforzar la seguridad del motor de decisiones.
6. Mejorar la consistencia de contexto y propuestas.
7. Mejorar la tolerancia a errores de transcripción.
8. Optimizar latencia y consumo.
9. Construir una evaluación independiente.
10. Realizar pruebas de regresión e integración.
11. Documentar las modificaciones.
12. Guardar cada conjunto de cambios terminado en Git y publicarlo en GitHub.

**No implementes todavía la Fase 4.**

Todas las acciones deben seguir siendo simuladas.

No habilites ningún mecanismo que abra aplicaciones, cambie volumen, controle luces, cierre procesos o ejecute comandos reales como consecuencia de una petición interpretada por Jarvis.

La prioridad es preparar el cerebro para actuar correctamente, no comenzar a actuar prematuramente.

---

# 1. FILOSOFÍA DE ESTA FASE

Jarvis debe ser un asistente que comprende lo que el usuario realmente quiere expresar.

No debe depender de que el usuario recuerde una frase exacta.

Pero tampoco debe asumir que toda frase relacionada con una acción constituye una orden.

Por ejemplo:

«Apaga las luces».

«No apagues las luces».

«Cuando termine de jugar, apaga las luces».

«Al acabar la partida, apaga las luces».

«¿Qué pasaría si apagara las luces?».

«Estaba pensando en apagar las luces».

«Apaga las luces, pero espera, mejor no».

Estas frases comparten vocabulario, pero tienen significados operativos diferentes.

**Jarvis debe interpretar la intención completa antes de decidir qué acción proponer.**

La seguridad no debe depender únicamente de un prompt del LLM.

La flexibilidad no debe conseguirse eliminando validaciones.

La velocidad no debe conseguirse aceptando interpretaciones dudosas.

El consumo reducido no debe conseguirse haciendo que cada conversación resulte excesivamente lenta.

El objetivo es encontrar un equilibrio medible entre estos factores.

## Principios de trabajo

**Primero reproducir, después modificar.**

No cambies código porque algo parezca sospechoso. Crea primero una prueba que permita identificar el comportamiento, salvo que se trate de una vulnerabilidad evidente cuya prueba requiera un tratamiento especial.

**No arreglar una frase rompiendo otras.**

Una regla añadida para comprender «al acabar la partida» no debe impedir entender «abre Steam cuando yo te lo diga» como una solicitud condicionada.

**No inventar intención a partir de una transcripción defectuosa.**

Cuando el reconocimiento produzca una frase incompleta o incoherente, Jarvis debe recuperar la información cuando sea posible y solicitar aclaración cuando no lo sea.

**La memoria no es una lista de mensajes.**

La memoria contextual debe representar correctamente entidades, propuestas, modificaciones y condiciones.

**La inteligencia generativa es una herramienta, no el centro obligatorio de todas las solicitudes.**

Las expresiones inequívocas deben conservar su ruta rápida.

**Sin comprometer las fases anteriores.**

La escucha residente, el reconocimiento, la síntesis y la gestión de sesiones deben seguir funcionando.

---

# 2. ESTADO ACTUAL DEL PROYECTO

La implementación disponible incluye:

- Rustpotter para activación.
- Captura única de micrófono.
- Moonshine para transcripción.
- Faster-whisper como alternativa.
- Silero VAD.
- Piper TTS.
- Conversaciones por turnos.
- Ruta rápida de interpretación.
- Ruta semántica mediante E5.
- Qwen3 mediante Ollama local.
- Memoria contextual temporal.
- Validación independiente de intenciones.
- Catálogo simulado de 19 acciones.
- Control de recursos.
- Gestión de errores.
- Registros y diagnósticos.

La última validación reporta:

- 218 pruebas automatizadas aprobadas.
- 328 casos escritos y 363 turnos evaluados.
- Reducción de memoria del proceso Python en una comparación controlada.
- Menor consumo medio de CPU en inferencias con dos hilos, acompañado de mayor tiempo de respuesta.
- Integraciones de voz que han funcionado parcialmente.
- Errores de reconocimiento en algunas frases cortas.
- Dificultades ocasionales con la activación.
- Una secuencia de luces que no superó la última integración sintética completa.

Las pruebas existentes demuestran comportamientos relevantes, pero los conjuntos revisados no constituyen evidencia independiente de precisión general.

**La Fase 3.1 debe resolver estas observaciones sin ocultar los fallos históricos.**

---

# 3. AUDITORÍA OBLIGATORIA DEL REPOSITORIO

Antes de modificar cualquier archivo:

1. Confirma la rama actual.
2. Confirma el HEAD y su relación con `fed3f11`.
3. Examina los commits posteriores, si existen.
4. Comprueba que no hay cambios locales sin guardar.
5. Lee `AGENTS.md`.
6. Lee `README.md`.
7. Lee `docs/phase_3_feedback.md`.
8. Lee `docs/intelligence_architecture.md`.
9. Lee `docs/intelligence_validation.md`.
10. Lee `docs/model_comparison.md`.
11. Examina los informes de integración de voz.
12. Ejecuta las pruebas actuales y guarda los resultados.

Presta especial atención a estos archivos:

```text
jarvis/intelligence/language.py
jarvis/intelligence/fast_path.py
jarvis/intelligence/safety.py
jarvis/intelligence/context.py
jarvis/intelligence/dialogue_manager.py
jarvis/intelligence/contracts.py
jarvis/intelligence/catalog.py
jarvis/intelligence/semantic.py
jarvis/intelligence/ollama_client.py
jarvis/intelligence/provider.py
jarvis/intelligence/responses.py

jarvis/speech/worker.py
jarvis/core/voice_session.py

tests/test_intelligence.py
tests/test_intelligence_safety.py
tests/test_intelligence_integration.py
tests/test_phase3_user_feedback.py
```

No des por hecho que estos archivos siguen idénticos al commit de referencia.

Utiliza el código realmente presente en el repositorio.

## 3.1. Rama de desarrollo

Crea una rama nueva:

`phase-3-1-hardening`

Conserva íntegramente `phase-3-intelligence`.

No reescribas el historial ni utilices `force-push`.

Realiza commits descriptivos por conjuntos de cambios comprobados.

Al terminar, deja un informe que permita identificar exactamente qué modificaciones pertenecen a esta fase.

---

# 4. PROBLEMA CRÍTICO 1 — TEMPORALIDAD Y CONDICIONES FUTURAS

## 4.1. Problema identificado

En la implementación revisada de `language.py`, la función `clause_kind()` reconoce determinadas expresiones temporales mediante patrones regulares.

Por ejemplo:

- «cuando».
- «mañana».
- «después».
- «al terminar».
- «más tarde».

Sin embargo, hay expresiones equivalentes que podrían no reconocerse.

Un caso especialmente importante es:

**«Apaga las luces al acabar la partida».**

La implementación anterior puede identificar el verbo «apaga» y proponer una acción inmediata porque «al acabar» no está necesariamente cubierta por las reglas actuales.

Esta posibilidad debe reproducirse mediante una prueba real del código.

## 4.2. Comportamiento correcto

Las siguientes expresiones deben identificarse como solicitudes futuras o condicionadas:

- «Apaga las luces al acabar la partida».
- «Apaga las luces cuando termine de jugar».
- «Una vez termine el juego, apaga las luces».
- «Al finalizar la canción, baja el volumen».
- «Después de cerrar Steam, apaga las luces».
- «En cuanto termine la película, apaga la iluminación».
- «Si algún día vuelvo a jugar, activa ese modo».
- «Solo cuando te lo diga, abre Chrome».
- «No hagas nada hasta que termine».
- «Cuando llegue el momento, abre Spotify».

No deben convertirse automáticamente en acciones inmediatas.

## 4.3. Solución esperada

No quiero que solamente agregues unas cuantas palabras a una expresión regular y declares el problema resuelto.

Implementa una estrategia de análisis que distinga:

- Peticiones inmediatas.
- Peticiones diferidas.
- Condiciones previas.
- Condiciones posteriores.
- Referencias temporales.
- Hipótesis.
- Comentarios sobre acciones pasadas.
- Negaciones.

Separa el análisis lingüístico de la validación de autorización.

Si una construcción no puede clasificarse con suficiente seguridad, el sistema debe abstenerse de proponer ejecución inmediata.

No rechaces automáticamente cualquier frase que contenga una palabra temporal si su significado completo no es diferido.

Por ejemplo:

«Abre la aplicación que usé ayer».

Puede constituir una petición inmediata con una referencia al pasado, aunque necesite aclaración sobre la aplicación.

## 4.4. Pruebas obligatorias

Construye pares contrastivos donde una modificación mínima cambie el significado.

Ejemplo:

```text
Apaga las luces.
Apaga las luces al acabar la partida.

Abre Steam.
Abre Steam cuando termine de estudiar.

Baja el volumen.
No bajes el volumen.

Pon las luces azules.
Si pudiera, pondría las luces azules.
```

La clasificación debe reflejar correctamente cada diferencia.

**Criterio de aceptación:** ninguna solicitud futura o condicionada del conjunto crítico puede producir una propuesta autorizada como inmediata.

---

# 5. PROBLEMA CRÍTICO 2 — VALIDACIÓN DE CORRECCIONES CONTEXTUALES

## 5.1. Problema identificado

En `safety.py`, existe un tratamiento especial para resultados de la ruta rápida que tengan determinados `reason_code`, como:

- `context_correction`
- `clarification_resolved`

En esos casos se omiten algunas verificaciones de evidencia lingüística.

El objetivo original es permitir expresiones cortas como:

«Mejor azul».

Eso es razonable, porque el contexto proporciona el dispositivo y la intención.

Sin embargo, **una corrección contextual no debe tener autorización implícita para evitar comprobaciones de negación, condiciones o alcance**.

## 5.2. Caso que debes investigar

Secuencia:

Usuario:

«Pon las luces rojas».

Después:

«No, mejor azules, pero no hagas nada».

El sistema no debe autorizar una nueva propuesta inmediata de cambio de color sin considerar la prohibición explícita de realizar la acción.

Otros casos:

- «Mejor azul cuando termine».
- «Mejor azul, pero no ahora».
- «No, mejor azul, aunque todavía no lo cambies».
- «Déjalo en rojo, no lo cambies».
- «Si es posible después, mejor azul».
- «No era una orden, solo estaba preguntando».

## 5.3. Nueva regla de validación

Toda propuesta debe superar las comprobaciones de autorización.

Eso incluye:

- Solicitudes directas.
- Resultados semánticos.
- Resultados del LLM.
- Correcciones.
- Aclaraciones resueltas.

La procedencia de la propuesta no debe sustituir su validación.

Sin embargo, tampoco debemos exigir que una corrección corta repita toda la solicitud original.

La validación debe poder combinar:

**Evidencia de la frase actual + contexto anterior válido + tipo de modificación solicitada.**

Por ejemplo:

Frase actual: «Mejor azul».

Contexto válido: propuesta de cambiar la luz principal a rojo.

Modificación autorizada: reemplazar `color=red` por `color=blue`.

No es necesario que el usuario vuelva a decir «luz principal».

## 5.4. Procedencia de los parámetros

Diseña, si resulta útil, una estructura que indique la procedencia de cada parámetro:

- `explicit_current_turn`
- `resolved_from_context`
- `confirmed_by_clarification`
- `default_configured`

No utilices un campo de procedencia como autorización automática.

La finalidad es permitir validación y diagnóstico.

## 5.5. Evitar excepciones excesivas

Refactoriza la lógica actual para que las correcciones puedan validar su evidencia contextual sin saltarse las comprobaciones esenciales.

Las comprobaciones de negación y temporalidad deben aplicarse siempre al significado completo de la intervención.

**Criterio de aceptación:** ninguna corrección puede generar una propuesta inmediata cuando el usuario explícitamente prohíbe o pospone esa acción.

---

# 6. PROBLEMA CRÍTICO 3 — CAMBIOS DE CONTEXTO ANTES DE VALIDAR

## 6.1. Riesgo identificado

Revisa el recorrido actual de:

`DialogueManager.interpret()`

y las funciones de:

`FastPath`

`ContextManager`

Algunas operaciones de la ruta rápida pueden modificar el contexto mientras todavía se está interpretando la frase.

Por ejemplo:

- Crear una aclaración pendiente.
- Eliminar una aclaración.
- Registrar una preferencia temporal.
- Limpiar el contexto.
- Modificar propuestas.

Estas modificaciones pueden ocurrir antes de que finalicen todas las verificaciones o antes de comprobar que la sesión sigue siendo válida.

Esto debe auditarse cuidadosamente.

## 6.2. Objetivo

**La interpretación no debe producir cambios definitivos en el contexto hasta que la decisión haya sido validada y siga perteneciendo a la sesión correcta.**

Propongo separar conceptualmente:

1. Lectura del contexto.
2. Interpretación.
3. Propuesta de modificación del contexto.
4. Validación.
5. Verificación de sesión y turno.
6. Confirmación de los cambios.

## 6.3. Actualización atómica

Una corrección debe aplicarse como una operación coherente.

Por ejemplo:

Estado inicial:

```json
{
  "target": "main_light",
  "intent": "set_light_color",
  "color": "red"
}
```

Frase:

«No, mejor azul».

Nuevo estado:

```json
{
  "target": "main_light",
  "intent": "set_light_color",
  "color": "blue"
}
```

La operación no debe dejar simultáneamente dos versiones contradictorias de la misma propuesta.

Si la validación falla, el estado anterior debe conservarse o modificarse únicamente conforme a una regla explícita y segura.

## 6.4. Respuestas tardías

Prueba el caso en que:

1. Se recibe una frase.
2. Se inicia una interpretación con Qwen.
3. La sesión termina.
4. Se crea una nueva sesión.
5. Llega el resultado de la primera interpretación.

Ese resultado no debe modificar el contexto nuevo.

Tampoco debe provocar una respuesta de Piper.

Incluye pruebas con tareas canceladas y resultados que llegan fuera de orden.

## 6.5. Implementación

Puedes utilizar una copia temporal del contexto, un mecanismo de revisión/versión o una operación de commit de estado.

Selecciona la alternativa más sencilla y segura para la arquitectura existente.

No conviertas esta corrección en un sistema de transacciones excesivamente complejo.

**Criterio de aceptación:** una interpretación rechazada, cancelada o caducada no puede dejar cambios inesperados en el estado conversacional.

---

# 7. PROBLEMA 4 — CANCELACIONES Y ACLARACIONES PENDIENTES

## 7.1. Problema

En `fast_path.py`, una frase clasificada como negación puede provocar que se elimine una aclaración pendiente.

Pero una negación no siempre significa cancelar.

Ejemplo:

Jarvis:

«¿Qué aplicación quieres abrir?».

Usuario:

«No canceles».

Esta frase no debería eliminar necesariamente la aclaración.

Otros ejemplos:

- «No, esa no».
- «No era Chrome».
- «No quiero cancelar».
- «Todavía no».
- «Espera».
- «Cancela».
- «Olvida todo».
- «No hagas nada».

Estas expresiones deben interpretarse según el estado de la conversación.

## 7.2. Diferencias necesarias

Distingue:

**Cancelación explícita**

El usuario quiere abandonar una propuesta o solicitud pendiente.

**Rechazo de alternativa**

El usuario rechaza un candidato sin necesariamente cancelar la solicitud completa.

**Corrección**

El usuario reemplaza información anterior.

**Nueva solicitud**

El usuario abandona implícitamente una aclaración para comenzar otra acción independiente.

**Solicitud de mantener pendiente**

El usuario indica que todavía no quiere cancelar.

## 7.3. Pruebas obligatorias

Prueba secuencias como:

```text
Jarvis: ¿Qué aplicación?
Usuario: Steam.
```

```text
Jarvis: ¿Qué aplicación?
Usuario: Cancela.
```

```text
Jarvis: ¿Chrome o Spotify?
Usuario: No, ninguna.
```

```text
Jarvis: ¿Chrome o Spotify?
Usuario: No quiero cancelar, abre Spotify.
```

```text
Jarvis: ¿Qué color?
Usuario: Mejor no cambies nada.
```

```text
Jarvis: ¿Qué color?
Usuario: Azul.
Usuario: No, verde.
```

Cada resultado debe ser coherente con el contexto.

## 7.4. Cancelación mientras Jarvis habla

Conserva el comportamiento semidúplex de Fase 2.

No prometas interrupciones por voz durante la reproducción si todavía no están implementadas.

La cancelación mediante bandeja debe seguir disponible.

No amplíes el alcance hacia full-duplex.

---

# 8. PROBLEMA 5 — CONSERVACIÓN Y CORRECCIÓN DE PLANES

La memoria contextual actual conserva propuestas simuladas.

Para la Fase 4 necesitamos una representación más explícita de los cambios entre turnos.

## 8.1. Situación actual

Una orden puede generar varias propuestas.

Ejemplo:

«Abre Steam y pon las luces rojas».

Después:

«Mejor azules».

La corrección debe modificar exclusivamente el color de las luces.

Steam debe permanecer en el plan si ambas acciones continúan formando parte de una solicitud pendiente.

## 8.2. No confundir nuevos turnos con reemplazos

Hay tres operaciones distintas:

**Agregar una acción**

«Y baja el volumen».

**Modificar una acción**

«No, mejor las luces azules».

**Reemplazar todo el plan**

«Olvida eso. Mejor abre Chrome».

No deben utilizar exactamente la misma operación interna.

## 8.3. Modelo de plan

Diseña una representación acotada con:

- Identificador del plan.
- Identificador de acción.
- Intención.
- Destino.
- Parámetros.
- Estado de la propuesta.
- Fuente contextual.
- Número de revisión.
- Información de dependencias cuando corresponda.

Durante esta fase, los estados de ejecución física no existirán realmente.

Puedes distinguir como mínimo:

- Propuesto.
- Pendiente de aclaración.
- Validado.
- Reemplazado.
- Cancelado.

Las futuras acciones ejecutadas necesitarán otros estados, pero no implementes todavía el ejecutor real.

## 8.4. Correcciones de parámetros

Prueba:

«Pon las luces rojas».

«Mejor azules».

«Y el brillo al veinte».

«No, al treinta».

Resultado esperado:

Un plan coherente con la luz principal en azul y brillo propuesto del 30 %.

## 8.5. Ambigüedad

Prueba:

«Abre Chrome y Spotify».

«Ciérralo».

Jarvis no debe elegir arbitrariamente una aplicación.

Debe preguntar cuál.

También prueba:

«Abre Chrome y Spotify».

«Cierra Spotify».

La segunda solicitud sí está determinada.

## 8.6. Restricciones

No utilices propuestas simuladas como prueba de un estado físico.

Si el usuario dice:

«Déjalas como estaban».

Jarvis debe saber si dispone de información suficiente para determinar el estado previo.

Si no existe una observación física válida, debe aclarar.

**Criterio de aceptación:** las correcciones conservan las partes compatibles de un plan, eliminan contradicciones y nunca inventan estados físicos.

---

# 9. PROBLEMA 6 — NORMALIZACIÓN DE LENGUAJE Y NÚMEROS

La Fase 3 ya corrigió errores relacionados con puntuación, cortesía, números negativos y «ciento veinte».

No quiero reemplazar esa implementación sin razón.

Pero debemos ampliar las pruebas para detectar casos semejantes.

## 9.1. Separación de representaciones

Conserva:

**Texto original del STT.**

**Texto normalizado para coincidencias.**

**Estructura interpretada.**

No reemplaces el texto original por una normalización destructiva.

La normalización debe ser útil para la comparación y preservar la información semántica importante.

## 9.2. Puntuación

Prueba:

- «Por favor, pon las luces azules».
- «Por favor pon las luces azules».
- «Pon las luces azules, por favor».
- «No, mejor azul».
- «No mejor azul».
- «Abre Chrome, pero no Spotify».
- «Espera, no hagas eso».

No elimines todas las comas sin considerar cómo afectan la segmentación de cláusulas.

## 9.3. Números

Prueba como mínimo:

- «Volumen al veinte».
- «Volumen al veinticinco».
- «Volumen al treinta y cinco».
- «Volumen al cien».
- «Volumen al ciento veinte».
- «Volumen al menos diez».
- «Baja el volumen en diez».
- «Baja el volumen al diez».
- «Baja el volumen diez puntos».
- «Sube cinco por ciento».
- «No lo pongas al cincuenta».

La conversión numérica y la validación del parámetro deben ser independientes.

Un número correctamente reconocido no implica que sea válido.

## 9.4. Rangos

El volumen absoluto del catálogo actual tiene rango 0–100.

Mantén la validación de rango.

No conviertas valores fuera de rango en valores permitidos recortando cifras.

Ejemplo:

«Ciento veinte» no puede convertirse en 20.

Un número negativo no debe perder el signo.

## 9.5. Expresiones coloquiales

Prueba variaciones naturales del español:

- «Bájale tantico».
- «Ponlo más suave».
- «Está durísimo».
- «Mejor déjalo bajito».
- «Súbele un tris».
- «Que no alumbre tanto».
- «Pon las luces menos fuertes».
- «Me está encandilando».

No es necesario que todas produzcan una acción automáticamente.

Si el referente no está claro, deben generar una aclaración apropiada.

---

# 10. PROBLEMA 7 — INTEGRACIÓN REAL DE VOZ Y COMPRENSIÓN

Esta es una de las tareas más importantes de toda la fase.

## 10.1. Evidencia encontrada

El repositorio conserva una integración exitosa anterior con:

«Por favor pon la luz principal de color rojo».

«No, mejor cambia las luces a color azul».

Pero en la última integración sintética se registró una transcripción de Moonshine semejante a:

«Por favor, ponla en lo principal de color rojo».

Esto impidió establecer correctamente la propuesta inicial.

En otra prueba, una corrección corta se transcribió como:

«Fora Sodes».

Estos son fallos de reconocimiento que afectan la interpretación posterior.

## 10.2. Objetivo

Distinguir claramente:

1. Errores de captura.
2. Errores de VAD.
3. Errores de segmentación.
4. Errores de STT.
5. Errores de normalización.
6. Errores de interpretación.
7. Errores de contexto.
8. Errores de respuesta.

No atribuyas todos los fallos al LLM.

## 10.3. Diagnóstico por turno

Implementa un informe temporal que permita ver:

```text
Session ID
Turn ID
Wake detected
Speech start
Speech end
STT engine
Final transcript
Normalized text
Selected route
Interpretation
Safety validation
Context revision
Response
Latency
```

El registro de texto debe permanecer desactivado por defecto.

Permite habilitarlo temporalmente para pruebas voluntarias.

No guardes audio personal ni conversaciones permanentemente sin autorización.

## 10.4. Recuperación ante transcripciones dudosas

Investiga una estrategia escalonada:

**Nivel 1:** interpretación normal mediante el STT elegido.

**Nivel 2:** comprobación de consistencia de la transcripción con el contexto.

**Nivel 3:** transcripción alternativa bajo demanda, cuando exista audio suficiente y una duda real.

**Nivel 4:** aclaración breve al usuario.

Faster-whisper puede utilizarse como motor alternativo bajo demanda.

No lo ejecutes simultáneamente con Moonshine para todas las frases.

No utilices un diccionario de sustitución que convierta indiscriminadamente frases ambiguas en órdenes.

No inventes una luz porque una expresión se parezca acústicamente a su nombre.

## 10.5. Recuperación contextual

Si Jarvis comprende claramente el color «rojo», pero no identifica de forma fiable el dispositivo, puede preguntar:

«¿Te refieres a la luz principal?».

No debe inventar la respuesta y generar una propuesta autorizada.

## 10.6. Frases cortas

Prueba específicamente:

- «Azul».
- «Rojo».
- «No».
- «Sí».
- «Cancela».
- «Mejor azules».
- «La otra».
- «Al treinta».
- «Más bajo».
- «Déjalo así».

Las frases cortas son importantes porque suelen aparecer al responder aclaraciones.

## 10.7. Validación física

Prepara una sesión de prueba con el usuario que incluya:

- Micrófono habitual.
- Micrófono de audífonos, cuando esté disponible.
- Habla espontánea.
- Frases cortas.
- Pausas naturales.
- Variaciones de velocidad.
- Música de fondo moderada.
- Correcciones de una orden anterior.

No declares superada una prueba física que todavía no haya realizado el usuario.

---

# 11. PROBLEMA 8 — ACTIVACIÓN POR «JARVIS»

El usuario informó dificultades ocasionales al activar Jarvis.

La última configuración conocida utiliza Rustpotter con umbral aproximado de 0,55.

No reduzcas automáticamente ese umbral.

## 11.1. Objetivo

Medir la relación entre:

- Detecciones correctas.
- Activaciones perdidas.
- Falsas activaciones.
- Distancia al micrófono.
- Ruido ambiental.
- Diferencias entre micrófonos.

## 11.2. Herramienta de diagnóstico

Prepara un procedimiento para registrar temporalmente:

- Intentos de activación.
- Puntuaciones del detector cuando estén disponibles.
- Umbral utilizado.
- Activación aceptada o rechazada.
- Estado del micrófono.
- Momento de detección.

El sistema no puede conocer todos los intentos que el usuario hizo si no existe un protocolo de prueba que los registre.

Por eso prepara una prueba guiada donde el usuario indique cuántas veces pronunció «Jarvis».

## 11.3. Calibración

Si las mediciones muestran sensibilidad insuficiente:

- Evalúa repetir grabaciones de referencia.
- Examina el nivel de entrada.
- Examina ruido y distancia.
- Compara ajustes de umbral.
- Revisa falsos positivos antes de aceptar un nuevo umbral.

No reemplaces Rustpotter sin evidencia de que otra opción resulta significativamente mejor.

El detector debe seguir funcionando con consumo bajo.

---

# 12. PROBLEMA 9 — OPTIMIZACIÓN DE QWEN Y OLLAMA

La comparación disponible muestra:

**Qwen3 1.7B con cuatro hilos:**

- Aproximadamente 3,55 segundos.
- CPU media del equipo cercana a 13,83 %.

**Qwen3 1.7B con dos hilos:**

- Aproximadamente 6,05 segundos.
- CPU media del equipo cercana a 7,36 %.

Estas fueron pruebas aisladas y no representan por sí solas el rendimiento general.

La reducción de CPU aumenta la espera.

Necesitamos decidir qué configuración ofrece mejor experiencia.

## 12.1. Nuevas pruebas

Compara al menos:

- Dos hilos.
- Tres hilos, si el entorno lo admite.
- Cuatro hilos.

Utiliza las mismas solicitudes.

Repite cada escenario varias veces para reducir el efecto de variación ocasional.

Separa:

- Modelo recién cargado.
- Modelo preparado.
- Primera conversación.
- Conversación con contexto.
- Interpretación estructurada.
- Pregunta conversacional breve.

## 12.2. Métricas

Registra:

- Latencia total.
- Tiempo de carga.
- Tiempo de evaluación del prompt.
- Tiempo de generación.
- Tokens por segundo.
- CPU media.
- CPU máxima muestreada.
- Memoria del árbol de procesos.
- VRAM.
- Tiempo hasta comenzar la respuesta hablada cuando se mida el ciclo completo.

No consideres la CPU media como la única métrica de eficiencia.

## 12.3. Caché de metadatos

Revisa `ollama_client.py`.

Actualmente consulta información sobre los modelos instalados y sus capacidades.

Evalúa almacenar temporalmente estos metadatos para evitar consultas repetitivas en conversaciones consecutivas.

La caché debe invalidarse cuando:

- Cambie el modelo.
- Cambie el servidor.
- Se modifique la instalación.
- Se detecte un error de modelo desconocido.

No almacenes indefinidamente información potencialmente obsoleta.

## 12.4. Streaming

Investiga si las respuestas conversacionales pueden empezar a sintetizarse antes de recibir todo el texto final.

Pero no implementes una arquitectura complicada de reproducción incremental sin demostrar una mejora clara.

Las propuestas estructuradas de acción deben seguir validándose completamente antes de registrarse.

No permitas interpretar o ejecutar fragmentos parciales del modelo.

## 12.5. Tiempo máximo

Mantén plazos de espera y cancelación.

Si el LLM excede el tiempo disponible, Jarvis debe recuperarse.

No debe quedar indefinidamente en PROCESSING_RESPONSE.

---

# 13. PROBLEMA 10 — E5 Y CONSUMO DE MEMORIA

La optimización que evita cargar E5 para conversaciones generales debe conservarse.

El informe disponible muestra una reducción significativa de memoria del proceso Python cuando se evita esa carga.

Sin embargo, E5 continúa utilizando memoria cuando realmente se necesita.

## 13.1. Objetivo

Conservar la ventaja de comprensión semántica sin cargar el modelo innecesariamente.

## 13.2. Pruebas

Comprueba:

- Conversación general sin E5.
- Orden directa sin E5.
- Aclaración directa sin E5.
- Petición semántica compatible con E5.
- Retorno a conversación general después de usar E5.
- Liberación de recursos después de inactividad.

## 13.3. No perjudicar precisión

La restricción de dominios debe evitar cargas innecesarias, pero no bloquear expresiones naturales que podrían necesitar la búsqueda semántica.

Por ejemplo:

«La música está demasiado fuerte».

Debe seguir llegando a la ruta apropiada.

Si una expresión no contiene vocabulario explícito suficiente, estudia cuándo resulta mejor consultar Qwen o pedir aclaración.

No elimines la ruta semántica solo para reducir RAM.

## 13.4. Carga y descarga

Comprueba que liberar el proveedor ONNX realmente libera los recursos cuando termina el proceso o se aplica la política correspondiente.

Distingue entre:

- Memoria de Python.
- Memoria asignada por bibliotecas nativas.
- Memoria reservada.
- Memoria residente del proceso.
- Memoria de Ollama.

No presentes una sola cifra como consumo total sin explicar su alcance.

---

# 14. OPTIMIZACIÓN PARA VIDEOJUEGOS

El hardware del usuario dispone de:

- Ryzen 9 de la serie 4000.
- GTX 1660 Ti.
- 16 GB de RAM.

La prioridad sigue siendo evitar que Jarvis perjudique el uso normal del computador.

## 14.1. Medición real

Prepara un protocolo para comprobar:

- Jarvis dormido.
- Jarvis durante conversación.
- Qwen generando una respuesta.
- E5 cargando.
- Moonshine transcribiendo.
- Piper reproduciendo.
- Liberación posterior.

Cuando el usuario pueda realizar pruebas durante un juego, mide el impacto.

No inventes resultados de FPS.

## 14.2. Procesadores y afinidad

La Fase 3 limitó el proceso de voz a dos procesadores lógicos y redujo su prioridad.

Esta medida puede disminuir la interferencia con otras aplicaciones, pero también puede perjudicar la velocidad de transcripción.

Compara el perfil actual con alternativas controladas.

No modifiques el núcleo residente de bajo consumo sin razón.

## 14.3. Perfiles

Deja documentadas y, si resulta sencillo, configurables tres políticas:

**Equilibrado:** prioridad de respuesta y consumo moderado.

**Gaming:** limitar interferencia con el juego.

**Ahorro:** maximizar liberación de modelos tras inactividad.

No implementes todavía detección automática compleja de juegos.

La selección automática puede quedar para una fase posterior.

---

# 15. EVALUACIÓN INDEPENDIENTE DE COMPRENSIÓN

Este requisito es esencial para cerrar la Fase 3.

Los 328 casos escritos existentes se utilizaron durante el desarrollo.

No deben presentarse como prueba independiente de precisión general.

## 15.1. Nuevos conjuntos

Conserva los conjuntos actuales como regresión.

Crea un nuevo conjunto de al menos 150 ejemplos que no se utilicen inicialmente para ajustar el sistema.

Incluye:

- Frases naturales.
- Variaciones colombianas.
- Sinónimos.
- Negaciones.
- Condiciones.
- Correcciones.
- Ambigüedades.
- Comentarios.
- Preguntas.
- Cancelaciones.
- Números.
- Múltiples acciones.
- Frases cortas.
- Solicitudes con puntuación variable.

Añade un conjunto específico de seguridad de al menos 100 casos.

Evita duplicaciones y variaciones triviales de frases conocidas.

Los ejemplos nuevos deben diferir estructuralmente de los de entrenamiento y desarrollo.

## 15.2. Separación

Distingue:

**Development**

Conjunto utilizado para corregir errores.

**Holdout**

Conjunto reservado para la evaluación final.

**Critical Safety**

Conjunto de pruebas de negaciones, condiciones y autorizaciones indebidas.

El conjunto crítico también debe tener ejemplos reservados que no se utilicen para ajustar reglas.

Si inspeccionas los errores del holdout y modificas el código basándote en ellos, ese conjunto pasa a ser parte del desarrollo y deberás crear otro conjunto reservado para declarar una nueva precisión independiente.

## 15.3. Métricas

Mide:

- Exactitud de intención.
- Precisión de acciones propuestas.
- Recall de acciones válidas.
- Precisión de parámetros.
- Resolución contextual.
- Aclaraciones correctas.
- Aclaraciones innecesarias.
- Negaciones mal interpretadas.
- Condiciones mal interpretadas.
- Cancelaciones mal interpretadas.
- Latencia por ruta.
- Tasa de abstención.

No midas únicamente el porcentaje de respuestas correctas.

También necesitamos saber cuántas veces Jarvis se abstiene adecuadamente de actuar.

---

# 16. PRUEBAS DE SEGURIDAD MÁS ALLÁ DE LOS CASOS CONOCIDOS

Necesitamos encontrar errores que no estén cubiertos por las pruebas actuales.

## 16.1. Pruebas contrastivas

Genera pares donde una sola modificación cambia la autorización.

Ejemplo:

```text
Abre Steam.
No abras Steam.

Apaga la luz.
Apaga la luz cuando termine.

Sube el volumen.
No subas el volumen.

Cambia el color a azul.
Me gustaría cambiar el color a azul algún día.
```

## 16.2. Pruebas con cláusulas contradictorias

Ejemplos:

- «Abre Steam, pero espera, no lo abras».
- «No apagues las luces, aunque sí quiero que bajes el brillo».
- «Pon las luces azules, pero todavía no».
- «Cuando termine, apaga la luz; por ahora déjala encendida».
- «Baja el volumen, no, mejor súbelo».
- «No canceles, solo cambia el color».

## 16.3. Pruebas de contexto

Ejemplos:

- Referencia vencida.
- Dos aplicaciones mencionadas.
- Dos luces mencionadas.
- Solicitud corregida varias veces.
- Nueva solicitud durante aclaración.
- Cancelación de un plan con varias acciones.
- Respuesta tardía de una sesión antigua.
- Resultado de LLM inválido.
- Parámetros no presentes en la frase.
- Entidades no reconocidas.

## 16.4. Generación de casos

Puedes utilizar herramientas automáticas para generar variaciones, pero no consideres que cientos de ejemplos casi idénticos proporcionan evidencia independiente.

Prioriza diversidad semántica y estructural.

## 16.5. Propiedades de seguridad

Cuando sea posible, implementa pruebas basadas en propiedades o generación controlada.

Ejemplo:

Añadir una condición futura a una orden inmediata no debería convertirla en una autorización inmediata equivalente.

Añadir una negación que afecte la acción no debería conservar la propuesta afirmativa.

Estas propiedades deben definirse con cuidado para no generar falsas expectativas ante estructuras lingüísticas ambiguas.

---

# 17. INTEGRACIÓN COMPLETA — PRUEBA DEFINITIVA DE FASE 3.1

La prueba principal deberá recorrer el sistema real:

Rustpotter → AudioManager → Silero → Moonshine → DialogueManager → Validación → Contexto → Piper.

Durante la prueba, todas las acciones continuarán siendo simuladas.

## 17.1. Secuencia A — Luces

Usuario:

«Jarvis».

«Pon las luces rojas».

«No, mejor azules».

«Y bájales el brillo».

«Mejor al treinta por ciento».

Resultado esperado:

- Dispositivo correcto.
- Color azul.
- Brillo propuesto al 30 %.
- Correcciones contextualizadas.
- Ninguna acción física.
- Ningún error de sesión.

## 17.2. Secuencia B — Aclaración

«Abre una aplicación».

Jarvis:

«¿Cuál?».

Usuario:

«Steam».

Debe completar la propuesta.

Después:

«No, mejor Chrome».

Debe corregir el objetivo.

## 17.3. Secuencia C — Negaciones

«No abras Steam».

«Cuando termine de jugar, abre Steam».

«Abre Steam».

El sistema debe distinguir las tres peticiones.

Solo la última podrá convertirse en propuesta inmediata.

## 17.4. Secuencia D — Cancelación

«Pon las luces azules».

«Cancela».

Debe descartar la solicitud pendiente.

Después:

«No canceles la siguiente solicitud».

Debe interpretar correctamente la frase sin asumir automáticamente que existe una nueva cancelación.

## 17.5. Secuencia E — Conversación

«¿Qué es la memoria RAM?».

«Explícamelo más fácil».

«Dame un ejemplo».

Debe conservar el tema y responder naturalmente.

## 17.6. Secuencia F — Errores de STT

Utiliza algunas frases que hayan causado errores anteriormente.

No alteres el texto esperado para conseguir artificialmente una prueba aprobada.

Si el STT falla, el informe debe decirlo.

Evalúa si el sistema se recupera de forma correcta.

---

# 18. GESTIÓN DE ERRORES Y RECUPERACIÓN

Jarvis debe continuar funcionando cuando falle un componente no esencial.

## 18.1. Fallo de E5

La ruta semántica puede quedar temporalmente no disponible.

No debe cerrar Jarvis.

## 18.2. Fallo de Qwen

Jarvis debe conservar las rutas rápidas disponibles.

No debe afirmar haber entendido una solicitud compleja si no pudo interpretarla.

## 18.3. Fallo de STT

Debe descartar el turno defectuoso o solicitar repetir la frase.

No debe recuperar texto inventado.

## 18.4. Fallo del contexto

Si no se puede recuperar una referencia, solicita aclaración.

No utilices automáticamente el último destino de tipo parecido.

## 18.5. Fallo de validación

La propuesta debe rechazarse.

Conserva un estado conversacional coherente.

No dejes acciones parcialmente autorizadas.

---

# 19. GITHUB ACTIONS Y CALIDAD DEL REPOSITORIO

Actualmente existe evidencia de pruebas ejecutadas y guardadas, pero debemos mejorar la validación continua.

## 19.1. CI

Configura GitHub Actions para ejecutar las pruebas compatibles con un entorno sin hardware físico.

Incluye:

- Pruebas unitarias.
- Pruebas de contexto.
- Validadores.
- Ruta rápida.
- Contratos.
- Pruebas simuladas de cancelación.
- Pruebas de regresión.
- Comprobaciones básicas de importación.

No permitas que el pipeline dependa de un micrófono real, GPU o modelos Ollama descargados.

Separa las pruebas que requieren esos recursos mediante marcas o categorías.

Configura permisos mínimos para el flujo.

No publiques tokens ni credenciales.

## 19.2. Documentación

Actualiza:

- README.
- Arquitectura.
- Informe de Fase 3.
- Informe de Fase 3.1.
- Registro de decisiones.
- Guía de pruebas físicas.
- Limitaciones conocidas.

El repositorio ahora es público.

Corrige las referencias antiguas que lo describan como privado.

Antes de confirmar archivos de diagnóstico, comprueba que no contienen conversaciones personales, grabaciones o datos sensibles.

No elimines informes históricos legítimos únicamente porque muestren fallos.

## 19.3. Commits

Realiza commits diferenciados cuando corresponda:

- Seguridad temporal.
- Validación de correcciones.
- Contexto y aclaraciones.
- Integración de voz.
- Optimización de recursos.
- Pruebas independientes.
- Documentación y CI.

Los nombres son orientativos.

No realices commits artificiales sin cambios funcionales.

Publica la rama después de verificar cada conjunto terminado.

---

# 20. ORDEN DE IMPLEMENTACIÓN OBLIGATORIO

Trabaja en el siguiente orden.

## Etapa 1 — Auditoría y línea base

Inspecciona el proyecto, ejecuta las pruebas actuales y mide el estado inicial.

No hagas cambios de rendimiento todavía.

## Etapa 2 — Reproducción de defectos

Crea pruebas que expongan los riesgos identificados.

En particular:

- «Al acabar la partida».
- Correcciones con prohibición posterior.
- Negaciones durante aclaración.
- Cancelaciones.
- Estado modificado antes de validación.
- Resultados de sesiones caducadas.

Documenta cuáles producen fallos reales y cuáles ya están protegidos.

## Etapa 3 — Seguridad lingüística

Corrige temporalidad, negaciones y condiciones.

Verifica tanto ruta rápida como validación final.

## Etapa 4 — Contexto transaccional

Corrige cambios prematuros de estado, propuestas y aclaraciones.

Implementa actualizaciones coherentes.

## Etapa 5 — Planes y correcciones

Define cómo se agregan, sustituyen y cancelan propuestas.

Verifica secuencias largas.

## Etapa 6 — Normalización

Amplía pruebas y corrige defectos concretos de números, puntuación y expresiones coloquiales.

## Etapa 7 — Integración de voz

Evalúa Moonshine, errores cortos y recuperación controlada.

No cambies el micrófono o el umbral de activación sin evidencia.

## Etapa 8 — Rendimiento

Compara hilos de Qwen, retención, cachés y carga semántica.

Selecciona los valores según resultados.

## Etapa 9 — Evaluación independiente

Construye y ejecuta conjuntos nuevos.

Conserva los conjuntos existentes como regresión.

## Etapa 10 — Integración completa

Ejecuta simulaciones de voz y prepara las pruebas físicas del usuario.

## Etapa 11 — CI y documentación

Añade las comprobaciones reproducibles y actualiza los documentos.

## Etapa 12 — Informe final

Entrega un resultado técnico claro, con problemas corregidos, problemas pendientes y recomendación sobre el cierre de Fase 3.

---

# 21. CRITERIOS DE ACEPTACIÓN

No declares cerrada la Fase 3.1 hasta comprobar lo siguiente.

## Seguridad

- Ninguna condición futura del conjunto crítico produce una propuesta inmediata indebida.
- Ninguna negación de acción produce la acción afirmativa correspondiente.
- Las correcciones no pueden saltarse las comprobaciones esenciales.
- Las aclaraciones no producen acciones sin información suficiente.
- Las propuestas siguen siendo simuladas.
- No existe ejecución arbitraria.
- Las respuestas obsoletas no modifican sesiones nuevas.

## Contexto

- Las correcciones conservan referentes válidos.
- Las propuestas contradictorias se sustituyen correctamente.
- Las acciones compatibles de un plan se conservan.
- Las aclaraciones pendientes se resuelven o cancelan correctamente.
- Las referencias vencidas no se reutilizan indebidamente.
- El estado físico no se inventa.

## Voz

- Se conserva la activación local.
- Se conserva la captura única.
- Las frases cortas se prueban específicamente.
- El motor identifica o gestiona errores de reconocimiento.
- Las conversaciones por turnos siguen funcionando.
- No se produce un ciclo de respuesta a la propia voz.
- La secuencia principal de luces se supera por voz real o se documenta explícitamente por qué sigue fallando.

## Rendimiento

- Se conserva el reposo ligero.
- No existe inferencia LLM continua en DORMANT.
- Se mide la latencia real.
- Se compara el perfil de dos hilos con alternativas.
- Se conserva la carga diferida de E5.
- Se documenta el consumo de todos los procesos.
- No se introducen regresiones graves de estabilidad o memoria.

## Pruebas

- Las 218 pruebas existentes continúan aprobándose, salvo modificaciones contractuales justificadas.
- Existen nuevas pruebas para los defectos identificados.
- Se ejecuta un conjunto de evaluación reservado.
- El conjunto crítico no contiene propuestas indebidamente autorizadas.
- Las pruebas que requieren hardware quedan claramente separadas.
- Los resultados de GitHub Actions son verificables.

Los porcentajes obtenidos en conjuntos de desarrollo no deben presentarse como precisión general sobre frases desconocidas.

---

# 22. ENTREGABLES

Al finalizar debes entregar:

**1. Código actualizado de Fase 3.1.**

Sin reconstruir las fases anteriores.

**2. Registro de problemas.**

Para cada problema: reproducción, causa, cambio realizado y prueba de regresión.

**3. Validadores reforzados.**

Con especial atención a condiciones, negaciones y correcciones.

**4. Contexto estabilizado.**

Con operaciones coherentes y resultados de sesión protegidos.

**5. Normalización revisada.**

Incluyendo números, puntuación y frases coloquiales.

**6. Integración de voz evaluada.**

Con errores preservados y recuperación documentada.

**7. Comparación de rendimiento.**

CPU, RAM, latencia y retención de modelos.

**8. Evaluación independiente.**

Conjunto reservado y resultados reproducibles.

**9. CI.**

Pruebas automáticas ejecutables desde GitHub cuando el entorno lo permita.

**10. Documentación actualizada.**

Arquitectura, decisiones y límites.

**11. Commits publicados.**

Sin alterar el historial anterior.

**12. Informe final de preparación para Fase 4.**

Debe indicar una de estas conclusiones:

- Preparado para comenzar integración controlada de herramientas.
- Preparado parcialmente, con restricciones específicas.
- No preparado, con problemas bloqueantes identificados.

La conclusión debe basarse en pruebas.

---

# 23. FORMATO DEL INFORME FINAL

Al finalizar, presenta una tabla con las siguientes columnas:

| Problema | Estado anterior | Cambio realizado | Prueba | Estado final |
|---|---|---|---|---|
| Temporalidad | Descripción | Solución | Resultado | Resuelto/Pendiente |
| Correcciones | Descripción | Solución | Resultado | Resuelto/Pendiente |
| Contexto | Descripción | Solución | Resultado | Resuelto/Pendiente |
| Aclaraciones | Descripción | Solución | Resultado | Resuelto/Pendiente |
| Normalización | Descripción | Solución | Resultado | Resuelto/Pendiente |
| Voz | Descripción | Solución | Resultado | Resuelto/Pendiente |
| Rendimiento | Descripción | Solución | Resultado | Resuelto/Pendiente |

Incluye también:

- Commit final.
- Rama.
- Número de pruebas aprobadas.
- Número de pruebas fallidas.
- Resultados de evaluación independiente.
- Latencia comparativa.
- Consumo comparativo.
- Fallos conocidos.
- Pruebas físicas pendientes.
- Recomendación de cierre.

No reduzcas el informe a «todas las pruebas pasaron».

Necesito comprender qué mejoró realmente.

---

# 24. LO QUE NO DEBES HACER

Durante Fase 3.1 está prohibido:

1. Reescribir todo Jarvis sin justificación.
2. Sustituir Rustpotter por iniciativa propia.
3. Cambiar el micrófono sin necesidad.
4. Alterar arbitrariamente el VAD.
5. Reemplazar Qwen por un modelo grande.
6. Cargar E5 durante todas las conversaciones.
7. Eliminar validaciones para mejorar reconocimiento.
8. Convertir toda frase dudosa en una orden.
9. Ejecutar acciones reales.
10. Añadir un controlador físico de luces.
11. Abrir aplicaciones mediante voz.
12. Cambiar el volumen real.
13. Ejecutar comandos shell producidos por el LLM.
14. Guardar permanentemente conversaciones personales.
15. Modificar conjuntos de evaluación reservados para inflar la precisión.
16. Borrar pruebas históricas que muestran errores.
17. Declarar pruebas físicas no realizadas.
18. Presentar inferencias como mediciones.
19. Publicar credenciales o datos sensibles.
20. Iniciar automáticamente la Fase 4.

---

# 25. EXPERIENCIA FINAL QUE BUSCAMOS

Al terminar la Fase 3.1 quiero poder hablar con Jarvis de manera natural.

Ejemplo:

**Usuario:** «Jarvis».

**Usuario:** «Pon las luces rojas y abre Steam».

Jarvis identifica dos propuestas simuladas.

**Usuario:** «No, mejor azules».

Jarvis cambia únicamente el color.

**Usuario:** «Y que no alumbren tanto».

Jarvis interpreta una reducción de brillo utilizando el contexto.

**Usuario:** «Pero todavía no hagas nada».

Jarvis conserva la intención conversacional correspondiente sin autorizar una ejecución inmediata.

**Usuario:** «Bueno, olvida lo de las luces».

Jarvis descarta las propuestas de iluminación afectadas por la cancelación, conservando otras solicitudes independientes cuando corresponda.

**Usuario:** «¿Y qué es exactamente la memoria RAM?».

Jarvis cambia a conversación general.

**Jarvis:** Explica brevemente la RAM.

**Usuario:** «Explícamelo más sencillo».

Jarvis mantiene el tema y adapta la explicación.

**Usuario:** «Gracias, hablamos luego».

Jarvis responde brevemente y regresa a reposo.

Todo continúa siendo local y simulado.

No tiene que ser una inteligencia perfecta.

Tiene que ser un sistema capaz de interpretar correctamente los casos comunes, reconocer sus dudas y evitar decisiones injustificadas.

---

# 26. EL PRINCIPIO FUNDAMENTAL

**No queremos que Jarvis ejecute más cosas. Queremos que se equivoque menos cuando interpreta lo que le pedimos.**

La Fase 4 convertirá propuestas en acciones reales.

Eso significa que la calidad del motor de comprensión dejará de ser un detalle conversacional y pasará a tener consecuencias sobre el computador y los dispositivos conectados.

Por eso esta fase debe asegurar que:

- Las decisiones estén fundamentadas.
- Las negaciones se respeten.
- Las condiciones no se ignoren.
- Las correcciones sean coherentes.
- Los contextos no se mezclen.
- Los resultados tardíos no afecten conversaciones nuevas.
- Los errores de transcripción no se transformen en órdenes inventadas.
- Los modelos consuman recursos solo cuando aporten valor.

La fiabilidad es más importante que aparentar inteligencia.

La velocidad es más importante que producir respuestas extensas.

La flexibilidad es más importante que memorizar cientos de comandos rígidos.

Y la eficiencia es más importante que mantener modelos trabajando sin necesidad.

**La Fase 3.1 debe dejar preparado el cerebro de Jarvis para que la Fase 4 pueda comenzar sobre una base segura, estable y rápida.**

---

# 27. INSTRUCCIÓN FINAL PARA CODEX

Comienza ahora la implementación real de:

**JARVIS — FASE 3.1: INTELLIGENCE HARDENING & OPTIMIZATION.**

Primero inspecciona el código y verifica el estado de Git.

Reproduce los problemas identificados antes de modificarlos.

Corrige temporalidad, negaciones y validación de correcciones.

Refuerza la coherencia del contexto, los planes y las aclaraciones.

Evalúa los errores de voz sin introducir asociaciones acústicas peligrosas.

Optimiza el uso de Qwen y E5 mediante pruebas comparativas.

Construye conjuntos de evaluación independientes.

Ejecuta las pruebas anteriores y las nuevas.

Añade CI compatible con GitHub.

Documenta los cambios y sus resultados.

Publica los commits en una rama de Fase 3.1.

Si una prueba depende de mi voz, micrófono o videojuegos y no puedes ejecutarla, prepara instrucciones claras para que yo la realice.

**No implementes Fase 4.**

**No habilites acciones reales.**

**No declares finalizada la Fase 3.1 hasta proporcionar evidencia técnica suficiente y separar claramente las pruebas pendientes.**

Entrega el código actualizado, las pruebas y un informe de preparación para la siguiente fase.

**Comienza el desarrollo ahora.**