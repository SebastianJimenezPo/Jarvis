from jarvis.dialogue.bridge import DialogueReply,Phase2ResponseProvider
from .dialogue_manager import DialogueManager
from .settings import load_intelligence


class IntelligenceResponseProvider:
    def __init__(self,root,cancel=None,config=None):
        self.manager=DialogueManager(root,config,cancel=cancel)
    def begin_session(self,session_id,snapshot=None):self.manager.begin_session(session_id,snapshot)
    def respond(self,utterance,diagnostic_echo=False):
        if diagnostic_echo:return Phase2ResponseProvider().respond(utterance,True)
        decision,text=self.manager.interpret(utterance.text,utterance.session_id,utterance.turn_id)
        return DialogueReply(text,decision.end_session)
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
        data['llm_metrics']=self.manager.client.last_metrics.copy()
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
