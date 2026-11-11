import re
from jarvis.dialogue.bridge import DialogueReply,Phase2ResponseProvider
from .dialogue_manager import DialogueManager
from .settings import load_intelligence
from .contracts import Kind
from .fast_path import FastPath
from .language import normalize,color,number,mentions
from .catalog import APPLICATIONS,LIGHTS


class IntelligenceResponseProvider:
    def __init__(self,root,cancel=None,config=None):
        self.manager=DialogueManager(root,config,cancel=cancel)
        self.last_trace={};self.recovery_status='not_needed'
    def begin_session(self,session_id,snapshot=None):self.manager.begin_session(session_id,snapshot)
    def respond(self,utterance,diagnostic_echo=False):
        if diagnostic_echo:return Phase2ResponseProvider().respond(utterance,True)
        decision,text=self.manager.interpret(utterance.text,utterance.session_id,utterance.turn_id)
        self.last_trace={'original_transcript':utterance.text,'selected_transcript':utterance.text,'normalized_text':normalize(utterance.text),'response':text}
        self.recovery_status='not_needed'
        return DialogueReply(text,decision.end_session)

    def respond_audio(self,utterance,alternative=None):
        ticket=self.manager.ticket()
        original=utterance.text;context=self.manager.context.fork();fast=FastPath(context)
        preview=fast.interpret(original)
        if preview is None:preview=fast.recover_fragment(original)
        action_topic=self.manager.last_decision and self.manager.last_decision.interpretation.kind==Kind.ACTION_PROPOSAL
        doubtful=(preview is not None and preview.reason_code=='transcript_target_uncertain') or (
            preview is None and (context.pending or (context.proposals and action_topic)) and len(normalize(original).split())<=4
            and not re.match(r'^(?:que|como|por que|dime|explica\w*|dame|hazlo|hola|gracias)\b',normalize(original)))
        if not doubtful:return self.respond(utterance)
        selected=original;status='clarified';accepted=False
        if alternative is not None:
            try:
                candidate=alternative()
                n=normalize(original);alt=normalize(candidate)
                conflict=(color(n) is not None and color(alt) is not None and color(n)!=color(alt)) or (
                    number(n) is not None and number(alt) is not None and number(n)!=number(alt))
                for table in (APPLICATIONS,LIGHTS):
                    before=mentions(n,table);after=mentions(alt,table)
                    if before and after and set(before)!=set(after):conflict=True
                proposed=FastPath(self.manager.context.fork()).interpret(candidate)
                if not conflict and proposed and proposed.kind in (Kind.ACTION_PROPOSAL,Kind.CANCEL,Kind.NEGATED,Kind.DEFERRED_REQUEST):
                    self.manager.validator.validate(proposed,candidate,self.manager.context.fork())
                    selected=candidate;accepted=True;status='alternative_validated'
                elif conflict:status='conflict_clarified'
            except Exception as exc:
                from .ollama_client import RequestCancelled
                if isinstance(exc,RequestCancelled):raise
                status='alternative_unavailable_clarified'
        decision,response=self.manager.interpret(selected,utterance.session_id,utterance.turn_id,
            uncertain=not accepted and preview is None,expected_ticket=ticket)
        self.last_trace={'original_transcript':original,'selected_transcript':selected,'normalized_text':normalize(selected),'response':response}
        self.recovery_status=status
        return DialogueReply(response,decision.end_session)
    def snapshot(self):return self.manager.context.snapshot()
    def diagnostic(self):
        decision=self.manager.last_decision
        if decision is None:return None
        data=decision.model_dump(mode='json')
        if not self.manager.config.log_text:
            interpretation=data['interpretation']
            interpretation.pop('response',None);interpretation.pop('condition',None);interpretation.pop('clarification_question',None)
            for a in interpretation['actions']:
                a.pop('source_clause',None)
                if 'query' in a['parameters']:a['parameters']['query']='[text omitted]'
        data['llm_metrics']=self.manager.last_metrics.copy()
        data['stt_recovery']=self.recovery_status
        if self.manager.config.log_text:data['turn_trace']=dict(self.last_trace)
        data['routes']=self.manager.counts.copy()
        data['last_error']=self.manager.last_error
        if not self.manager.config.log_text and data['last_error']:
            data['last_error']=data['last_error'].split(':',1)[0]+' (details omitted for privacy)'
        return data
    def close(self):self.manager.close()


def make_provider(root,cancel=None):
    try:config=load_intelligence(root)
    except (ValueError,TypeError,OSError):return Phase2ResponseProvider()
    return IntelligenceResponseProvider(root,cancel,config) if config.enabled else Phase2ResponseProvider()
