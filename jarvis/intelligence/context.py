from dataclasses import dataclass,field,asdict
import time
from .contracts import ActionProposal
from .catalog import entity_type


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

    def expire(self):
        if self.clock()-self.updated>self.config.context_ttl_seconds:self.clear()
        if self.pending and self.clock()>=self.pending.expires:self.pending=None
        self.referents=[r for r in self.referents if self.clock()-r.last_mention<=self.config.context_ttl_seconds]

    def begin_session(self,session_id):
        self.expire();self.session_id=session_id
        if self.pending and self.pending.session_id!=session_id:self.pending=None

    def clear(self):
        self.referents=[];self.proposals=[];self.pending=None;self.history=[];self.topic=None;self.preferences={}
        self.updated=self.clock()

    def remember(self,actions,replace_previous=False):
        self.expire();self.updated=self.clock()
        if replace_previous:
            previous=list(self.proposals)
            for action in actions:
                matches=[a for a in previous if a.intent==action.intent and
                         (a.target==action.target or entity_type(a.intent)=='application')]
                if len(matches)==1:previous.remove(matches[0])
                previous.append(action)
            self.proposals=previous[-8:]
        else:self.proposals=list(actions)
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
        self.pending=PendingClarification(intent,params,missing,candidates,self.session_id,now,now+self.config.clarification_ttl_seconds)

    def exchange(self,user,assistant):
        self.updated=self.clock()
        self.history.append({'user':user[:800],'assistant':assistant[:1000]})
        self.history=self.history[-self.config.max_recent_turns:]

    def snapshot(self):
        self.expire()
        return {'session_id':self.session_id,'updated':self.updated,'referents':[asdict(r) for r in self.referents],
                'proposals':[a.model_dump() for a in self.proposals],'pending':asdict(self.pending) if self.pending else None,
                'history':[dict(item) for item in self.history],'topic':self.topic,'preferences':dict(self.preferences)}

    def restore(self,data):
        if not isinstance(data,dict) or self.clock()-data.get('updated',0)>self.config.context_ttl_seconds:return
        self.updated=data['updated'];self.session_id=str(data.get('session_id',''))
        self.referents=[Referent(**r) for r in data.get('referents',[])[:12]]
        self.proposals=[ActionProposal.model_validate(a) for a in data.get('proposals',[])[:8]]
        self.pending=PendingClarification(**data['pending']) if data.get('pending') else None
        self.history=data.get('history',[])[-self.config.max_recent_turns:]
        self.topic=data.get('topic');self.preferences=data.get('preferences',{})
        self.expire()
