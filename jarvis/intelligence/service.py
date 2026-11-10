"""Start only the bundled local service when absent; never pull models at runtime."""
import os
import subprocess
import time
from pathlib import Path
from .ollama_client import OllamaClient
from .settings import IntelligenceConfig
from jarvis.core.config import data_dir


def ensure_service():
    client=OllamaClient(IntelligenceConfig())
    try:client.request('/api/version',timeout=1);return 'existing'
    except Exception:pass
    executable=Path(__file__).resolve().parents[2]/'.tools'/'ollama'/'ollama.exe'
    if not executable.is_file():raise FileNotFoundError('Install local Ollama explicitly first')
    root=data_dir();logs=root/'logs';logs.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy();env.update(OLLAMA_HOST='127.0.0.1:11434',OLLAMA_MODELS=str(root/'intelligence_models'/'ollama'),
        OLLAMA_NUM_PARALLEL='1',OLLAMA_MAX_LOADED_MODELS='1',OLLAMA_KEEP_ALIVE='0',CUDA_VISIBLE_DEVICES='-1')
    with (logs/'ollama.stdout.log').open('ab') as stdout,(logs/'ollama.stderr.log').open('ab') as stderr:
        subprocess.Popen([str(executable),'serve'],env=env,stdout=stdout,stderr=stderr,
                         creationflags=subprocess.CREATE_NO_WINDOW)
    deadline=time.monotonic()+10
    while time.monotonic()<deadline:
        try:client.request('/api/version',timeout=0.5);return 'started'
        except Exception:time.sleep(0.1)
    raise TimeoutError('Local Ollama did not start; inspect service log')
