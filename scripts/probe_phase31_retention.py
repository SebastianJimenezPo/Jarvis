"""Sequential retention and conversational streaming probes; no playback or actions."""
import json
import re
import http.client
import sys
import time
from dataclasses import replace
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def main():
    from jarvis.intelligence.settings import IntelligenceConfig
    from jarvis.intelligence.ollama_client import OllamaClient
    cfg=IntelligenceConfig();rows=[]
    messages=[{'role':'system','content':'Eres Jarvis. Explica en una frase breve.'},{'role':'user','content':'¿Qué es la memoria RAM?'}]
    if OllamaClient(cfg).running():raise RuntimeError('Shared Ollama service is busy')
    for keep in (0,30,60):
        client=OllamaClient(replace(cfg,keep_alive_seconds=keep))
        try:
            timings=[]
            for index in range(2):
                if index:time.sleep(2)
                start=time.perf_counter();client.chat(messages)
                timings.append({'elapsed_seconds':time.perf_counter()-start,'metrics':client.last_metrics.copy(),'loaded_after':client.running()})
            rows.append({'keep_alive_seconds':keep,'requests':timings})
            if keep==30:
                start=time.monotonic()
                while client.running() and time.monotonic()-start<36:time.sleep(1)
                rows[-1]['observed_seconds_until_empty_after_last_response']=time.monotonic()-start
                rows[-1]['models_after_wait']=client.running()
        finally:client.unload()
    streaming=[];client=OllamaClient(cfg)
    try:
        for index in range(3):
            conn=http.client.HTTPConnection('127.0.0.1',11434,timeout=12);start=time.perf_counter();first=None;sentence=None;answer=''
            body={'model':cfg.model,'messages':messages,'stream':True,'think':False,'keep_alive':'30s',
                  'options':{'num_thread':2,'num_gpu':0,'num_ctx':2048,'num_predict':160,'temperature':.1,'seed':17}}
            conn.request('POST','/api/chat',json.dumps(body),{'Content-Type':'application/json'})
            response=conn.getresponse();last={};total_bytes=0
            try:
                while True:
                    line=response.readline(100001)
                    if not line:break
                    total_bytes+=len(line)
                    if len(line)>100000 or total_bytes>1000000:raise ValueError('Streaming response too large')
                    last=json.loads(line);piece=last.get('message',{}).get('content','');answer+=piece
                    if piece.strip() and first is None:first=time.perf_counter()-start
                    if sentence is None and re.search(r'[.!?](?:\s|$)',answer):sentence=time.perf_counter()-start
                    if last.get('done'):break
            finally:conn.close()
            streaming.append({'state':'cold' if index==0 else 'warm','first_content_seconds':first,'first_complete_sentence_seconds':sentence,
                'total_seconds':time.perf_counter()-start,'answer':answer,'eval_duration':last.get('eval_duration'),'eval_count':last.get('eval_count')})
    finally:client.used_models.add(cfg.model);client.unload()
    Path('docs/reports/phase31-retention-streaming.json').write_text(json.dumps({'retention':rows,'streaming_probe':streaming,
        'limits':'Single short stimulus, identical seed; 2-second gap and only 30-second expiry observed. 60-second model was explicitly unloaded, not observed through expiry. Streaming probe is conversational text only, no incremental Piper architecture and no partial action interpretation.'},indent=2,ensure_ascii=False),encoding='utf-8')
    print('Retention and streaming probe completed',flush=True)


if __name__=='__main__':main()
