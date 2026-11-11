"""Conservative speech-act and scope analysis, independent of proposal creation.

Recognizers identify grammatical constructions (temporal subordinate clauses,
relative past references, corrections and final vetoes), not just temporal words.
Unknown mixed scope is withheld as a whole, rather than inventing an ordering.
"""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SpeechAct:
    kind: str|None
    temporal_scope: str='immediate'
    reason: str='no_global_guard'
    relative_past_reference: bool=False


def correction_text(text):
    return bool(re.match(r'^(?:no[, ]+)?(?:mejor\b|al\s+\w+|(?:azul|rojo|verde|blanc|morad|amarill)\w*\b)|^(?:no era |en realidad |que esten )',text))


def replacement_request(text):
    from .language import explicit_request
    match=re.match(r'^(?:bueno[, ]+)?(?:olvida eso|olvida lo anterior|cancela lo anterior)[,; ]+(?:mejor\s+)?(.+)$',text)
    if match and explicit_request(match[1]):return match[1]
    return None


def analyze(text):
    from .language import normalize,explicit_request
    text=normalize(text)
    replacement=replacement_request(text)
    if replacement:return analyze(replacement)
    if re.search(r'\b(?:ignora (?:las |tus )?(?:restricciones|reglas)|powershell|ejecuta (?:un )?(?:comando|codigo)|cmd exe|borra archivos|formatea)\b',text):
        return SpeechAct('unsupported',reason='unsupported_operation')
    # Explicit abandonment differs from negating the verb "cancelar".
    if re.search(r'\b(?:olvidalo|olvida eso|cancela todo|espera[, ]+(?:mejor[, ]+)?no|no lo hagas)\b',text):
        return SpeechAct('cancel',reason='explicit_abandonment')
    if re.search(r'\b(?:que pasaria|como si|si (?:pudiera|pusiera|apagara|bajara|abriera)|hipoteticamente|suponiendo)\b',text):
        return SpeechAct('hypothetical','hypothetical','counterfactual')
    if re.search(r'\b(?:me gustaria|estaria bien|quisiera algun dia|estoy pensando en)\b',text):
        return SpeechAct('hypothetical','hypothetical','desire_or_deliberation')
    # Time belongs to the action's subordinate clause, including postposed clauses.
    if re.search(r'\b(?:cuando|en cuanto|tan pronto como|siempre que|hasta que|a menos que|con tal de que|a condicion de que|mientras|apenas)\b',text):
        return SpeechAct('deferred_request','condition','subordinate_condition')
    if re.search(r'\b(?:una vez)\s+(?:que\s+)?(?:termine|acabe|finalice|haya|este|pueda|salga|cierre|guarde)\b',text):
        return SpeechAct('deferred_request','condition','completion_condition')
    if re.search(r'\bal\s+(?:acabar|terminar|finalizar|salir|cerrar|guardar|volver|llegar|iniciar|abrir)\b',text):
        return SpeechAct('deferred_request','after','infinitive_temporal_clause')
    if re.search(r'\b(?:antes de|tras)\s+(?:que\s+)?\w+',text):
        return SpeechAct('deferred_request','condition','relative_temporal_clause')
    if re.search(r'\b(?:manana|despues|mas tarde|esta noche|dentro de|algun dia|luego de|si\s+\w+|en (?:\d+|cinco|diez|veinte|treinta|una|dos) (?:minutos|horas|segundos))\b',text):
        return SpeechAct('deferred_request','future','explicit_future_or_condition')
    if re.search(r'\b(?:todavia no|aun no|no ahora|por ahora no)\b',text):
        return SpeechAct('deferred_request','withheld','not_yet')
    if re.search(r'\b(?:no hagas (?:nada|eso)|no (?:lo|la|las|los) (?:cambies|abras|cierres|apagues|enciendas)|no era una orden|solo estaba preguntando)\b',text):
        return SpeechAct('negated','withheld','whole_turn_veto')
    if re.search(r'\b(?:ni se te ocurra|no se te ocurra|de ningun modo|esta prohibido)\b',text):
        return SpeechAct('negated','withheld','whole_turn_veto')
    if re.match(r'^(?:yo )?(?:prefiero|me gusta|recuerda|mi preferencia|quisiera recordar)\b',text):
        return SpeechAct('preference',reason='preference')
    relative=bool(re.search(r'\bque (?:use|usaba|utilice|abri|cerre|tenia)\b',text)) and explicit_request(text)
    if not relative and re.search(r'\b(?:ayer|el otro dia|mi (?:amigo|hermano) (?:dijo|siempre)|estaba pensando|dijeron que)\b',text):
        return SpeechAct('conversation','past','past_comment')
    if re.search(r'^(?:como (?:puedo|se)|que (?:es|significa)|por que|puedes (?:abrir programas|cerrar aplicaciones automaticamente)|sabes |es posible|podrias explicarme)\b',text):
        return SpeechAct('conversation',reason='question')
    if re.match(r'^no (?:se (?:oye|escucha)|quiero que (?:suene|se escuche) (?:tan|muy) fuerte)',text):return SpeechAct(None)
    if correction_text(text):return SpeechAct(None,reason='contextual_modification')
    if re.search(r'^(?:no (?:quiero que |debes |vayas a )?|nunca |jamas |evita )',text):
        return SpeechAct('negated',reason='negative_clause')
    return SpeechAct(None,relative_past_reference=relative)
