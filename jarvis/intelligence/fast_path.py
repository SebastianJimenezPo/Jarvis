import re
from .contracts import Interpretation,Kind,ActionProposal
from .catalog import APPLICATIONS,LIGHTS,SCENES,COLORS,validate_action,entity_type
from .language import normalize,mentions,clause_kind,number,color,explicit_request,split_clauses


def action(intent,target,params=None,source=''):
    return ActionProposal(intent=intent,target=target,parameters=params or {},source_clause=source)


def proposal(actions,reason='explicit_immediate_request'):
    return Interpretation(kind=Kind.ACTION_PROPOSAL,actions=actions,immediate=True,reason_code=reason)


class FastPath:
    def __init__(self,context):self.context=context

    def clarify(self,intent,params,group,candidates=None,missing='target'):
        candidates=candidates or []
        self.context.ask(intent,params,missing,candidates)
        labels={'application':'aplicación','light':'luz','scene':'modo','audio':'valor de volumen'}
        question=(f"¿Cuál: {', '.join(candidates)}?" if candidates else f"¿Qué {labels.get(group,'dato')} quieres usar?")
        if missing=='color':question='¿Qué color quieres para las luces?'
        elif missing=='value':question='¿Qué valor entre cero y cien quieres?'
        return Interpretation(kind=Kind.CLARIFICATION,clarification_question=question,reason_code='missing_or_ambiguous_reference')

    def pending(self,text):
        p=self.context.pending
        if not p:return None
        if text in ('si','esa','ese') and len(p.candidates)==1:chosen=p.candidates[0]
        elif text in ('la primera','el primero') and p.candidates:chosen=p.candidates[0]
        elif text in ('la segunda','el segundo') and len(p.candidates)>1:chosen=p.candidates[1]
        else:
            table={'application':APPLICATIONS,'light':LIGHTS,'scene':SCENES}.get(entity_type(p.intent),{})
            found=mentions(text,table);chosen=found[0] if len(found)==1 else None
            selected_color=color(text)
            if chosen is None and selected_color and entity_type(p.intent)=='light':
                matches=[a.target for a in self.context.proposals if a.parameters.get('color')==selected_color and a.target in p.candidates]
                if len(set(matches))==1:chosen=matches[0]
        params=dict(p.parameters)
        if p.missing_parameter=='color':
            selected_color=color(text)
            if selected_color:
                params['color']=selected_color
                chosen=chosen or (p.candidates[0] if len(p.candidates)==1 else None)
        if p.missing_parameter=='value':
            value=number(text)
            if value is not None:
                params['value']=value;chosen=p.candidates[0] if len(p.candidates)==1 else None
        if chosen and (not p.candidates or chosen in p.candidates):
            if p.intent=='set_light_color' and 'color' not in params:
                result=self.clarify(p.intent,params,'light',[chosen],missing='color')
                self.context.pending.prior_actions=p.prior_actions
                return result
            try:a=validate_action(action(p.intent,chosen,params,text))
            except ValueError:return Interpretation(kind=Kind.CLARIFICATION,clarification_question='¿Qué valor entre cero y cien quieres?',reason_code='invalid_parameter')
            self.context.pending=None
            previous=[validate_action(ActionProposal.model_validate(item)) for item in p.prior_actions]
            return proposal([*previous,a],'clarification_resolved')
        p.attempts+=1
        if p.attempts>=self.context.config.max_clarification_attempts:
            self.context.pending=None
            return Interpretation(kind=Kind.CANCEL,reason_code='clarification_attempt_limit')
        return Interpretation(kind=Kind.CLARIFICATION,clarification_question='¿A cuál te refieres?',reason_code='unresolved_clarification')

    def interpret(self,raw):
        text=normalize(raw);self.context.expire()
        text=re.sub(r'^jarvis[ ,]*','',text)
        text=re.sub(r'^y\s+','',text)
        # STT may insert a comma after a polite prefix. Remove the filler,
        # keeping the actual action clause available to independent validation.
        text=re.sub(r'^por favor(?:\s*[,;]\s*|\s+)','',text)
        text=re.sub(r'\s*[,;]?\s+por favor$','',text).strip()
        from .speech_act import replacement_request,correction_text
        replacement=replacement_request(text)
        if replacement:
            self.context.cancel();text=replacement
        if re.fullmatch(r'(?:bueno[, ]+)?(?:olvida|cancela|descarta) (?:lo de )?(?:las luces|la luz|la iluminacion)',text):
            self.context.cancel('light')
            return Interpretation(kind=Kind.CANCEL,reason_code='selective_cancel',response='Descarté las propuestas de luces. No he ejecutado ninguna acción.')
        if not text:return Interpretation(kind=Kind.CONVERSATION,response='',reason_code='empty')
        cancel_text=' '.join(re.sub(r'\b(?:jarvis|por favor)\b','',text).strip(' ,').split())
        if (cancel_text.replace(',','') in ('no','no olvidalo','olvida eso','olvida todo','olvida lo anterior','mejor ninguna','no ninguna','ninguna','espera no','no gracias','no hagas nada','mejor no cambies nada')
                or re.fullmatch(r'(?:cancela|cancelar|cancelalo|cancelala|cancelame|cancele)(?:\s+(?:eso|esto|todo|la solicitud|la orden|la propuesta|lo anterior))?',cancel_text)):
            self.context.cancel()
            return Interpretation(kind=Kind.CANCEL,reason_code='user_cancel')
        if self.context.pending:
            if re.fullmatch(r'no (?:canceles(?: nada)?|quiero cancelar|canceles la (?:solicitud|propuesta))',text):
                return Interpretation(kind=Kind.CLARIFICATION,clarification_question='Mantengo la solicitud pendiente. ¿Qué opción prefieres?',reason_code='keep_pending')
            if re.match(r'^no[, ]+(?:esa no|ese no|era\b)',text):
                p=self.context.pending
                table={'application':APPLICATIONS,'light':LIGHTS,'scene':SCENES}.get(entity_type(p.intent),{})
                rejected=mentions(text,table)
                p.candidates=[target for target in p.candidates if target not in rejected]
                return Interpretation(kind=Kind.CLARIFICATION,clarification_question='Entendido. ¿Qué otra opción prefieres?',reason_code='alternative_rejected')
            text=re.sub(r'^no quiero cancelar[,;]\s*','',text)
        if text in ('hola','buenos dias','buenas tardes','buenas noches','gracias','gracias jarvis','perfecto','listo','como estas','tu como estas','perfecto como estas','perfecto tu como estas','que mas todo bien','me escuchas','me escuchas bien','hola me escuchas bien'):
            reply=('Con gusto' if text.startswith('gracias') else 'Sí, te escucho' if 'me escuchas' in text else
                   'Todo funcionando bien' if 'como estas' in text or 'todo bien' in text else 'Listo' if text in ('perfecto','listo') else 'Hola')
            return Interpretation(kind=Kind.CONVERSATION,response=reply,reason_code='small_talk')
        if text.replace(',','') in ('adios','hasta luego','chao','bueno hablamos luego','hablamos luego','nos vemos'):
            return Interpretation(kind=Kind.CONVERSATION,response='Hasta luego',reason_code='farewell')
        if re.search(r'\b(?:noticias de hoy|precio actual|clima de hoy|cotizacion actual|resultados en vivo)\b',text):
            return Interpretation(kind=Kind.CONVERSATION,response='No tengo acceso a información en vivo ni he consultado internet.',reason_code='no_live_data')
        global_guard=clause_kind(text)
        from .speech_act import analyze
        if analyze(text).reason=='whole_turn_veto':
            return Interpretation(kind=Kind.NEGATED,negated=True,reason_code='whole_turn_veto')
        if global_guard=='cancel':
            self.context.cancel();return Interpretation(kind=Kind.CANCEL,reason_code='user_cancel')
        if global_guard in ('unsupported','hypothetical','deferred_request','preference','conversation'):
            if global_guard=='preference':self.context.preferences['last_preference']=raw[:300]
            return Interpretation(kind=Kind(global_guard),condition=raw[:500] if global_guard=='deferred_request' else None,
                                  reason_code='language_guard')
        if self.context.pending:
            # A fresh request replaces a pending question rather than answering it.
            if explicit_request(text) or global_guard=='negated':self.context.pending=None
            else:return self.pending(text)
        # Corrections require one compatible earlier proposal; preserve other proposals in a multi-action plan.
        if correction_text(text) or re.match(r'^no[, ]+(?:steam|spotify|chrome|discord)\b',text):
            corrected=self.correction(text)
            if corrected:return corrected
        clauses=split_clauses(text)
        if len(clauses)>8:return Interpretation(kind=Kind.CLARIFICATION,clarification_question='¿Podemos hacerlo en menos pasos?',reason_code='too_many_actions')
        actions=[];negative=False;carry=None
        for clause in clauses:
            clause=clause.strip(' ,')
            if clause in ('voy a jugar','voy a estudiar') and len(clauses)>1:continue
            guard=clause_kind(clause)
            if guard=='negated':negative=True;carry=None;continue
            if guard:
                return Interpretation(kind=Kind(guard),reason_code='clause_guard')
            candidate=self.parse_action(clause,text,carry)
            if isinstance(candidate,Interpretation):
                if candidate.kind==Kind.CLARIFICATION and self.context.pending:
                    self.context.pending.prior_actions=[a.model_dump() for a in actions]
                return candidate
            if candidate:
                actions.extend(candidate);carry=candidate[-1].intent
            elif clause and not (negative and re.fullmatch(r'(?:spotify|chrome|discord|steam)',clause)):
                return None
        if actions:return proposal(actions)
        if negative:return Interpretation(kind=Kind.NEGATED,negated=True,reason_code='explicit_negation')
        return None

    def correction(self,text):
        if not self.context.proposals:
            return self.clarify('set_light_color',{},'light')
        c=color(text);apps=mentions(text,APPLICATIONS);value=number(text)
        previous=self.context.proposals
        group='light' if c or 'suaves' in text or 'brillo' in text else 'application' if apps else None
        matches=[a for a in previous if group is None or entity_type(a.intent)==group]
        if value is not None and group is None:
            focus=self.context.focus
            matches=[a for a in matches if focus and a.intent==focus['intent'] and a.target==focus['target'] and a.intent in ('set_volume','set_light_brightness')]
        if c:
            colored=[a for a in matches if a.intent=='set_light_color']
            if colored:matches=colored
        elif group=='light' and ('suaves' in text or 'brillo' in text):
            brightness=[a for a in matches if a.intent=='set_light_brightness']
            if brightness:matches=brightness
        if len(matches)!=1:return self.clarify('set_light_color' if group=='light' else 'close_application',{},group or 'application',[a.target for a in matches])
        old=matches[0];params=dict(old.parameters);intent=old.intent;target=old.target
        if c:intent='set_light_color';params={'color':c}
        elif group=='light' and ('suaves' in text or 'brillo' in text):intent='set_light_brightness';params={'delta':-10}
        elif apps:target=apps[0]
        elif value is not None:
            if intent not in ('set_volume','set_light_brightness'):return None
            params={'value':value}
        elif 'como estaba' in text or 'anterior' in text:
            return Interpretation(kind=Kind.CLARIFICATION,clarification_question='No conozco el estado físico anterior. ¿Qué valor quieres?',reason_code='unknown_physical_state')
        else:return None
        try:new=validate_action(action(intent,target,params,text))
        except ValueError:return Interpretation(kind=Kind.CLARIFICATION,clarification_question='¿Qué valor entre cero y cien quieres?',reason_code='invalid_parameter')
        return proposal([new],'context_correction')

    def parse_action(self,text,whole,carry=None):
        original=text
        text=re.sub(r'^por favor\s+','',text)
        text=re.sub(r'^(?:quiero|necesito) que abras\b','abre',text)
        text=re.sub(r'^(?:quiero|necesito) que cierres\b','cierra',text)
        apps=mentions(text,APPLICATIONS);lights=mentions(text,LIGHTS);scene=mentions(text,SCENES)
        c=color(text);value=number(text);intent=None;params={};group=None
        if 'como estaba' in text or 'igual que antes' in text:
            return Interpretation(kind=Kind.CLARIFICATION,clarification_question='No conozco el estado físico anterior. ¿Qué valor quieres?',reason_code='unknown_physical_state')
        if re.search(r'\b(?:abre|abrir|abierto|abierta)\b',text):intent='open_application';group='application'
        elif re.search(r'\b(?:cierra|cerrar|cierralo|cierrala)\b',text):intent='close_application';group='application'
        elif re.search(r'\b(?:enfoca|enfocar|trae al frente)\b',text):intent='focus_application';group='application'
        elif apps and carry in ('open_application','close_application','focus_application'):
            intent=carry;group='application'
        elif lights and carry in ('turn_on_light','turn_off_light'):
            intent=carry;group='light'
        elif scene and explicit_request(text):intent='activate_scene';group='scene'
        elif ('brillo' in text or ('suaves' in text and self.context.targets('light'))):
            intent='set_light_brightness';group='light'
            params={'value':value} if value is not None else {'delta':-10 if re.search(r'baja|reduce|suave|disminu',text) else 10}
        elif c and (lights or explicit_request(text)):
            intent='set_light_color';group='light';params={'color':c}
        elif lights and re.search(r'\bcolor\b',text) and explicit_request(text):
            intent='set_light_color';group='light'
        elif re.search(r'\b(?:apaga|apagar|apagalo|apagala)\b',text):intent='turn_off_light';group='light'
        elif re.search(r'\b(?:enciende|prende|encender)\b',text):intent='turn_on_light';group='light'
        elif 'volumen' in text or re.match(r'^(?:bajale|subele)\b',text):
            group='audio'
            if re.search(r'\b(?:quita el silencio|desilencia)\b',text):intent='unmute_audio'
            elif 'silencia' in text or 'mudo' in text:intent='mute_audio'
            elif value is not None and re.search(r'\b(?:baja|reduce|disminuye|sube|aumenta)\b.*\b(?:en|un|unos)\s+-?\d+',text):
                intent='decrease_volume' if re.search(r'baja|reduce|disminu',text) else 'increase_volume'
                params={'amount':value}
            elif value is not None:intent='set_volume';params={'value':value}
            elif re.search(r'baja|reduce|disminu|bajita',text):intent='decrease_volume';params={'amount':10}
            elif re.search(r'sube|aumenta|alto',text):intent='increase_volume';params={'amount':10}
            else:intent='set_volume'
        elif re.search(r'\b(?:silencia|quita el sonido)\b',text):intent='mute_audio';group='audio'
        elif re.search(r'\b(?:quita el silencio|activa el sonido)\b',text):intent='unmute_audio';group='audio'
        elif re.search(r'\b(?:pausa|pausar)\b',text):intent='pause_music';group='music'
        elif re.search(r'\b(?:siguiente cancion|siguiente pista)\b',text):intent='next_track';group='music'
        elif re.search(r'\b(?:cancion anterior|pista anterior)\b',text):intent='previous_track';group='music'
        elif re.match(r'^(?:busca|buscar)\b',text):intent='search_music';group='music';params={'query':re.sub(r'^(?:busca|buscar)\s+','',text)}
        elif re.match(r'^(?:reproduce|quiero escuchar|pon musica|pon la musica)\b',text):
            intent='play_music';group='music';query=re.sub(r'^(?:reproduce|quiero escuchar|pon (?:la )?musica)\s*','',text)
            if query:params={'query':query}
        elif text in ('dame el estado del sistema','muestra el estado del sistema'):
            intent='get_system_status';group='system'
        if not intent:return None
        # A mention alone is not an imperative; allow only documented direct request forms.
        if not explicit_request(text) and not re.match(r'^quiero (?:escuchar|(?:las? |el |los? )?(?:luz|luces))\b',text) and not carry and not re.search(r'\babierto\b',text):return None
        if group=='application':
            pronoun=bool(re.search(r'\b(?:cierralo|cierrala|abrelo|esa|ese|la aplicacion|el programa)\b',text))
            targets=apps or (self.context.targets(group) if pronoun else [])
        elif group=='light':targets=lights or mentions(whole,LIGHTS) or self.context.targets(group)
        elif group=='scene':targets=scene
        else:targets=[{'audio':'system_audio','music':'music_player','system':'system'}[group]]
        if len(targets)!=1:
            return self.clarify(intent,params,group,targets)
        if intent=='set_light_color' and 'color' not in params:
            return self.clarify(intent,params,group,targets,missing='color')
        if intent=='set_volume' and 'value' not in params:
            return self.clarify(intent,params,group,targets,missing='value')
        candidate=action(intent,targets[0],params,original)
        try:validate_action(candidate)
        except ValueError:
            if intent in ('set_volume','set_light_brightness') and 'value' in params:
                return self.clarify(intent,{},group,targets,missing='value')
            return Interpretation(kind=Kind.CLARIFICATION,clarification_question='¿Qué valor válido entre cero y cien quieres?',reason_code='invalid_parameter')
        return [candidate]
