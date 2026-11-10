import json
import sys
import time
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def main():
    from jarvis.core.config import data_dir
    from jarvis.intelligence.dialogue_manager import DialogueManager
    from jarvis.intelligence.settings import IntelligenceConfig
    reports=[]
    for name in ['qwen3:1.7b','qwen3.5:2b']:
        manager=DialogueManager(data_dir(),replace(IntelligenceConfig(),model=name,fallback_model=name,semantic_enabled=False,timeout_seconds=45.0))
        rows=[]
        try:
            for index,text in enumerate(['¿Qué es una variable?','Explícamelo más fácil','Ponme un ejemplo']):
                d,response=manager.interpret(text,name,str(index))
                rows.append({'text':text,'response':response,'route':d.route,'seconds':d.seconds,'metrics':manager.client.last_metrics.copy(),'error':manager.last_error})
                print(name,index,round(d.seconds,2),d.route,flush=True)
            running=manager.client.running()
        finally:manager.close()
        reports.append({'model':name,'rows':rows,'running':running})
        Path('docs/reports/conversation-comparison.json').write_text(json.dumps(reports,indent=2,ensure_ascii=False),encoding='utf-8')


if __name__=='__main__':main()
