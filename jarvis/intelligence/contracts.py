from enum import Enum
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,model_validator


class Kind(str,Enum):
    ACTION_PROPOSAL='action_proposal'
    CONVERSATION='conversation'
    CLARIFICATION='clarification'
    CANCEL='cancel'
    PREFERENCE='preference'
    DEFERRED_REQUEST='deferred_request'
    HYPOTHETICAL='hypothetical'
    UNSUPPORTED='unsupported'
    NEGATED='negated'


Intent=Literal['open_application','close_application','focus_application','set_volume','increase_volume',
    'decrease_volume','mute_audio','unmute_audio','play_music','pause_music','next_track','previous_track',
    'search_music','turn_on_light','turn_off_light','set_light_color','set_light_brightness','activate_scene','get_system_status']


class ActionProposal(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    intent: Intent
    target: str=Field(min_length=1,max_length=60)
    parameters: dict[str,str|int]=Field(default_factory=dict,max_length=4)
    source_clause: str=Field(default='',max_length=1000)


class Interpretation(BaseModel):
    model_config=ConfigDict(extra='forbid')
    kind: Kind
    actions: list[ActionProposal]=Field(default_factory=list,max_length=8)
    immediate: bool=False
    negated: bool=False
    condition: str|None=Field(default=None,max_length=500)
    clarification_question: str|None=Field(default=None,max_length=250)
    reason_code: str=Field(default='',max_length=80)
    response: str=Field(default='',max_length=1200)

    @model_validator(mode='after')
    def invariant(self):
        if self.kind==Kind.ACTION_PROPOSAL:
            if not self.actions or not self.immediate or self.negated or self.condition:
                raise ValueError('An action proposal must be explicit, immediate and non-negated')
        elif self.actions:
            raise ValueError('Only action_proposal may contain authorized simulated actions')
        return self


class Decision(BaseModel):
    interpretation: Interpretation
    route: Literal['fast','semantic','llm','fallback']
    seconds: float
    session_id: str
    turn_id: str
    request_id: str
    simulated: Literal[True]=True
    executed: Literal[False]=False
    end_session: bool=False


class ModelInterpretation(BaseModel):
    """Compact LLM wire format. Authorization flags are derived then independently checked."""
    model_config=ConfigDict(extra='forbid')
    kind: Kind
    actions:list[ActionProposal]=Field(default_factory=list,max_length=8)
    question:str=Field(default='',max_length=250)
    answer:str=Field(default='',max_length=600)

    def validated_interpretation(self):
        return Interpretation(kind=self.kind,actions=self.actions,immediate=self.kind==Kind.ACTION_PROPOSAL,
                              negated=self.kind==Kind.NEGATED,clarification_question=self.question or None,
                              response=self.answer,reason_code='local_model_interpretation')
