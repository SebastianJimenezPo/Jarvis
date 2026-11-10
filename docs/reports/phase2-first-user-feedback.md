# Primera prueba física de Fase 2

El usuario reportó activación real, respuestas habladas, varios turnos sin repetir Jarvis y respuestas distintas para gracias/adiós. También reportó un fallo: decir solo Jarvis disparaba la respuesta genérica sobre control de aplicaciones; otras frases de prueba también recibían esa respuesta.

Los registros muestran sesiones y varios turnos reales, reproducción y cierre por despedida. El primer turno comenzaba inmediatamente sobre el pre-roll. El texto de esas transcripciones no se conservó por privacidad; no es posible afirmar qué palabra exacta produjo STT ni confirmar todas las frases pronunciadas.

Corrección: el primer turno con un único token desconocido se considera ambiguo y mantiene la escucha, sin modificar su transcripción ni presentarlo como una orden. Los saludos conocidos y las frases de varias palabras siguen disponibles. Es una medida conservadora: también puede silenciar una solicitud desconocida de una sola palabra en ese primer turno. Se ampliaron variantes explícitas de «me escuchas» y se reservó el aviso de aplicaciones a peticiones de ese tipo. Otras frases desconocidas reciben una aclaración breve.

Se añadió al menú el diagnóstico voluntario que repite el texto reconocido en voz sin habilitar registros de texto. Este modo omite el filtro de ambigüedad para permitir escuchar el resultado de STT. Falta repetir la prueba física después de aplicar la corrección; no se declara resuelto acústicamente sin esa comprobación.
