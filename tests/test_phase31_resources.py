from dataclasses import replace
import pytest
from jarvis.intelligence.ollama_client import OllamaClient,OllamaError
from jarvis.intelligence.settings import IntelligenceConfig


class LocalClient(OllamaClient):
    def __init__(self):
        super().__init__(IntelligenceConfig());self.calls=[];self.unknown=False;self.digest='one'
    def request(self,path,payload=None,*args,**kwargs):
        self.calls.append(path)
        if path=='/api/tags':return {'models':[{'name':name,'digest':self.digest} for name in ('qwen3:1.7b','qwen3.5:2b')]}
        if path=='/api/show':return {'capabilities':['thinking']}
        if path=='/api/chat':
            if self.unknown:raise OllamaError('model not found')
            return {'message':{'content':'Hola'},'eval_count':1,'eval_duration':1}
        return {}


def test_metadata_is_cached_but_not_model_output():
    client=LocalClient();client.chat([]);client.chat([])
    assert client.calls.count('/api/tags')==1 and client.calls.count('/api/show')==1
    assert client.calls.count('/api/chat')==2


@pytest.mark.parametrize('field,value',[('model','qwen3.5:2b'),('ollama_url','http://localhost:11435')])
def test_metadata_cache_is_invalidated_by_model_or_server(field,value):
    client=LocalClient();client.chat([]);client.config=replace(client.config,**{field:value});client.chat([])
    assert client.calls.count('/api/tags')==2 and client.calls.count('/api/show')==2


def test_explicit_installation_refresh_invalidates_capabilities():
    client=LocalClient();client.chat([]);client.digest='two';client.installed();client.chat([])
    assert client.calls.count('/api/show')==2


def test_unknown_model_error_invalidates_without_retry_loop():
    client=LocalClient();client.chat([]);client.unknown=True
    with pytest.raises(OllamaError):client.chat([])
    client.unknown=False;client.chat([])
    assert client.calls.count('/api/tags')==2


def test_semantic_unload_can_be_followed_by_a_fresh_load(tmp_path):
    from jarvis.intelligence.semantic import SemanticRouter
    router=SemanticRouter(tmp_path,IntelligenceConfig());released=[]
    class Provider:
        def unload(self):released.append(True)
    router.provider=Provider();router.unload()
    assert released==[True] and router.provider is None


def test_metadata_cache_expires(monkeypatch):
    from jarvis.intelligence import ollama_client
    now=[0.0];monkeypatch.setattr(ollama_client.time,'monotonic',lambda:now[0])
    client=LocalClient();client.chat([]);now[0]=16;client.chat([])
    assert client.calls.count('/api/tags')==2


def test_semantic_load_failure_does_not_leave_broken_provider(tmp_path):
    from jarvis.intelligence.semantic import SemanticRouter
    router=SemanticRouter(tmp_path,IntelligenceConfig())
    with pytest.raises(FileNotFoundError):router.load()
    assert router.provider is None


def test_manual_profiles_preserve_device_vad_privacy_and_enable_flags(tmp_path):
    from scripts.set_performance_profile import apply_profile
    from jarvis.core.config import Config,save
    from jarvis.speech.settings import VoiceConfig,load_voice,save_voice
    from jarvis.intelligence.settings import save_intelligence,load_intelligence
    save(tmp_path,replace(Config(),threshold=.55,device='auto'))
    before=(tmp_path/'config.json').read_bytes()
    save_voice(tmp_path,replace(VoiceConfig(),enabled=True,end_silence_ms=1200,log_transcripts=False))
    save_intelligence(tmp_path,replace(IntelligenceConfig(),enabled=True,log_text=False))
    apply_profile(tmp_path,'balanced')
    assert load_intelligence(tmp_path).cpu_threads==3
    assert load_voice(tmp_path).cpu_threads==2 and load_voice(tmp_path).end_silence_ms==1200
    assert load_voice(tmp_path).enabled and not load_voice(tmp_path).log_transcripts
    assert load_intelligence(tmp_path).enabled and not load_intelligence(tmp_path).log_text
    assert (tmp_path/'config.json').read_bytes()==before
