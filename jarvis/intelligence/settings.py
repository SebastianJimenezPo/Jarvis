import json
from dataclasses import dataclass,asdict
from urllib.parse import urlparse


@dataclass(frozen=True)
class IntelligenceConfig:
    version:int=1
    enabled:bool=False
    semantic_enabled:bool=True
    semantic_model:str='e5-small'
    llm_enabled:bool=True
    ollama_url:str='http://127.0.0.1:11434'
    model:str='qwen3:1.7b'
    fallback_model:str='qwen3.5:2b'
    timeout_seconds:float=12.0
    keep_alive_seconds:int=90
    context_tokens:int=2048
    max_output_tokens:int=320
    cpu_threads:int=4
    gpu_layers:int=0
    temperature:float=0.1
    conversation_temperature:float=0.1
    conversation_max_output_tokens:int=320
    max_recent_turns:int=6
    context_ttl_seconds:float=120.0
    clarification_ttl_seconds:float=60.0
    max_clarification_attempts:int=3
    log_text:bool=False

    def validate(self):
        for key,value in asdict(self).items():
            expected=type(getattr(IntelligenceConfig(),key))
            if (expected is float and type(value) not in (int,float)) or (expected is not float and type(value) is not expected):
                raise ValueError(f'intelligence.{key}: wrong type')
        if self.version!=1 or self.semantic_model not in ('minilm','e5-small'):
            raise ValueError('Invalid intelligence version/model')
        if self.model not in ('qwen3.5:2b','qwen3:1.7b') or self.fallback_model not in ('qwen3.5:2b','qwen3:1.7b'):
            raise ValueError('Unapproved local model')
        url=urlparse(self.ollama_url)
        if url.scheme!='http' or url.hostname not in ('127.0.0.1','localhost','::1') or url.username or url.path not in ('','/'):
            raise ValueError('Ollama must be a loopback HTTP service')
        for field,low,high in [('timeout_seconds',0.1,120),('keep_alive_seconds',0,300),('context_tokens',512,4096),
            ('max_output_tokens',64,1024),('cpu_threads',1,8),('gpu_layers',0,99),('temperature',0,1),
            ('conversation_temperature',0,1),('conversation_max_output_tokens',32,1024),
            ('max_recent_turns',1,12),('context_ttl_seconds',1,600),('clarification_ttl_seconds',1,180),('max_clarification_attempts',1,5)]:
            if not low<=getattr(self,field)<=high:raise ValueError('Out of range: '+field)
        return self


def load_intelligence(root):
    path=root/'intelligence.json'
    return IntelligenceConfig(**json.loads(path.read_text(encoding='utf-8'))).validate() if path.exists() else IntelligenceConfig()


def save_intelligence(root,config):
    config.validate();root.mkdir(parents=True,exist_ok=True)
    temp=root/'intelligence.tmp';temp.write_text(json.dumps(asdict(config),indent=2),encoding='utf-8');temp.replace(root/'intelligence.json')
