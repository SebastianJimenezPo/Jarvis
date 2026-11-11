# Auditoría inicial de Fase 3.1

2026-11-10. Rama de origen `phase-3-intelligence`, HEAD exacto `fed3f113455c6e867283b4959a5f21bdd0c35d4b`, sin cambios locales ni commits posteriores. GitHub confirmó visibilidad PUBLIC. Rama nueva `phase-3-1-hardening`; historial de origen intacto.

Se leyeron AGENTS, README, informes de fase 3, comparación de modelos, arquitectura, validación y los fallos históricos de voz. El residente se cerró por su manejador Windows de fin de sesión, sin terminar procesos ajenos. Línea base: 218 aprobadas en 26.14 s (`reports/phase31-baseline.txt`). No se modificó rendimiento durante esta etapa.

Antes de corregir se escribieron 38 regresiones de desarrollo: **23 fallaron y 15 pasaron**. Salida preservada en `reports/phase31-reproductions-before.txt`. Tras separar archivos por área, los casos de autorización están en `test_phase31_authorization.py` y los de estado/planes/normalización en `test_phase31_reproductions.py`. Estos casos son desarrollo, nunca evaluación reservada.

| Área | Reproducción inicial | Causa |
| --- | --- | --- |
| Temporalidad | 6 construcciones futuras emitieron acciones | Detección incompleta de subordinadas temporales |
| Correcciones | 4 prohibiciones/posposiciones no bloquearon acciones | Guardas globales incompletas y excepción por reason_code |
| Pasado relativo | Petición inmediata con «que usé ayer» mal clasificada | Una palabra temporal afectaba toda la frase |
| Estado | Cancelación dejó pending; rechazo borró aclaración | Mutaciones durante interpretación, antes de validar |
| Aclaración | «No canceles» y «No quiero cancelar» borraron pending | Negación confundida con abandono |
| Plan | Ampliar perdió acciones; corrección numérica no se resolvió | Lista sin operación append/modify ni foco de parámetro |
| Números cortos | 4 frases «Volumen al…» no resueltas | Sintaxis nominal y conjunción numérica no cubiertas |
| Cancelación selectiva | Se conservaron luces que se pidieron descartar | No había operación de cancelación por alcance |
| Validador | reason_code de corrección permitió destino inventado | La procedencia sustituía evidencia |

La comprobación adicional del validador reprodujo seis fallos (tres casos, con ambas etiquetas de ruta): consultar estado ante «Abre Chrome», volumen ante una petición de luces y brillo con dirección contraria. Otro grupo de diez pruebas gramaticales encontró ocho fallos en subordinadas y menciones no imperativas. Se corrigieron con pruebas previas; no son descubrimientos de holdout.

Etapa de seguridad: análisis de acto y alcance gramatical independiente del creador de propuestas, vetos completos, subordinadas, distinción de pasado relativo y validación de evidencia contextual. No se confía en la ruta o reason_code. La validación usa una instantánea previa para poder verificar aclaraciones resueltas; la etapa siguiente convierte también la interpretación completa en una transacción.

No se cambiaron micrófono, umbral de Rustpotter, VAD, modelos instalados ni ejecución simulada. La integración histórica de luces continúa registrada como fallida por STT; todavía no se atribuye a esta fase una aceptación física nueva.

Etapa de contexto: la interpretación trabaja sobre una copia. La confirmación compara revisión, sesión, generación de solicitud y caducidad antes y después de validar. El rechazo conserva todo el contexto anterior, incluida la aclaración y la historia. Los resultados antiguos no actualizan decisiones ni registros de simulación. Las pruebas incluyen respuestas fuera de orden en la misma sesión y en sesiones distintas, cancelación durante validación, caducidad durante LLM y negaciones durante aclaración. «No canceles» mantiene pending; «No quiero cancelar, abre Spotify» conserva la petición afirmativa determinada.

Etapa de planes: identidad de plan/acción, revisión, fuente de turno, procedencia validada y estados propuesto/pendiente/validado/reemplazado/cancelado, todos simulados. Historial de 32 elementos y máximo de ocho propuestas activas. Las partes de una petición incompleta dependen de su aclaración, sin programar ejecuciones. Append conserva solicitudes compatibles; modify sustituye únicamente lo afectado; replace reemplaza el plan. La cancelación por alcance retira luces y conserva aplicaciones independientes. Superar el límite produce aclaración sin mutación ni registro de acción. Pruebas específicas conservan IDs, revisiones, instantáneas y ausencia de estados físicos.

Etapa de normalización: se reprodujeron once fallos adicionales en quince casos numéricos/coloquiales antes del cambio. La conjunción de «treinta y cinco» ya no separa acciones. Decimales y fracciones conservan una representación reconocible y se aclaran, sin truncarlos a enteros. «Por ciento» no se interpreta como el prefijo ciento. Se distinguen incrementos y objetivos absolutos tanto al interpretar como al validar. Se admiten peticiones nominales explícitas como «volumen al veinte»; el foco contextual permite «no, al treinta» después de brillo. Negaciones de intensidad como «que no alumbren tanto» se interpretan conservando el referente válido. Resultado de esta etapa: **300 pruebas aprobadas** incluyendo las 218 originales y todas las reproducciones iniciales, salvo el refuerzo del caso de dos luces que ahora exige comprobar ambas propuestas y no solo abstenerse después.
