"""Transient operational dialogue. Short answers only acquire meaning locally.

No evaluator oracle, persistent memory, physical tools, or general language parser.
"""
from dataclasses import dataclass
import re
import unicodedata
import uuid
from .engine import NextEngine
from .responses import response


def normalized(text):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFD',text.casefold())
                           if not unicodedata.combining(c)).split()).rstrip('.!?¿¡ ')


@dataclass(frozen=True)
class PendingQuestion:
    question_id: str
    intent: str
    parameter: str
    candidates: tuple[str,...]
    session_id: str
    revision: int
    expires: float


@dataclass(frozen=True)
class Reference:
    target: str
    session_id: str
    expires: float


class NextConversation:
    def __init__(self,engine=None):
        self.engine=engine or NextEngine(review_enabled=True)
        self.session_id='cli';self.pending=None;self.reference=None;self._review=None
        self._turn=0;self._epoch=0;self._last=None;self._question_generation=None

    def begin_session(self,session_id):
        self._epoch+=1;self.session_id=session_id
        self.pending=self.reference=self._review=self._last=None
        self.engine.begin_session(session_id)

    def _local(self,message,turn):
        result=self.engine.local_reply(message,self.session_id,turn)
        self._last=result
        return result

    def _question(self,intent,parameter,candidates,turn):
        result=self._local('¿Cuál aplicación quieres: Spotify, Steam, Chrome o Discord?' if parameter=='target'
                           else '¿A qué porcentaje quieres ajustar el volumen, entre 0 y 100?',turn)
        self.pending=PendingQuestion(uuid.uuid4().hex,intent,parameter,candidates,self.session_id,
            result.plan.revision,self.engine.manager.clock()+45)
        self._question_generation=result.generation
        return result

    def _live_question(self):
        p=self.pending
        if p and (p.session_id!=self.session_id or self.engine.manager.clock()>=p.expires
                  or p.revision!=self.engine.manager.snapshot().revision): self.pending=None
        return self.pending

    def interpret(self,text,turn_id=None):
        if not isinstance(text,str) or not text.strip() or len(text)>1600: raise ValueError('Expected text')
        self._turn+=1;turn=turn_id or str(self._turn);epoch=self._epoch
        key=normalized(text);question=self._live_question()
        if self.reference and (self.reference.session_id!=self.session_id or self.engine.manager.clock()>=self.reference.expires): self.reference=None
        if key in ('cancela','cancelar','olvida todo lo anterior'):
            return self.cancel(turn)
        if key in ('si','confirmo','confirmo la simulacion','confirmo la revision'):
            if self._review:
                review,self._review=self._review,None
                result=self.engine.confirm(review,self.session_id,turn)
                return self._finish(result,epoch)
            return self._local('No hay una propuesta vigente que pueda confirmar.',turn)
        if key == 'no' and self._review:
            self._review=None
            return self._local('Descarté el borrador; conservé el plan anterior.',turn)
        self._review=None  # Every ordinary new turn supersedes a confirmation.
        if key in ('abre una aplicacion','abre alguna aplicacion','quiero abrir una aplicacion'):
            return self._question('applications.open','target',('spotify','steam','chrome','discord'),turn)
        if key in ('ajusta el volumen','cambia el volumen'):
            return self._question('system_audio.set_volume','value',(),turn)
        effective=text
        if question:
            target=None
            if question.parameter=='target':
                if key in question.candidates: target=key
                ordinal={'el primero':0,'la primera':0,'el segundo':1,'la segunda':1,'el tercero':2,'la tercera':2,'el cuarto':3}
                if key in ordinal and ordinal[key]<len(question.candidates): target=question.candidates[ordinal[key]]
                if key in ('ese','esa'):
                    if len(question.candidates)==1: target=question.candidates[0]
                    elif self.reference and self.reference.target in question.candidates: target=self.reference.target
                if target: effective='Abre '+target
            else:
                if re.fullmatch(r'(?:100|[1-9]?\d)\s*%?',key): effective='Volumen al '+key.rstrip('% ').strip()+'%';target=effective
            if target: self.pending=None
            elif len(key.split())<=3:
                # Keep the same candidates/expiry; invalid short replies never guess.
                return self._local('Necesito un nombre de la lista.' if question.parameter=='target' else 'Necesito un número entre 0 y 100.',turn)
            else: self.pending=None
        elif key in ('spotify','steam','chrome','discord','ese','esa','el segundo'):
            return self._local('No hay una pregunta vigente para interpretar esa respuesta. Dime qué quieres hacer.',turn)
        if key.startswith('abre ese') and key in ('abre ese','abre esa') and self.reference:
            effective='Abre '+self.reference.target
        if key in ('autoriza la simulacion','simula el plan') and self.engine.manager.snapshot().status!='withheld':
            return self._local('No hay un plan retenido para autorizar.',turn)
        courtesies={'hola':'Hola. Estoy disponible en simulación.','gracias':'Con gusto.','adios':'Hasta luego.',
                    'hasta luego':'Hasta luego.','me escuchas':'Sí, te escucho.','me escuchas bien':'Sí, te escucho.'}
        if key in courtesies: return self._local(courtesies[key],turn)
        result=self.engine.interpret(effective,self.session_id,turn)
        return self._finish(result,epoch)

    def _finish(self,result,epoch):
        if epoch!=self._epoch: return result.model_copy(update={'message':''})
        if result.review: self._review=result.review.review_id
        decision=result.decision
        if decision and not result.error:
            targets=[c.target for c in decision.actions if c.tool=='applications.open']
            targets += [c.target for c in decision.changes if c.target]
            if len(set(targets))==1: self.reference=Reference(targets[0],self.session_id,self.engine.manager.clock()+120)
        result=result.model_copy(update={'message':response(result)})
        self._last=result
        return result

    def cancel(self,turn_id='cancel'):
        self._epoch+=1;self.pending=self.reference=self._review=None
        return self._finish(self.engine.cancel(self.session_id,turn_id),self._epoch)

    def confirm(self,review_id,turn_id='local-review'):
        self._review=None;self.pending=None
        return self._finish(self.engine.confirm(review_id,self.session_id,turn_id),self._epoch)

    def can_publish(self,result):
        if result is not self._last or self.engine.cancelled(): return False
        if result.generation==self._question_generation and not self._live_question(): return False
        return self.engine.manager.can_publish(result)

    def close(self):
        self._epoch+=1;self.pending=self.reference=self._review=self._last=None
        self.engine.close()
