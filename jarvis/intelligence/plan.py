"""Bounded simulated plan revisions. No physical execution states or adapters."""
from dataclasses import dataclass,field,asdict
import uuid
from .contracts import ActionProposal
from .catalog import validate_action,entity_type


@dataclass
class PlanItem:
    action_id:str
    intent:str
    target:str|None
    parameters:dict
    status:str
    source:str
    revision:int
    depends_on:list[str]=field(default_factory=list)
    evidence:dict=field(default_factory=dict)
    clause:str=''

    def proposal(self):
        return ActionProposal(intent=self.intent,target=self.target,parameters=self.parameters,source_clause=self.clause)


@dataclass
class ActionPlan:
    plan_id:str=field(default_factory=lambda:uuid.uuid4().hex)
    revision:int=0
    items:list[PlanItem]=field(default_factory=list)

    def active(self):return [item for item in self.items if item.status=='validated']

    def apply(self,actions,operation,source,evidence):
        if operation not in ('replace','append','modify'):raise ValueError('Unknown plan operation')
        self.revision+=1
        for item in self.items:
            if item.status in ('proposed','pending_clarification'):item.status='replaced'
        if operation=='replace':
            for item in self.items:
                if item.status in ('validated','proposed','pending_clarification'):item.status='replaced'
        for index,action in enumerate(actions):
            validate_action(action)
            for item in self.active():
                same=item.intent==action.intent and item.target==action.target and not (operation=='append' and action.intent in ('increase_volume','decrease_volume'))
                replacement_app=(operation=='modify' and entity_type(item.intent)=='application' and item.intent==action.intent)
                opposed=(item.target==action.target and {item.intent,action.intent} in (
                    {'turn_on_light','turn_off_light'},{'open_application','close_application'},
                    {'mute_audio','unmute_audio'},{'play_music','pause_music'}))
                if same or replacement_app or opposed:item.status='replaced'
            self.items.append(PlanItem(uuid.uuid4().hex,action.intent,action.target,dict(action.parameters),'validated',source,self.revision,
                                       evidence=evidence[index] if index<len(evidence) else {},clause=action.source_clause))
        if len(self.active())>8:raise ValueError('Plan exceeds eight active proposals')
        self.items=self.items[-32:]

    def hold(self,pending,source):
        self.revision+=1
        for item in self.items:
            if item.status in ('proposed','pending_clarification'):item.status='replaced'
        pending_id=uuid.uuid4().hex
        for action in pending.prior_actions:
            a=ActionProposal.model_validate(action);validate_action(a)
            self.items.append(PlanItem(uuid.uuid4().hex,a.intent,a.target,a.parameters,'proposed',source,self.revision,depends_on=[pending_id],clause=a.source_clause))
        self.items.append(PlanItem(pending_id,pending.intent,None,dict(pending.parameters),'pending_clarification',source,self.revision))
        self.items=self.items[-32:]

    def cancel(self,group=None):
        self.revision+=1
        for item in self.items:
            if item.status in ('validated','proposed','pending_clarification') and (group is None or entity_type(item.intent)==group):
                item.status='cancelled'

    def snapshot(self):return asdict(self)

    @classmethod
    def restore(cls,data):
        plan=cls(plan_id=str(data['plan_id']),revision=int(data['revision']))
        for row in data.get('items',[])[-32:]:
            item=PlanItem(**row)
            if item.status not in ('proposed','pending_clarification','validated','replaced','cancelled'):raise ValueError('Invalid simulated plan state')
            if item.target is not None:validate_action(item.proposal())
            plan.items.append(item)
        if len(plan.active())>8:raise ValueError('Oversized plan')
        return plan
