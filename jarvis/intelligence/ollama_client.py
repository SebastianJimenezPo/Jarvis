import http.client
import json
import queue
import socket
import threading
import time
from urllib.parse import urlparse


class OllamaError(RuntimeError):pass
class RequestCancelled(OllamaError):pass


class OllamaClient:
    def __init__(self,config):
        config.validate();self.config=config;self.last_metrics={};self.used_models=set()

    def request(self,path,payload=None,cancel=None,timeout=None):
        url=urlparse(self.config.ollama_url)
        conn=http.client.HTTPConnection(url.hostname,url.port or 11434,timeout=timeout or self.config.timeout_seconds)
        result=queue.Queue(maxsize=1)
        def work():
            try:
                body=json.dumps(payload).encode() if payload is not None else None
                conn.request('POST' if payload is not None else 'GET',path,body,{'Content-Type':'application/json'})
                response=conn.getresponse();data=response.read(1_000_001)
                if len(data)>1_000_000:raise OllamaError('Response exceeds limit')
                parsed=json.loads(data)
                if response.status!=200:raise OllamaError(str(parsed.get('error','Ollama failed')))
                result.put_nowait(parsed)
            except Exception as exc:result.put_nowait(exc)
            finally:conn.close()
        thread=threading.Thread(target=work,name='ollama-request',daemon=True);thread.start()
        deadline=time.monotonic()+(timeout or self.config.timeout_seconds)
        try:
            while True:
                if cancel is not None and cancel.is_set():raise RequestCancelled('Inference cancelled')
                if time.monotonic()>=deadline:raise TimeoutError('Ollama request timed out')
                try:value=result.get(timeout=0.025)
                except queue.Empty:continue
                if isinstance(value,Exception):raise OllamaError(str(value)) from value
                return value
        finally:
            if conn.sock:
                try:conn.sock.shutdown(socket.SHUT_RDWR)
                except OSError:pass
            conn.close()

    def installed(self):return self.request('/api/tags',timeout=2).get('models',[])
    def running(self):return self.request('/api/ps',timeout=2).get('models',[])
    def show(self,model):return self.request('/api/show',{'model':model},timeout=3)

    def chat(self,messages,schema=None,cancel=None,model=None):
        names={m.get('name') for m in self.installed()}
        chosen=model or self.config.model
        if chosen not in names:
            if self.config.fallback_model in names:chosen=self.config.fallback_model
            else:raise OllamaError('Requested local model is not installed; no automatic downloads')
        capabilities=self.show(chosen).get('capabilities',[])
        payload={'model':chosen,'messages':messages,'stream':False,'keep_alive':f'{self.config.keep_alive_seconds}s',
            'options':{'temperature':self.config.temperature if schema else self.config.conversation_temperature,'num_ctx':self.config.context_tokens,
                       'num_predict':self.config.max_output_tokens if schema else self.config.conversation_max_output_tokens,'num_thread':self.config.cpu_threads,
                       'num_gpu':self.config.gpu_layers,'seed':17}}
        if 'thinking' in capabilities:payload['think']=False
        if schema:payload['format']=schema
        start=time.monotonic();self.used_models.add(chosen)
        result=self.request('/api/chat',payload,cancel)
        self.last_metrics={key:result.get(key) for key in ('load_duration','prompt_eval_duration','eval_duration','prompt_eval_count','eval_count')}
        self.last_metrics.update(model=chosen,wall_seconds=time.monotonic()-start,thinking_disabled='think' in payload)
        if result.get('done_reason')=='length':raise OllamaError('Model output reached token limit')
        return result['message']['content']

    def unload(self):
        for model in list(self.used_models):
            try:self.request('/api/generate',{'model':model,'keep_alive':0},timeout=3)
            except (OllamaError,TimeoutError):pass
        self.used_models.clear()
