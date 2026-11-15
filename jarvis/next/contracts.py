"""Provider-neutral data. A decision is never an execution permission."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, StrictStr, model_validator


class Record(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)


Parameters = dict[str, StrictInt | StrictStr | StrictBool]
Operation = Literal[
    'create_plan', 'append_plan', 'modify_plan', 'replace_plan', 'remove_actions',
    'cancel_subset', 'cancel_all', 'hold', 'answer_clarification', 'query_state',
    'clarify', 'preference', 'deferred', 'unsupported', 'conversation', 'negated', 'hypothetical',
]
PolicyReason = Literal['revision', 'plan_identity', 'reference', 'evidence', 'catalog',
                       'direct_mismatch', 'scope', 'temporal', 'missing_plan', 'conflict', 'capacity',
                       'quoted_command', 'deferred_time']


class Span(Record):
    start: StrictInt = Field(ge=0)
    end: StrictInt = Field(gt=0)

    @model_validator(mode='after')
    def ordered(self):
        if self.end <= self.start:
            raise ValueError('Invalid evidence range')
        return self


class ToolCall(Record):
    tool: StrictStr = Field(min_length=1, max_length=80)
    target: StrictStr = Field(min_length=1, max_length=60)
    parameters: Parameters = Field(default_factory=dict, max_length=8)
    evidence: Span
    depends_on: tuple[StrictStr, ...] = Field(default=(), max_length=8)


class ActionChange(Record):
    action_id: StrictStr = Field(min_length=1, max_length=64)
    target: StrictStr | None = Field(default=None, min_length=1, max_length=60)
    parameters: Parameters = Field(default_factory=dict, max_length=8)

    @model_validator(mode='after')
    def nonempty(self):
        if not self.parameters and self.target is None:
            raise ValueError('Empty change')
        return self


class Decision(Record):
    schema_version: Literal[1] = 1
    operation: Operation
    expected_revision: StrictInt = Field(default=0, ge=0)
    plan_id: StrictStr | None = Field(default=None, max_length=64)
    temporal: Literal['now', 'future', 'conditional', 'unspecified'] = 'unspecified'
    evidence: Span | None = None
    actions: tuple[ToolCall, ...] = Field(default=(), max_length=8)
    changes: tuple[ActionChange, ...] = Field(default=(), max_length=8)
    action_ids: tuple[StrictStr, ...] = Field(default=(), max_length=8)

    @model_validator(mode='after')
    def shape(self):
        additions = self.operation in ('create_plan', 'append_plan', 'replace_plan', 'query_state')
        if self.operation != 'modify_plan' and bool(self.actions) != additions:
            raise ValueError('Actions do not match operation')
        if self.actions and self.temporal != 'now':
            raise ValueError('Future decisions cannot carry immediate tool calls')
        if bool(self.changes) != (self.operation == 'modify_plan'):
            raise ValueError('Changes do not match operation')
        if bool(self.action_ids) != (self.operation in ('remove_actions', 'cancel_subset')):
            raise ValueError('Action references do not match operation')
        if (self.changes or self.action_ids or self.operation in ('append_plan', 'answer_clarification')) and not self.plan_id:
            raise ValueError('Existing-plan operation requires plan identity')
        if self.operation == 'deferred' and self.temporal not in ('future', 'conditional'):
            raise ValueError('Deferred operation requires temporal scope')
        return self


class PlanItem(Record):
    action_id: StrictStr
    call: ToolCall


class ContextView(Record):
    plan_id: StrictStr | None = None
    revision: StrictInt = 0
    status: Literal['empty', 'simulated', 'withheld', 'cancelled'] = 'empty'
    items: tuple[PlanItem, ...] = Field(default=(), max_length=8)


class Capability(Record):
    tool: StrictStr
    description: StrictStr
    targets: tuple[StrictStr, ...]
    resource: Literal['application', 'audio', 'media']
    access: Literal['read', 'write']
    risk: Literal['low', 'moderate']
    availability: Literal['simulation_only'] = 'simulation_only'
    parameter_schema: dict
    can_verify: Literal[False] = False
    can_revert: Literal[False] = False


class InterpretationRequest(Record):
    request_id: StrictStr
    session_id: StrictStr
    turn_id: StrictStr
    text: StrictStr = Field(min_length=1, max_length=1600)
    context: ContextView
    capabilities: tuple[Capability, ...]


class Usage(Record):
    input_tokens: StrictInt | None = Field(default=None, ge=0)
    output_tokens: StrictInt | None = Field(default=None, ge=0)


class ProviderReply(Record):
    decision_json: StrictStr = Field(min_length=2, max_length=16384)
    usage: Usage = Field(default_factory=Usage)


class ToolResult(Record):
    tool: StrictStr
    target: StrictStr
    status: Literal['simulated', 'unknown']
    executed: Literal[False] = False
    verified: Literal[False] = False


class PlanReview(Record):
    review_id: StrictStr
    operation: Operation
    source_text: StrictStr = Field(min_length=1, max_length=1600)
    base_revision: StrictInt
    proposed_plan: ContextView
    expires_in_seconds: float = Field(gt=0)


class Outcome(Record):
    request_id: StrictStr
    session_id: StrictStr
    turn_id: StrictStr
    generation: StrictInt = Field(ge=0)
    route: Literal['direct', 'provider', 'offline']
    disposition: Literal['simulated', 'cancelled', 'held', 'withheld', 'rejected', 'unavailable', 'stale']
    decision: Decision | None = None
    plan: ContextView
    results: tuple[ToolResult, ...] = ()
    message: StrictStr
    error: StrictStr | None = None
    proposed_operation: Operation | None = None
    policy_reason: PolicyReason | None = None
    seconds: float = Field(ge=0)
    usage: Usage = Field(default_factory=Usage)
    review: PlanReview | None = None
    executed: Literal[False] = False
