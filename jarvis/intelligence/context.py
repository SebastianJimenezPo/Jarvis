from dataclasses import dataclass,field,asdict
import time
import copy
from .contracts import ActionProposal
from .catalog import entity_type
from .plan import ActionPlan


@dataclass
class Referent:
    entity_type:str
    entity_id:str
    source:str='explicit_user_reference'
    status:str='proposed_simulated'
    last_mention:float=0


@dataclass
class PendingClarification:
    intent:str
    parameters:dict
    missing_parameter:str
    candidates:list[str]
    session_id:str
    created:float
    expires:float
    attempts:int=0
    prior_actions:list=field(default_factory=list)


class ContextManager:
    def __init__(self,config,clock=time.monotonic):
        self.config,self.clock=config,clock
        self.session_id='';self.updated=clock();self.referents=[];self.proposals=[]
        self.pending=None;self.history=[];self.topic=None;self.preferences={}
        self.revision=0
        self.plan=ActionPlan();self.focus=None

    def fork(self):
        return copy.deepcopy(self)

    def expire(self):
        if self.clock()-self.updated>self.config.context_ttl_seconds:self.clear()
        if self.pending and self.clock()>=self.pending.expires:self.pending=None;self.revision+=1
        self.referents=[r for r in self.referents if self.clock()-r.last_mention<=self.config.context_ttl_seconds]

    def begin_session(self,session_id):
        self.expire();self.session_id=session_id
        if self.pending and self.pending.session_id!=session_id:self.pending=None
        self.revision+=1

    def clear(self):
        self.referents=[];self.proposals=[];self.pending=None;self.history=[];self.topic=None;self.preferences={}
        self.updated=self.clock()
        self.revision+=1
        self.plan=ActionPlan();self.focus=None

    def cancel(self,group=None):
        self.plan.cancel(group)
        self.proposals=[a for a in self.proposals if group is not None and entity_type(a.intent)!=group]
        self.referents=[r for r in self.referents if group is not None and r.entity_type!=group]
        if self.pending and (group is None or entity_type(self.pending.intent)==group):self.pending=None
        if self.focus and (group is None or entity_type(self.focus['intent'])==group):self.focus=None
        self.revision+=1;self.updated=self.clock()

    def remember(self,actions,replace_previous=False,operation=None,source='',evidence=None):
        self.expire();self.updated=self.clock()
        self.revision+=1
        operation=operation or ('modify' if replace_previous else 'replace')
        self.plan.apply(actions,operation,source,evidence or [])
        self.proposals=[item.proposal() for item in self.plan.active()]
        if actions:self.focus={'intent':actions[-1].intent,'target':actions[-1].target}
        self.referents=[r for r in self.referents if any(a.target==r.entity_id for a in self.proposals)]
        # Preserve multiple compatible referents; do not pick the last application arbitrarily.
        for action in actions:
            self.referents=[r for r in self.referents if r.entity_id!=action.target]
            self.referents.append(Referent(entity_type(action.intent),action.target,last_mention=self.clock()))
        self.referents=self.referents[-12:]

    def targets(self,group):
        self.expire()
        return list(dict.fromkeys(r.entity_id for r in self.referents if r.entity_type==group))

    def ask(self,intent,params,missing,candidates):
        now=self.clock();self.updated=now
        self.revision+=1
        self.pending=PendingClarification(intent,params,missing,candidates,self.session_id,now,now+self.config.clarification_ttl_seconds)

    def exchange(self,user,assistant):
        self.updated=self.clock()
        self.revision+=1
        self.history.append({'user':user[:800],'assistant':assistant[:1000]})
        self.history=self.history[-self.config.max_recent_turns:]

    def snapshot(self):
        self.expire()
        return {'session_id':self.session_id,'updated':self.updated,'revision':self.revision,'plan':self.plan.snapshot(),'focus':self.focus,'referents':[asdict(r) for r in self.referents],
                'proposals':[a.model_dump() for a in self.proposals],'pending':asdict(self.pending) if self.pending else None,
                'history':[dict(item) for item in self.history],'topic':self.topic,'preferences':dict(self.preferences)}

    def restore(self,data):
        if not isinstance(data,dict) or self.clock()-data.get('updated',0)>self.config.context_ttl_seconds:return
        self.updated=data['updated'];self.session_id=str(data.get('session_id',''))
        self.revision=int(data.get('revision',0))
        self.referents=[Referent(**r) for r in data.get('referents',[])[:12]]
        self.proposals=[ActionProposal.model_validate(a) for a in data.get('proposals',[])[:8]]
        self.plan=ActionPlan.restore(data['plan']) if data.get('plan') else ActionPlan()
        if not data.get('plan') and self.proposals:self.plan.apply(self.proposals,'replace','legacy_snapshot',[])
        self.focus=data.get('focus')
        self.pending=PendingClarification(**data['pending']) if data.get('pending') else None
        self.history=data.get('history',[])[-self.config.max_recent_turns:]
        self.topic=data.get('topic');self.preferences=data.get('preferences',{})
        self.expire()
