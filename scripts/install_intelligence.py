"""Explicit installation of local embeddings and Ollama models. Not called during speech."""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from jarvis.core.config import data_dir

SEMANTIC_MODELS={
    'minilm':('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2','e8f8c211226b894fcb81acc59f3b34ba3efd5f42','onnx/model_quint8_avx2.onnx'),
    'e5-small':('intfloat/multilingual-e5-small','614241f622f53c4eeff9890bdc4f31cfecc418b3','onnx/model.onnx')}
OLLAMA_VERSION='0.40.16'
OLLAMA_SHA256='50fcf5ad54277f2fa5d173ebfc93bcb017adbc0c9ef2314daabc96ca9e6aa64e'


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('components',nargs='+',choices=[*SEMANTIC_MODELS,'ollama','qwen3.5:2b','qwen3:1.7b'])
    args=p.parse_args();root=data_dir()/'intelligence_models';root.mkdir(parents=True,exist_ok=True)
    for name in args.components:
        if name in SEMANTIC_MODELS:
            from huggingface_hub import snapshot_download
            repo,revision,onnx=SEMANTIC_MODELS[name];folder=root/name
            snapshot_download(repo,revision=revision,local_dir=folder,allow_patterns=[onnx,'tokenizer.json','tokenizer_config.json','config.json','LICENSE','README.md'])
            hashes={}
            for file in folder.rglob('*'):
                if file.is_file() and '.cache' not in file.parts:
                    with file.open('rb') as stream:hashes[file.relative_to(folder).as_posix()]=hashlib.file_digest(stream,'sha256').hexdigest()
            path=root/'registry.json';entries=json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
            entries[name]={'repo':repo,'revision':revision,'onnx':onnx,'sha256':hashes}
            path.write_text(json.dumps(entries,indent=2),encoding='utf-8')
        elif name=='ollama':
            tools=Path(__file__).resolve().parents[1]/'.tools';tools.mkdir(exist_ok=True)
            archive=tools/'ollama-windows-amd64.zip'
            if not archive.exists():urllib.request.urlretrieve(f'https://github.com/ollama/ollama/releases/download/v{OLLAMA_VERSION}/ollama-windows-amd64.zip',archive)
            with archive.open('rb') as stream:
                if hashlib.file_digest(stream,'sha256').hexdigest()!=OLLAMA_SHA256:raise ValueError('Ollama integrity mismatch')
            folder=tools/'ollama';folder.mkdir(exist_ok=True)
            with zipfile.ZipFile(archive) as z:
                for entry in z.infolist():
                    if not (folder/entry.filename).resolve().is_relative_to(folder.resolve()):raise ValueError('Unsafe archive path')
                z.extractall(folder)
        else:
            from jarvis.intelligence.service import ensure_service
            ensure_service()
            executable=Path(__file__).resolve().parents[1]/'.tools'/'ollama'/'ollama.exe'
            subprocess.run([str(executable),'pull',name],check=True)
        print(name,'installed',flush=True)


if __name__=='__main__':main()
