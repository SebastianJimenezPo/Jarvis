"""Next voice boundary. Only text leaves the worker, after explicit remote opt-in."""
from .bridge import DialogueReply
from jarvis.next.conversation import NextConversation,normalized
from jarvis.next.engine import NextEngine


class NextVoiceBridge:
    def __init__(self,config,cancel,conversation=None):
        self.cancel_event=cancel
        self.log_details=config.log_transcripts
        if conversation is None:
            provider=None
            if config.next_remote:
                from jarvis.next.groq import GroqProvider
                provider=GroqProvider(enabled=True,free_tier_confirmed=True,
                    model='openai/gpt-oss-120b',reasoning_effort=config.next_reasoning)
            conversation=NextConversation(NextEngine(provider,timeout=config.next_timeout_seconds,
                review_enabled=True,cancelled=cancel.is_set))
        self.conversation=conversation
        self._reply=self._outcome=None

    def begin_session(self,session_id,snapshot=None):
        self.conversation.begin_session(str(session_id))
        self._reply=self._outcome=None

    def respond(self,utterance,diagnostic_echo=False):
        if utterance.session_id!=self.conversation.session_id or self.cancel_event.is_set():
            return DialogueReply('')
        result=(self.conversation._local('Escuché: '+utterance.text,utterance.turn_id) if diagnostic_echo
                else self.conversation.interpret(utterance.text,utterance.turn_id))
        self._outcome=result
        text=result.message if self.conversation.can_publish(result) else ''
        self._reply=DialogueReply(text,normalized(utterance.text) in ('adios','hasta luego'))
        return self._reply

    def can_publish(self,reply):
        return (reply is self._reply and self._outcome is not None and not self.cancel_event.is_set()
                and self.conversation.can_publish(self._outcome))

    def cancel(self):
        self.conversation.cancel()
        self._reply=self._outcome=None

    def end_session(self):
        self.cancel()

    def diagnostic(self):
        r=self._outcome
        if r is None:return {}
        data=dict(profile='next',route=r.route,operation=r.proposed_operation or (r.decision.operation if r.decision else None),
            disposition=r.disposition,error=r.error,provider_error_stage=r.provider_error_stage,
            interpretation_seconds=r.timings.interpretation_seconds,
            validation_context_seconds=r.timings.validation_context_seconds,
            pending_question=self.conversation.pending is not None,review_pending=bool(r.review),executed=False)
        if self.log_details:
            data['plan']=[dict(action_id=item.action_id,tool=item.call.tool,target=item.call.target,parameters=item.call.parameters) for item in r.plan.items]
            data['plan_status']=r.plan.status
            data['proposed_plan']=[dict(tool=item.call.tool,target=item.call.target,parameters=item.call.parameters) for item in r.review.proposed_plan.items] if r.review else None
        return data

    def close(self):
        self._reply=self._outcome=None
        self.conversation.close()
