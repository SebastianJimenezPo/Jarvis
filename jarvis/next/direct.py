"""Whole-utterance grammar, not a general Spanish interpreter or a word allowlist."""
import re
import unicodedata
from .contracts import ActionChange, ContextView, Decision, Span, ToolCall


def direct_decision(text: str, context: ContextView):
    normalized = ''.join(c for c in unicodedata.normalize('NFD', text.casefold())
                         if not unicodedata.combining(c))
    normalized = ' '.join(normalized.split())
    # Keep quotes, question marks and clauses. A terminal period is harmless.
    normalized = normalized.removesuffix('.')
    evidence = Span(start=0, end=len(text))
    common = dict(plan_id=context.plan_id, expected_revision=context.revision, evidence=evidence)
    if normalized in ('autoriza la simulacion', 'simula el plan') and context.items and context.status == 'withheld':
        return Decision(operation='authorize_plan', **common)
    if match := re.fullmatch(r'(?:no,? )?mejor (steam|spotify|chrome|discord)', normalized):
        apps = [item for item in context.items if item.call.tool == 'applications.open']
        if len(apps) == 1 and context.status == 'withheld':
            return Decision(operation='modify_plan', temporal='now',
                changes=(ActionChange(action_id=apps[0].action_id,target=match[1]),), **common)
    if match := re.fullmatch(r'abre (steam|spotify|chrome|discord),? pero todavia no hagas nada', normalized):
        return Decision(operation='create_plan', temporal='now', retained=True,
            actions=(ToolCall(tool='applications.open',target=match[1],evidence=evidence),), **common)
    if normalized in ('cancela', 'olvida todo lo anterior'):
        return Decision(operation='cancel_all', **common)
    if normalized in ('todavia no hagas nada', 'no hagas nada todavia'):
        return Decision(operation='hold', **common)
    if normalized in ('no canceles', 'no quiero cancelar'):
        return Decision(operation='negated', **common)
    call = None
    if match := re.fullmatch(r'abre (steam|spotify|chrome|discord)', normalized):
        call = ToolCall(tool='applications.open', target=match[1], evidence=evidence)
    elif match := re.fullmatch(r'volumen al (100|[1-9]?\d)\s*%', normalized):
        call = ToolCall(tool='system_audio.set_volume', target='system_audio',
                        parameters={'value': int(match[1])}, evidence=evidence)
    elif normalized == 'pausa la musica':
        call = ToolCall(tool='media.pause', target='music_player', evidence=evidence)
    elif normalized == 'silencia el audio':
        call = ToolCall(tool='system_audio.set_mute', target='system_audio',
                        parameters={'muted': True}, evidence=evidence)
    elif normalized == 'consulta el volumen':
        call = ToolCall(tool='system_audio.get_volume', target='system_audio', evidence=evidence)
    if call:
        return Decision(operation='query_state' if call.tool=='system_audio.get_volume' else 'create_plan',
                        temporal='now', actions=(call,), **common)
    return None
