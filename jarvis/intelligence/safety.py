"""Authorization uses actual turn evidence plus bounded valid context, never route labels."""
import re
import copy
from .contracts import Kind,Interpretation,ActionProposal
from .catalog import validate_action,entity_type,APPLICATIONS,LIGHTS,SCENES
from .language import normalize,clause_kind,split_clauses,mentions,color,number,explicit_request
from .speech_act import analyze,correction_text


class SafetyValidator:
    def validate(self,result,text,context,trusted_fast=False):
        if result.kind!=Kind.ACTION_PROPOSAL:return result
        normalized=normalize(text);speech=analyze(normalized)
        if speech.kind in ('unsupported','hypothetical','deferred_request','preference','conversation','cancel') or speech.reason=='whole_turn_veto':
            raise ValueError('Speech act does not authorize immediate proposals')
        clauses=split_clauses(normalized)
        evidence=[]
        for a in result.actions:
            validate_action(a)
            proof=self.context_evidence(a,normalized,context)
            if proof and proof.get('prior'):
                # A held partial plan needs grounded origin evidence as well.
                origins=[h['user'] for h in context.history if normalize(a.source_clause) and normalize(a.source_clause) in normalize(h['user'])]
                if not origins:raise ValueError('No origin for held partial action')
                origin_context=copy.deepcopy(context);origin_context.pending=None
                self.validate(Interpretation(kind=Kind.ACTION_PROPOSAL,immediate=True,actions=[a]),origins[-1],origin_context)
                evidence.append({'target':'resolved_from_context','parameters':{k:'resolved_from_context' for k in a.parameters}})
                continue
            source=normalize(a.source_clause or normalized)
            matches=[c for c in clauses if source in c]
            if proof and source in normalized:matches=[normalized]
            # Contextual answers can be short, but all current-turn guards still apply.
            if not matches or any(clause_kind(c) is not None for c in matches):
                raise ValueError('Ungrounded or guarded source clause')
            clause=matches[0];group=entity_type(a.intent)
            table={'application':APPLICATIONS,'light':LIGHTS,'scene':SCENES}.get(group)
            target_source='explicit_current_turn'
            if table:
                entities=mentions(clause,table)
                if not entities:
                    # Elliptical conjunctions can share an explicit domain/target.
                    entities=mentions(normalized,table) if group=='light' else []
                if entities and a.target not in entities:raise ValueError('Target does not match current request')
                if not entities:
                    candidates=context.targets(group)
                    if not (proof or (len(candidates)==1 and a.target==candidates[0])):
                        raise ValueError('Missing target evidence')
                    target_source='confirmed_by_clarification' if proof and proof.get('clarification') else 'resolved_from_context'
            origins={}
            for key,value in a.parameters.items():
                actual=color(clause) if key=='color' else number(clause) if key in ('value','amount') else None
                if key in ('color','value'):
                    if actual==value:origins[key]='explicit_current_turn'
                    elif proof and proof.get('inherited',{}).get(key)==value:origins[key]='resolved_from_context'
                    else:raise ValueError('Parameter not grounded in turn/context')
                elif key=='amount':
                    if value!=(actual if actual is not None else 10):raise ValueError('Relative amount not grounded')
                    origins[key]='explicit_current_turn' if actual is not None else 'default_configured'
                elif key=='delta':
                    if value not in (-10,10):raise ValueError('Unsupported brightness step')
                    lower=bool(re.search(r'baja|reduce|disminu|suave|tenue|encandila|menos|no alumbre',clause))
                    higher=bool(re.search(r'sube|aumenta|mas (?:brillo|fuerte|luz)',clause))
                    if (value<0 and not lower) or (value>0 and not higher):raise ValueError('Brightness direction not grounded')
                    origins[key]='default_configured'
                elif key=='query':
                    if normalize(value) not in normalized:raise ValueError('Invented music query')
                    origins[key]='explicit_current_turn'
            if not proof:self.check_intent(a,clause,normalized,context)
            evidence.append({'target':target_source,'parameters':origins})
        self.last_evidence=evidence
        return result

    def context_evidence(self,a,text,context):
        """Reconstruct the exact allowed operation instead of trusting reason_code."""
        p=context.pending
        if p:
            if context.clock()>=p.expires or p.session_id!=context.session_id:return None
            if any(a.model_dump()==item for item in p.prior_actions):return {'prior':True}
            if a.intent!=p.intent:return None
            group=entity_type(a.intent);table={'application':APPLICATIONS,'light':LIGHTS,'scene':SCENES}.get(group,{})
            explicit=mentions(text,table) if table else []
            ordinal=(text in ('si','esa','ese') and len(p.candidates)==1 and a.target==p.candidates[0]) or (
                text in ('la primera','el primero') and p.candidates and a.target==p.candidates[0]) or (
                text in ('la segunda','el segundo') and len(p.candidates)>1 and a.target==p.candidates[1])
            target_ok=a.target in explicit or ordinal or (p.missing_parameter in ('color','value') and p.candidates==[a.target])
            if not target_ok or (p.candidates and a.target not in p.candidates):return None
            expected=dict(p.parameters)
            if p.missing_parameter=='color':expected['color']=color(text)
            if p.missing_parameter=='value':expected['value']=number(text)
            if a.parameters!=expected:return None
            return {'clarification':True,'inherited':p.parameters}
        if not correction_text(text):return None
        if context.clock()-context.updated>context.config.context_ttl_seconds:return None
        group=entity_type(a.intent)
        compatible=[old for old in context.proposals if entity_type(old.intent)==group]
        if group=='application':
            return {'correction':True} if len(compatible)==1 and compatible[0].intent==a.intent and a.target in mentions(text,APPLICATIONS) else None
        targets={old.target for old in compatible}
        if targets!={a.target}:return None
        allowed=(a.intent=='set_light_color' and color(text)==a.parameters.get('color')) or (
            a.intent in ('set_volume','set_light_brightness') and number(text)==a.parameters.get('value') and number(text) is not None) or (
            a.intent=='set_light_brightness' and a.parameters=={'delta':-10} and re.search(r'suave|brillo|alumbr|fuerte|baj',text))
        return {'correction':True} if allowed else None

    def check_intent(self,a,clause,whole,context):
        clause=re.sub(r'^(?:y|pero)\s+','',clause)
        request=explicit_request(clause) or bool(re.search(r'\b(?:quiero|necesito)\b',clause))
        complaint=bool(re.search(r'fuerte|duro|sordo|suave|encandila|no se oye',clause))
        # Conjoined app names inherit the explicitly stated app operation only.
        carry=(entity_type(a.intent)=='application' and a.target in mentions(clause,APPLICATIONS) and
               any(clause_kind(c) is None and explicit_request(c) and re.search({'open_application':r'\b(?:abre|abrir)\b','close_application':r'\b(?:cierra|cerrar)\b','focus_application':r'\b(?:enfoca|frente)\b'}[a.intent],c) for c in split_clauses(whole)))
        desired_state=bool(re.search(r'\babierto\b',clause) and re.search(r'\b(?:quiero|necesito)\b',whole))
        if not request and not complaint and not carry and not desired_state:raise ValueError('No actionable request evidence')
        if a.intent in ('decrease_volume','increase_volume'):
            if not (re.search(r'volumen|musica|sonido|audio|sonando|suene',clause) or context.targets('audio')):raise ValueError('No audio-domain reference')
            lower=bool(re.search(r'baja|reduce|disminu|fuerte|duro|sordo|suave|bajita',clause))
            higher=bool(re.search(r'sube|aumenta|alto|no se oye',clause))
            if (a.intent=='decrease_volume' and not lower) or (a.intent=='increase_volume' and not higher):raise ValueError('Unsubstantiated volume direction')
        elif a.intent.startswith(('open_','close_','focus_')):
            trigger={'open_application':r'abre|abrir|abierto','close_application':r'cierra|cerrar|cierralo|cierrala','focus_application':r'enfoca|frente'}[a.intent]
            if not re.search(trigger,clause) and not carry:raise ValueError('Wrong application action')
        elif a.intent in ('turn_on_light','turn_off_light'):
            trigger=r'enciende|prende|alumbra|necesito luz' if a.intent=='turn_on_light' else r'apaga|oscur'
            if not re.search(trigger,clause):raise ValueError('Wrong light action')
        elif a.intent=='pause_music':
            if not re.search(r'musica|cancion|pista|sonando',clause) and clause not in ('pausa','pausar'):raise ValueError('Missing music domain')
            if not re.search(r'pausa|deten|interrumpe|para |no siga',clause):raise ValueError('Missing pause evidence')
        elif a.intent=='set_light_brightness':
            if not re.search(r'brillo|suave|tenue|encandila|ilumin|alumbr',clause):raise ValueError('Missing brightness evidence')
        elif a.intent=='set_light_color' and color(clause) is None:raise ValueError('Missing color evidence')
        elif a.intent=='set_volume':
            if not ('volumen' in clause or context.targets('audio')):raise ValueError('Missing volume domain')
        elif a.intent=='get_system_status':
            if not re.search(r'estado (?:del )?sistema',clause):raise ValueError('Missing system status request')
        elif a.intent=='mute_audio':
            if not re.search(r'silencia|quita el sonido|mudo',clause):raise ValueError('Missing mute request')
        elif a.intent=='unmute_audio':
            if not re.search(r'quita el silencio|desilencia|activa el sonido',clause):raise ValueError('Missing unmute request')
        elif a.intent in ('next_track','previous_track'):
            if not re.search(r'siguiente|pasa' if a.intent=='next_track' else r'anterior|vuelve',clause):raise ValueError('Wrong track direction')
        elif a.intent=='activate_scene':
            if not re.search(r'activa|pon|cambia|modo',clause):raise ValueError('Missing scene request')
        elif a.intent=='play_music':
            if not re.search(r'reproduce|musica|quiero escuchar',clause):raise ValueError('Missing play request')
        elif a.intent=='search_music':
            if not re.match(r'busca(?:r)?\b',clause):raise ValueError('Missing search request')
