"""Explicit installation only. Runtime reads local registry and never downloads."""
import hashlib
import json
import shutil
import urllib.request
from pathlib import Path


def digest(path):
    with open(path,"rb") as stream:
        return hashlib.file_digest(stream,"sha256").hexdigest()


def registry(root):
    path=root/"models"/"registry.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def resolve(root, name, verify=False):
    item=registry(root).get(name)
    if not item:
        raise FileNotFoundError(f"Modelo no instalado: {name}. Ejecuta scripts/install_voice_models.py explícitamente.")
    for file, checksum in item["sha256"].items():
        path=root/"models"/file
        if not path.is_file() or (verify and digest(path)!=checksum):
            raise ValueError(f"Modelo ausente o integridad incorrecta: {file}")
    return root/"models"/item["path"], item


def install(root, names):
    folder=root/"models"
    folder.mkdir(parents=True,exist_ok=True)
    entries=registry(root)
    def fetch(url,path):
        path.parent.mkdir(parents=True,exist_ok=True)
        temp=path.with_suffix(path.suffix+".download")
        urllib.request.urlretrieve(url,temp)
        temp.replace(path)
    for name in names:
        print(f"Instalando explícitamente {name}",flush=True)
        source=""
        if name.startswith("moonshine-"):
            from moonshine_voice.download import find_model_info,download_model_from_info
            from moonshine_voice import ModelArch
            arch=ModelArch.SMALL_STREAMING if name.endswith("small") else ModelArch.TINY_STREAMING
            info=find_model_info("es",arch)
            path,_=download_model_from_info(info,cache_root=folder/"moonshine")
            target=Path(path)
            source=info["download_url"]
            metadata={"arch":int(arch),"license":"MIT (Spanish streaming)","source":source}
        elif name.startswith("whisper-"):
            from huggingface_hub import snapshot_download,HfApi
            repo="Systran/faster-whisper-"+name.split("-",1)[1]
            revision=HfApi().model_info(repo).sha
            target=folder/name
            snapshot_download(repo,revision=revision,local_dir=target,
                              allow_patterns=["config.json","model.bin","tokenizer.json","vocabulary.*"])
            metadata={"revision":revision,"source":repo,"license":"MIT"}
        elif name == "silero":
            target=folder/"silero"/"silero_vad.onnx"
            source="https://raw.githubusercontent.com/snakers4/silero-vad/v6.2/src/silero_vad/data/silero_vad.onnx"
            fetch(source,target)
            metadata={"source":source,"license":"MIT","version":"6.2"}
        elif name.startswith("es_"):
            language,speaker,quality=name.split("-")
            prefix=f"es/{language}/{speaker}/{quality}"
            target=folder/"piper"/(name+".onnx")
            revision='cf910fb59f1d79ab3b625a63993a108751c6c25d'
            base="https://huggingface.co/rhasspy/piper-voices/resolve/"+revision+"/"+prefix+"/"
            for filename in [name+".onnx",name+".onnx.json","MODEL_CARD"]:
                destination=target.parent/(name+".MODEL_CARD" if filename=="MODEL_CARD" else filename)
                fetch(base+filename,destination)
            metadata={"source":base,"revision":revision,"license_card":str(target.with_suffix('.MODEL_CARD').name)}
        else:
            raise ValueError(f"Modelo desconocido {name}")
        files=[target] if target.is_file() else [p for p in target.rglob('*') if p.is_file() and '.cache' not in p.parts]
        if name.startswith('es_'):
            files += [Path(str(target)+'.json'),target.with_suffix('.MODEL_CARD')]
        entries[name]={"path":target.relative_to(folder).as_posix(),"sha256":{p.relative_to(folder).as_posix():digest(p) for p in files},**metadata}
        pending=folder/"registry.tmp"
        pending.write_text(json.dumps(entries,indent=2),encoding="utf-8")
        pending.replace(folder/"registry.json")
        print(f"{name}: instalado y SHA-256 registrado",flush=True)
