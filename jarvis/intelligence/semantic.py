import hashlib
import json
import time
from pathlib import Path
import numpy as np

EXAMPLES={
 'decrease_volume':['Está sonando muy duro','Pon el sonido más suave','Bájale un poco','Reduce la intensidad del audio','La música está demasiado fuerte'],
 'increase_volume':['No se oye casi nada','Pon la música más fuerte','Necesito escuchar más alto','Súbele un poquito'],
 'set_light_brightness':['La luz me está encandilando','La iluminación está demasiado fuerte','Que las luces estén más suaves','Bájales un poquito el brillo'],
 'pause_music':['Detén la canción por un momento','Haz una pausa en la música','Que deje de sonar un momento'],
 'turn_off_light':['Deja la habitación a oscuras','Quiero oscuridad en el cuarto','Apaga la iluminación'],
 'turn_on_light':['Alumbra la habitación','Necesito luz en el cuarto','Prende la iluminación']}


class EmbeddingProvider:
    def __init__(self,root,name,threads=4):self.root,self.name,self.threads=root,name,threads;self.session=None
    def load(self):
        import onnxruntime as ort
        from tokenizers import Tokenizer
        folder=self.root/'intelligence_models'/self.name
        registry=json.loads((self.root/'intelligence_models'/'registry.json').read_text(encoding='utf-8'))
        entry=registry[self.name]
        for filename,checksum in entry['sha256'].items():
            with (folder/filename).open('rb') as stream:
                if hashlib.file_digest(stream,'sha256').hexdigest()!=checksum:raise ValueError('Embedding integrity failure')
        self.tokenizer=Tokenizer.from_file(str(folder/'tokenizer.json'))
        pad=self.tokenizer.token_to_id('[PAD]')
        if pad is None:pad=self.tokenizer.token_to_id('<pad>')
        self.tokenizer.enable_padding(pad_id=pad,pad_token='<pad>' if self.name=='e5-small' else '[PAD]')
        self.tokenizer.enable_truncation(max_length=128 if self.name=='minilm' else 512)
        options=ort.SessionOptions();options.intra_op_num_threads=self.threads;options.inter_op_num_threads=1
        self.session=ort.InferenceSession(str(folder/entry['onnx']),sess_options=options,providers=['CPUExecutionProvider'])

    def encode(self,texts,query=False):
        if self.name=='e5-small':texts=[('query: ' if query else 'passage: ')+t for t in texts]
        batch=self.tokenizer.encode_batch(texts)
        inputs={'input_ids':np.array([x.ids for x in batch],dtype=np.int64),
                'attention_mask':np.array([x.attention_mask for x in batch],dtype=np.int64),
                'token_type_ids':np.array([x.type_ids for x in batch],dtype=np.int64)}
        output=self.session.run(None,{i.name:inputs[i.name] for i in self.session.get_inputs()})[0]
        if output.ndim==3:
            mask=inputs['attention_mask'][...,None]
            output=(output*mask).sum(axis=1)/np.maximum(mask.sum(axis=1),1)
        return output/np.maximum(np.linalg.norm(output,axis=1,keepdims=True),1e-12)

    def unload(self):self.session=None


class SemanticRouter:
    def __init__(self,root,config):
        self.root,self.config=root,config;self.provider=None;self.load_seconds=None;self.error=None
        self.thresholds=None
    def load(self):
        start=time.monotonic()
        self.provider=EmbeddingProvider(self.root,self.config.semantic_model,self.config.cpu_threads);self.provider.load()
        self.labels=[];texts=[]
        for intent,phrases in EXAMPLES.items():
            self.labels.extend([intent]*len(phrases));texts.extend(phrases)
        self.vectors=self.provider.encode(texts)
        calibration=self.root/'intelligence_models'/('calibration-'+self.config.semantic_model+'.json')
        self.thresholds=json.loads(calibration.read_text(encoding='utf-8')) if calibration.exists() else None
        self.load_seconds=time.monotonic()-start
    def rank(self,text):
        if self.provider is None:self.load()
        scores=self.vectors@self.provider.encode([text],query=True)[0]
        best={label:float(max(scores[i] for i,l in enumerate(self.labels) if l==label)) for label in set(self.labels)}
        ranked=sorted(best.items(),key=lambda x:x[1],reverse=True)
        return ranked
    def candidate(self,text):
        ranked=self.rank(text)
        if not self.thresholds:return None,ranked
        threshold=self.thresholds.get('intents',{}).get(ranked[0][0])
        margin=ranked[0][1]-ranked[1][1]
        if threshold and ranked[0][1]>=threshold['score'] and margin>=threshold['margin']:return ranked[0][0],ranked
        return None,ranked
