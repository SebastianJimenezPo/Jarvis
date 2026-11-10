import re
from .contracts import Kind
from .catalog import validate_action,entity_type,APPLICATIONS,LIGHTS,SCENES
from .language import normalize,clause_kind,split_clauses,mentions,color,number,explicit_request


class SafetyValidator:
    """Independent semantic authorization checks; schema alone is insufficient."""
    def validate(self,result,text,context,trusted_fast=False):
        if result.kind!=Kind.ACTION_PROPOSAL:return result
        normalized=normalize(text)
        if clause_kind(normalized) in ('unsupported','hypothetical','deferred_request','preference','conversation','cancel'):
            raise ValueError('Speech act does not authorize immediate proposals')
        actual_clauses=split_clauses(normalized)
        for a in result.actions:
            validate_action(a)
            if trusted_fast:
                # Fast path still passes syntax/polarity checks; context corrections may carry earlier plan items.
                if result.reason_code in ('context_correction','clarification_resolved'):continue
            source=normalize(a.source_clause or normalized)
            matches=[c for c in actual_clauses if source in c]
            if not matches or any(clause_kind(c) is not None for c in matches):
                raise ValueError('Ungrounded or guarded source clause')
            clause=matches[0]
            group=entity_type(a.intent)
            if not trusted_fast and group=='audio' and not (re.search(r'volumen|musica|sonido|audio|sonando|suene',clause) or context.targets('audio')):
                raise ValueError('No audio-domain reference')
            table={'application':APPLICATIONS,'light':LIGHTS,'scene':SCENES}.get(group)
            if table:
                entities=mentions(clause,table)
                if not entities and trusted_fast:entities=mentions(normalized,table)
                if not entities:
                    candidates=context.targets(group)
                    if len(candidates)!=1 or a.target!=candidates[0]:raise ValueError('Missing target evidence')
                elif a.target not in entities:raise ValueError('Target does not match user request')
            if a.intent=='set_light_color' and color(clause)!=a.parameters['color']:raise ValueError('Color not grounded')
            if 'value' in a.parameters and number(clause)!=a.parameters['value']:raise ValueError('Value not grounded')
            if 'amount' in a.parameters:
                expected=number(clause)
                if a.parameters['amount']!=(expected if expected is not None else 10):raise ValueError('Relative amount not grounded')
            if 'delta' in a.parameters:
                if a.parameters['delta'] not in (-10,10):raise ValueError('Only configured small brightness steps are supported')
            if not trusted_fast:
                request=explicit_request(clause) or bool(re.search(r'\b(?:quiero|necesito)\b',clause))
                contextual_complaint=bool(re.search(r'fuerte|duro|sordo|suave|encandila|no se oye',clause))
                if not request and not contextual_complaint:raise ValueError('No actionable request evidence')
                if a.intent in ('decrease_volume','increase_volume'):
                    lower=bool(re.search(r'baja|reduce|disminu|fuerte|duro|sordo|suave|bajita',clause))
                    higher=bool(re.search(r'sube|aumenta|alto|no se oye',clause))
                    if (a.intent=='decrease_volume' and not lower) or (a.intent=='increase_volume' and not higher):
                        raise ValueError('Unsubstantiated volume direction')
                elif a.intent.startswith(('open_','close_','focus_')):
                    trigger={'open_application':r'abre|abrir|abierto','close_application':r'cierra|cerrar|cierralo','focus_application':r'enfoca|frente'}[a.intent]
                    if not re.search(trigger,clause):raise ValueError('Wrong application action')
                elif a.intent in ('turn_on_light','turn_off_light'):
                    trigger=r'enciende|prende|alumbra|necesito luz' if a.intent=='turn_on_light' else r'apaga|oscur'
                    if not re.search(trigger,clause):raise ValueError('Wrong light action')
                elif a.intent=='pause_music':
                    if not re.search(r'musica|cancion|pista|sonando',clause) or not re.search(r'pausa|deten|interrumpe|para |no siga',clause):
                        raise ValueError('Missing music pause evidence')
                elif a.intent=='set_light_brightness':
                    if not re.search(r'brillo|suave|tenue|encandila|ilumin|alumbr',clause):
                        raise ValueError('Missing brightness evidence')
                elif a.intent in ('play_music','search_music') and 'query' in a.parameters:
                    if normalize(a.parameters['query']) not in normalized:raise ValueError('Invented music query')
        return result
