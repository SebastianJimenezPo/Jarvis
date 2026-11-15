# Jarvis Next — piloto textual Groq y revisión contextual, 2026-11-14

Continuación autorizada de la primera etapa, base `cda3c5e`. La voz sigue en 3.1; no se habilitan herramientas físicas. Al empezar no había clave y se verificó el cliente con HTTP falso. Después el usuario proporcionó una clave y confirmó que su cuenta seguía en Free. Se guardó exclusivamente en Windows Credential Manager (`JarvisNext/Groq`, usuario actual) y se inició un piloto real con frases sintéticas de desarrollo. No se incluye la clave ni un fragmento en código, comandos, informes o Git.

## Proveedor elegido para el piloto

Candidatos explícitos `openai/gpt-oss-20b` y `openai/gpt-oss-120b`; no hay selección/fallback automático ni se declara ganador general. La comparación se hizo por etapas y sus límites se detallan abajo. La documentación oficial consultada lo incluye entre los modelos con JSON Schema estricto; ese modo requiere objetos cerrados y todas las propiedades obligatorias. Por eso se usa un contrato de transporte pequeño y cerrado, con valores opcionales como `null`, separado del contrato interno extensible. Las evidencias son citas exactas convertidas a índices localmente, sin pedir al modelo calcular posiciones Unicode. Fuentes: [salidas estructuradas](https://console.groq.com/docs/structured-outputs), [modelo](https://console.groq.com/docs/model/openai/gpt-oss-20b).

Una petición a Chat Completions, sin streaming, tools, búsqueda, código o fallback: límite de salida 1.024 tokens y razonamiento `low` o `medium` explícito, admitidos para esos modelos según la [referencia API](https://console.groq.com/docs/api-reference). El plazo global del motor limita la espera. Se mantiene una conexión TLS verificada al host fijo `api.groq.com`; se descartan redirecciones y respuestas mayores de 64 KiB. No hay SDK ni dependencia nueva. La conexión puede reutilizarse entre turnos; un fallo la cierra y no se reintenta el turno.

Groq distingue Free de Developer y las cuotas exactas varían por organización. El cliente no puede verificar el plan de facturación con una API key. Antes de usarlo, el operador debe comprobar que la cuenta sigue en Free; no añadir pago ni actualizar de plan. No se promete cuota fija o gratuidad de una cuenta Developer. Fuentes: [límites](https://console.groq.com/docs/rate-limits), [facturación](https://console.groq.com/docs/billing-faqs).

Los mensajes contienen solo texto actual, plan operativo y cinco capacidades de simulación. No se envían audio, historial completo, pantalla, archivos, IDs de sesión innecesarios ni claves en el prompt. La clave va solo en la cabecera de autorización al host fijo; no se interpolan cuerpos o excepciones HTTP en errores. Los ajustes Data Controls del proveedor siguen siendo responsabilidad de la cuenta: su política permite retención temporal para fiabilidad/abuso y ofrece opciones de exclusión; no se presenta una promesa absoluta de retención cero. Fuente: [datos en GroqCloud](https://console.groq.com/docs/your-data).

## Límite de autorización

Un esquema válido o una cita literal no demuestran intención correcta. Las órdenes directas conservan su validación independiente. Las decisiones complejas se ofrecen para revisión de desarrollo; todavía no autorizan ejecución real ni se aplican automáticamente por venir de Groq. La revisión queda ligada a contenido, sesión, generación, revisión y caducidad del plan. Se comprobaron cambios de objetivo/valores, adiciones, cancelaciones selectivas y modificaciones atómicas con adaptadores falsos antes de usarlos con el piloto real.

El contrato interno añade `ActionChange.target` opcional para corregir una aplicación sin inventar un nuevo ID. La modificación necesita un objetivo o parámetros; se revalidan juntos contra el registro. Se reprodujo antes de corregir que el destino modificado aún no se contrastaba, aunque la propuesta permanecía retenida: ahora un objetivo inventado produce rechazo, sin alterar el plan.


## Revisión de planes en esta etapa

La revisión es una interfaz de desarrollo explícita (`--review`), no una conversación de aprobación añadida a la voz. Un resultado contiene `review` con ID generado localmente, revisión base y el plan completo propuesto. La aplicación usa `:confirm ID` en la misma sesión. Este modo optativo muestra el texto actual en la salida JSON local: no publicar salidas de órdenes personales. El borrador dura hasta 30 s o hasta la caducidad del contexto; cualquier turno normal, cambio de sesión, retención, cancelación o cierre lo invalida. Un ID incorrecto consume el intento y exige otra solicitud. El modelo nunca recibe ni genera un `review_id`.

El borrador y la decisión son copias: cambiar el JSON mostrado no cambia lo que se confirma. IDs de acciones existentes se conservan al modificar; append añade solo elementos nuevos; cancel_subset/remove elimina solo los indicados; replace genera un plan nuevo. Se rechazan contradicciones por herramienta/objetivo, dependencias inválidas y más de ocho elementos. Un cambio con varias partes se valida por completo antes de confirmarse. Todos los resultados siguen con `executed=false`, `verified=false`; consultar volumen devuelve desconocido.

El evaluador puede confirmar automáticamente solo cuando la operación y TODO el plan propuesto coinciden con las expectativas escritas del caso de prueba. No confirma por ser JSON válido. Los casos no correctos se guardan sin aplicar y los turnos posteriores se marcan si la preparación contextual falló. Esto sirve al piloto controlado, no autoriza automáticamente instrucciones arbitrarias.

## Ejecutar sin compartir claves

La credencial ya está configurada en este equipo. No hace falta volver a pegarla en el chat ni incluirla en un comando. Si se reemplaza después, puede guardarse localmente con entrada oculta:

```powershell
.\.venv\Scripts\python.exe -c "from getpass import getpass; from jarvis.next.credentials import store_groq_key; store_groq_key(getpass('Clave Groq: ')); print('Credencial guardada')"
```

`GROQ_API_KEY` tiene prioridad si existe; por defecto se consulta la credencial de Windows solo cuando Groq está explícitamente habilitado. No se escribe un archivo `.env`. Para quitarla, usar Administrador de credenciales de Windows → Credenciales genéricas → `JarvisNext/Groq`. Las pruebas automatizadas usan claves falsas y sustituyen la lectura del almacén; no necesitan ni leen la clave real.

Comprobar que la cuenta sigue siendo Free antes de usar `--free-tier`. Ese flag declara una comprobación del operador, no detecta el plan de la cuenta ni impide cargos de una cuenta que alguien haya actualizado a Developer. El programa no añade pago, cambia de plan ni elige otro servicio.

```powershell
# Offline: ninguna petición a Groq, aunque exista la credencial.
.\.venv\Scripts\python.exe -m jarvis.next "Abre Steam" "Olvida todo lo anterior"

# Consola textual remota opcional; inspeccionar review.proposed_plan antes de :confirm ID.
.\.venv\Scripts\python.exe -m jarvis.next --provider groq --allow-remote --free-tier --review --interactive --model openai/gpt-oss-120b

# Piloto pequeño; conserva resultados previos y detiene errores de proveedor sin reintentar.
.\.venv\Scripts\python.exe scripts\evaluate_next_pilot.py --provider groq --allow-remote --free-tier --model openai/gpt-oss-120b --max-turns 5 --interval-seconds 30 --output build/groq-pilot-local.json
```

Crear `build` si no existe. El evaluador limita cada ejecución a un máximo de 40 turnos (32 por defecto) y un intervalo mínimo de seis segundos entre consultas reales; puede aumentarse según cuotas. Esa espera no entra en la latencia por interpretación. Se detiene ante autenticación, cuota, modelo ausente, timeout, conexión o respuesta malformada, sin repetir ni borrar el resultado. No presentar una ejecución parcial como piloto completo.

`python -m jarvis` conserva el residente y la voz 3.1. La consola nueva no abre micrófono ni cambia el dispositivo, umbral, referencia o 1.200 ms de silencio. No se ha medido aquí la voz real, el reposo del residente, reinicio con Next, FPS ni estabilidad prolongada.


## Resultados reales conservados

Todos los casos son desarrollo, redactados internamente y conocidos durante ajustes; ninguno es holdout ni demuestra generalización. Las respuestas fixture se construyen desde expectativas y solo prueban orquestación. El evaluador confirma únicamente si coinciden operación y plan completo esperados. Una preparación fallida deja el plan anterior intacto y marca los turnos dependientes; no se atribuyen todos esos fallos al modelo aislado.

- Antes de disponer de clave se conservaron informes `next-pilot-groq-not-run*.json`, con estado no ejecutado y métricas nulas. Son históricos: después se configuró la credencial y sí hubo consultas reales.
- 20B, primer piloto: 2/5 comprobaciones correctas, tres consultas remotas, dos turnos directos. Confundió corrección con reemplazo y otra propuesta fue rechazada. [Informe](reports/next-pilot-groq-live-first.json).
- 20B, instrucciones de edición revisadas: 3/5; tres consultas. «Y abre Discord» siguió convirtiéndose en corrección en lugar de adición. [Informe](reports/next-pilot-groq-live-edits.json).
- 120B `low`, piloto amplio: **24/32** comprobaciones correctas; 9/9 turnos directos y 15/23 remotos. Seis turnos tenían preparación contextual fallida. Hubo un borrador de acción inesperado ante una orden citada; el evaluador no lo confirmó. La última respuesta fue inválida y detuvo el piloto, aunque ya se habían intentado los 32 turnos. [Informe completo](reports/next-pilot-groq-120b.json).
- 120B `medium`, regresión focalizada: **8/15**, 11 consultas remotas. No resolvió la confusión de adición/corrección y hubo otro borrador incorrecto ante una cita. No se compara ese porcentaje con 24/32 como si fueran el mismo conjunto o la misma política. [Informe](reports/next-pilot-groq-focus-medium.json).

El piloto amplio midió la ruta remota con mediana **0,812 s** y p95 **1,437 s**, frente a 0,228 ms y 0,489 ms en los nueve turnos directos. Incluye solicitud completa, validación y propuesta; excluye espera artificial entre consultas y confirmación local. No es tiempo hasta primer token ni latencia de voz. No hubo STT, VAD o Piper en esa medición.

El proceso textual del piloto amplio terminó con **43,2 MB de RSS**, con máximo de 43,2 MB en fronteras de turno; CPU acumulada de interpretación/revisión **0,1875 s** en las muestras Windows. No se muestreó pico continuo de CPU/RAM ni GPU. No incluye residente de voz, recursos del servidor remoto ni impacto en juegos; no se compara como equivalente a los 1,7 GB de Ollama activo o a la memoria del residente completo. No se instalaron ni cargaron modelos LLM locales para esta etapa.

### Defectos de política/evaluación separados de los del modelo

Se reprodujo que la revisión exigía una cita que cubriera todo el turno, rechazando una cancelación selectiva correcta con evidencia de la cláusula afectada. Se corrigió exclusivamente la preparación del borrador: conserva la solicitud completa local y la evidencia parcial literal, sin conceder autorización automática. La revisión sigue ligada a ID, revisión, sesión, generación y TTL. La prueba verifica que antes de confirmar no cambia el plan y que el estado completo se revisa, no solo el fragmento.

También se detectó una exigencia excesiva del evaluador: `remove_actions` y `cancel_subset` retiran exactamente los mismos IDs pendientes en este reductor de simulación. Desde la corrección se aceptan como equivalentes solo si todo el plan propuesto coincide. `replace_plan` y `modify_plan` NO son equivalentes: sustituir el plan cambia su identidad y pierde referencias. Los informes anteriores se conservan con sus cifras originales, sin recalcularlos silenciosamente como aprobados.

Se equilibraron ejemplos de adición frente a corrección y se aclararon prohibiciones, citas y consultas de lectura en el prompt. Es ajuste con datos de desarrollo, no un resultado independiente. El rechazo original por destino inventado, los errores de alcance y los fallos de proveedor no se ocultan bajo éxito de esquema JSON. `proposed_operation` y `policy_reason` aportan diagnóstico de enums controlados sin publicar parámetros inválidos, respuestas libres o cuerpos HTTP.


## Comprobación final y estado de entrega

Tras equilibrar instrucciones y corregir el evaluador, la regresión focalizada de ocho turnos obtuvo **6/8**. Las prohibiciones, la cita y la consulta de volumen quedaron bien clasificadas. La adición de Discord ya era correcta, pero el código aún rechazaba preparar su revisión porque la evidencia estaba en cada acción y no duplicada en el campo global. Se reprodujo ese defecto antes de corregirlo: una cita válida por acción basta para preparar el borrador, conservando siempre la solicitud completa. No se aplica nada sin revisión local. [Informe previo al último ajuste](reports/next-pilot-groq-focus-final.json).

Con esa corrección, la secuencia real de aplicaciones obtuvo **5/5**: abrir Steam en simulación → corregir a Spotify preservando el ID → añadir Discord → retirar solo Discord → cancelar todo. Fueron tres consultas remotas y dos turnos directos; mediana remota **1,128 s**, p95 **1,232 s** (solo tres muestras). [Informe del código final](reports/next-pilot-groq-apps-after-policy.json), motor `f96949f`.

Es una regresión de casos conocidos, no un nuevo 100% de precisión general. El piloto amplio de 32 casos no se repitió entero después de los últimos ajustes, ni se hizo evaluación reservada nueva. Sus 24/32 y todos sus fallos permanecen publicados. No se fijó semilla ni temperatura explícita: las salidas del servicio pueden variar; no hay estimación estadística de estabilidad por estas muestras.

Se realizaron **49 consultas reales en total**, todas a Groq tras la confirmación del usuario de que su cuenta era Free. Se limitaron y espaciaron las consultas, sin reintentos automáticos. No se habilitó facturación, se compraron créditos ni se cambió de proveedor tras un error. Los experimentos `medium` no demostraron una ventaja general que justifique adoptarlos por defecto. Las dos configuraciones quedan explícitas y el modo offline sigue siendo el predeterminado.

Controles finales sin API: [fixture actual](reports/next-pilot-fixture-current.json), 32/32 comprobaciones de infraestructura; [offline actual](reports/next-pilot-offline-current.json), 9/32, con 11 turnos afectados por preparación contextual no resuelta. El resto requiere interpretación compleja: no se presenta esa abstención como comprensión correcta. Informes de desarrollo iniciales y de ausencia de clave se conservan con su procedencia, sin sumarlos como evaluaciones independientes.

### Pruebas y publicación

- **506 pruebas locales aprobadas, cero fallos**, en 29,29 s: 379 heredadas y 127 de Next. [Salida completa](reports/pytest-phase32-stage2-final.txt). No se eliminaron pruebas antiguas.
- [CI del código final verificado](https://github.com/SebastianJimenezPo/Jarvis/actions/runs/43641790404): `headless-windows`, 500 aprobadas, una omitida por instalación explícita de voz y cinco excluidas; `next-offline`, 127 aprobadas sin extras de inteligencia/voz. Las 127 se solapan con la batería general y no se suman como pruebas distintas.
- Comprobación exacta de la clave, leída del almacén local sin imprimirla: ninguna coincidencia en archivos versionados o publicables. No se almacena la clave en informes ni se usan credenciales reales en tests/CI.
- Compilación, enlaces y referencias de restauración comprobados. El código de residente, captura, voz e inteligencia 3.1 permanece intacto respecto a `5337b86`.

| Componente | Estado anterior | Cambio realizado | Motivo | Evidencia | Estado final |
| --- | --- | --- | --- | --- | --- |
| Proveedor | Offline/falso | Groq optativo, TLS fijo y esquemas cerrados | Probar interpretación capaz sin modelo local | HTTP simulado y 49 consultas reales | Conexión funcional, calidad experimental |
| Credenciales | Sin configurar | Almacén Windows del usuario; entorno opcional | Evitar claves en código, argumentos y Git | Lectura/guardado local y revisión exacta de archivos | Configurada fuera del repositorio |
| Contexto | Complejas retenidas sin edición | Proyección y revisión atómica de planes, objetivos, parámetros y subconjuntos | Conservar lo no modificado y evitar autorización del modelo | Pruebas de IDs, revisiones, TTL y última secuencia 5/5 | Funcional en simulación revisada |
| Política | Evidencias demasiado rígidas al preparar borradores | Solicitud completa ligada a revisión; citas parciales/acción validadas como tales | Corregir falsos rechazos sin dar permiso automático | Reproducciones antes de corrección | Sin autorización automática ni herramientas físicas |
| Evaluación | Solo fixture | Pilotos reales, atribución de rechazo y equivalencia de retiro pendiente | No confundir esquema/modelo/política ni ocultar fallos | 24/32 amplio; informes parciales preservados | No se acredita objetivo general del 95% |
| Voz y herramientas físicas | Residente 3.1 | Se conservan sin migración | Mantener alcance por etapas | Regresión heredada aprobada | Integración y aceptación física pendientes |

**Estado: bloque textual con Groq implementado y probado; Fase 3.2 abierta.** No se recomienda autorización automática ni conectar herramientas físicas sobre estas cifras. No hay nuevos resultados de voz real, ruido, pausas, reinicio con Next, juegos o estabilidad prolongada.

Siguiente bloque recomendado: congelar la configuración elegida y hacer evaluación nueva reservada de comprensión/contexto, separando predicción, router, política y aplicación. Resolver los fallos que aparezcan con reproducciones y retirar del rol reservado cualquier conjunto usado para ajustes. Después integrar la entrada/salida de voz mediante el puente existente, manteniendo simulación y sin reconstruir captura. El adaptador físico de volumen sigue siendo un bloque posterior y su activación requiere aprobación explícita.
