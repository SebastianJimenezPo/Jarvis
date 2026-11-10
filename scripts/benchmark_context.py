"""Two compact LLM context settings, same conversation, real local inference."""
import json,sys
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def main():
    from jarvis.core.config import data_dir
    from jarvis.intelligence.settings import IntelligenceConfig
    from jarvis.intelligence.dialogue_manager import DialogueManager
    rows=[]
    for tokens in (1024,2048):
        manager=DialogueManager(data_dir(),replace(IntelligenceConfig(),context_tokens=tokens,semantic_enabled=False,timeout_seconds=30.0))
        try:
            for index,text in enumerate(['¿Qué es una variable?','Ponme un ejemplo más sencillo']):
                decision,response=manager.interpret(text,f'context-{tokens}',str(index))
                rows.append({'context_tokens':tokens,'text':text,'response':response,'route':decision.route,
                    'seconds':decision.seconds,'metrics':manager.client.last_metrics.copy(),'error':manager.last_error})
                print(tokens,index,decision.route,round(decision.seconds,2),flush=True)
        finally:manager.close()
    Path('docs/reports/context-comparison.json').write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding='utf-8')


if __name__=='__main__':main()
