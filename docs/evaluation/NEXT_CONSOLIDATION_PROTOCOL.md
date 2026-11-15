# Referencia textual previa a voz

15 de noviembre de 2026. Se sella el motor de `731917a` antes de ampliar el contexto: 32 turnos, 29 textos nuevos y tres controles directos conocidos. Incluye contexto, órdenes naturales, negaciones, citas, hipótesis, condiciones, ambigüedad y capacidades inexistentes. Mismo autor que el código: la independencia humana no está demostrada; solo se excluyen duplicados textuales normalizados conocidos.

Groq 120B Medium, **4 s de plazo candidato de producción**, 1024 tokens máximos y mínimo 20 s entre solicitudes. El plazo se elige antes de leer resultados, con referencia al p95 histórico de 2,476 s más margen; no es garantía y se informan todos los timeouts. Máximo 29 solicitudes de primera exposición; una respuesta errónea no se reintenta. No se ajustan prompt ni motor durante la pasada. Ante fallo se conserva la cobertura realmente observada; una continuación solo puede empezar sesiones intactas y debe documentarse, sin repetir intentos.

Se separan clasificación observable del proveedor, validez del contrato, decisión del router, rechazos de política y coincidencia/aplicación del plan con conservación de IDs. Los fallos anteriores se marcan en secuencias dependientes. El evaluador solo confirma una propuesta si coincide con la expectativa completa: esa autorización por oráculo nunca se conecta al residente.

Se conservan métricas de latencia por ruta, errores, categorías y turnos no observables. Los informes no capturan audio ni HTTP. El conjunto se retira a desarrollo antes de usar sus errores para ajustar el motor. Los cambios posteriores de contexto/voz se verifican por regresiones e integración; no se atribuye a la versión nueva una precisión medida en esta base anterior.
