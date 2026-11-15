# Primera evaluación reservada interna de Next — 2026-11-14

Se congela el motor textual de `4ca6910572fb3673b9cab9d9a837bd5620236d77`, sin modificar `jarvis/next`. Los hashes SHA256 de cada módulo usan UTF-8/LF normalizado para ser reproducibles entre checkouts. La configuración es Groq `openai/gpt-oss-120b`, esfuerzo low, salida de 1.024 tokens definida por el adaptador, plazo global 8 s y 20 s entre solicitudes. No hay reintentos, fallback ni herramientas físicas. La autorización de la cuenta Free y el uso de su credencial proceden del usuario; no se leen o publican valores en los informes.

`next_reserved_v1.json` contiene 32 turnos nuevos y un control conocido explícito de preparación. Hay tres secuencias de contexto, doce casos críticos independientes y cinco de capacidades/ambigüedad/observación. Se verificaron duplicados exactos normalizados frente a corpus/informes JSON y literales de las pruebas; el control conocido no se cuenta como dato nuevo. Eso no excluye similitudes semánticas. Los ejemplos fueron redactados por el mismo agente tras congelar su implementación: no son una validación humana externa ni completamente ciega respecto al diseño.

Sello del dataset: `cf4f1e0e3864c4b3f86d57ee5081f788d23b971f744ceeaac802991779f2394c`. Los objetivos y parámetros esperados no se envían al proveedor. En un caso de estado histórico no observado se predeclaran como válidas aclaración o capacidad no disponible: ambas satisfacen preguntar o explicar la limitación; no se añade esa tolerancia después de ver respuestas. Retirar/cancelar un subconjunto sigue la equivalencia de operaciones ya declarada en la etapa 2.

El control fixture usa las expectativas para generar respuestas: solo verifica infraestructura y no cuenta como calidad de IA. Antes de Groq, el ejecutor verifica los sellos de datos y código. Se publica el conjunto antes de consultar sus resultados. El ejecutor rechaza sobrescribir informes o usar otra revisión del motor con este mismo sello.

## Separación de medidas

- Contrato interno recibido: una respuesta ausente por transporte o por rechazo del adaptador no se convierte artificialmente en JSON válido o inválido del modelo; se informa cobertura observable.
- Operación del proveedor: acierto sobre decisiones parseadas observables; no es exactitud global del modelo. Se conserva el número de decisiones no observadas.
- Herramientas/parámetros y referencias: validez del registro y de IDs/revisión/plan, por separado. Los casos sin propuestas de herramientas no inflan el denominador del catálogo.
- Propuesta completa: comparación de objetivos y valores contra el estado esperado, con rechazos locales identificados. No se atribuye automáticamente ese resultado conjunto al modelo.
- Aplicación: la confirmación local solo se realiza si operación y TODO el plan coinciden con las expectativas escritas. Después se comprueban identidad del plan y conservación de IDs. No basta con que las acciones mostradas parezcan iguales si se perdieron sus referentes.
- Contexto: los turnos posteriores a una preparación fallida quedan marcados. No se ocultan sus efectos ni se cuentan como evidencia independiente de comprensión contextual.
- Seguridad: se distinguen borradores no solicitados, resultados emitidos antes de revisión y ejecución física (deshabilitada por diseño). No se llama «seguro» al mero acierto del tipo JSON.

Solo texto, estados propuestos, respuestas estructuradas y métricas locales. No se guarda audio, se captura pantalla ni se cambia la voz. Los errores publicados son categorías y booleanos, nunca cuerpos HTTP, claves o valores de herramientas desconocidas. La observación está en el evaluador, no añade almacenamiento conversacional al runtime.

Una primera pasada conserva todos los fallos y no ajusta el motor durante la ejecución. Si después se usan para corregir prompt, política, contrato o código, el conjunto se retira como reservado y pasa a regresión. No puede presentarse un segundo intento sobre esos datos como otra validación independiente. La integración de voz y la autorización automática siguen fuera de este bloque.

## Interrupción y continuación manual

La ejecución se detuvo tras 18 turnos por `invalid_response`. No se repitió ese caso. Se añadió al ejecutor (no al motor) una continuación manual que exige el mismo sello, proveedor, configuración y prefijo de casos ya intentados. Solo permite empezar otra sesión aún no observada; rechaza reanudar a mitad de una secuencia. Se registran offset y hash canónico del informe anterior.

La continuación procesa los 15 casos intactos restantes con el mismo motor `4ca6910`. La consolidación verifica orden, ausencia de duplicados y enlaces de procedencia. No es una segunda evaluación y conserva el fallo original en el denominador. La conexión TLS se inicia de nuevo; las latencias son observaciones de dos procesos, no un experimento continuo controlado.

`setup_succeeded` es un indicador conservador de que todas las comprobaciones anteriores de la secuencia pasaron. Un fallo previo de clasificación puede activar esa marca aun si el plan real no cambió; no demuestra por sí solo que el estado operativo esté equivocado. Las medidas de referencias e identidad/no mutación se informan aparte y también incluyen casos sin elementos activos.

## Retirada de v1

`next_reserved_v1.status.json` registra su retirada antes de modificar el motor. El ejecutor reservado comprueba este estado además de los sellos. La consolidación histórica sigue disponible; repetir ejemplos conocidos solo aporta evidencia de regresión de desarrollo. Ver [etapa 3](../phase_3_2_stage_3.md).
