"""Bounded local wording; never claims that simulated state is physical state."""
def describe(call):
    if call.tool == 'applications.open': return 'abrir '+call.target.title()
    if call.tool == 'system_audio.set_volume': return f"ajustar el volumen al {call.parameters.get('value')}%"
    if call.tool == 'system_audio.set_mute': return 'silenciar el audio'
    if call.tool == 'media.pause': return 'pausar la música'
    return 'consultar el volumen (estado real no verificado)'


def response(outcome):
    if outcome.review:
        items=outcome.review.proposed_plan.items
        actions='; '.join(describe(item.call) for item in items) or 'descartar las propuestas indicadas'
        if outcome.review.purpose == 'edit':
            return f'Propongo corregir el borrador: {actions}. Seguirá retenido, sin simular acciones. ¿Confirmas esta revisión?'
        return f'Propongo simular: {actions}. ¿Confirmas esta simulación?'
    if outcome.error:
        if outcome.error == 'policy_rejected': return 'No pude validar la intención de esa propuesta. No he ejecutado acciones.'
        if outcome.disposition == 'stale': return ''
        if outcome.error == 'review_invalid': return 'Esa propuesta ya no está vigente. Pídemela otra vez.'
        return 'El intérprete no está disponible. Puedo atender órdenes directas, como abre Steam.'
    op=outcome.decision.operation if outcome.decision else None
    if op == 'clarify': return '¿Qué aplicación o ajuste quieres? Indica el nombre o el valor que falta.'
    if op == 'negated': return 'De acuerdo, no realizaré la acción que has negado.'
    if op == 'deferred': return 'Todavía no puedo programar acciones futuras. No he iniciado esa acción.'
    if op == 'hypothetical': return 'Lo tomo como un supuesto; no iniciaré acciones.'
    if op == 'conversation': return 'Entendido. No lo tomo como una orden para actuar.'
    if op == 'unsupported': return 'Esa función todavía no está disponible en este perfil.'
    if op == 'preference': return 'No guardaré esa preferencia de forma permanente en esta versión.'
    if outcome.plan.status == 'withheld' and outcome.disposition == 'held':
        return 'La propuesta queda retenida: '+('; '.join(describe(i.call) for i in outcome.plan.items) or 'sin acciones')+'. Corregirla no autoriza su simulación.'
    if outcome.disposition == 'cancelled': return 'Descarté las propuestas pendientes de esta sesión. No he revertido acciones físicas.'
    if outcome.results and op != 'query_state': return 'En simulación: '+'; '.join(describe(i.call) for i in outcome.plan.items)+'.'
    return outcome.message
