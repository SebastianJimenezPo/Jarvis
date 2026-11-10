"""Text-only dialogue diagnostics: structured simulated decisions, no microphone or real actions."""
import argparse
import json
import sys
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def main():
    from jarvis.core.config import data_dir
    from jarvis.intelligence.settings import load_intelligence
    from jarvis.intelligence.dialogue_manager import DialogueManager
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--text',action='append',default=[])
    p.add_argument('--no-llm',action='store_true')
    p.add_argument('--no-semantic',action='store_true')
    p.add_argument('--data-dir',type=Path,default=data_dir())
    args=p.parse_args();config=load_intelligence(args.data_dir)
    config=replace(config,llm_enabled=config.llm_enabled and not args.no_llm,
                   semantic_enabled=config.semantic_enabled and not args.no_semantic)
    manager=DialogueManager(args.data_dir,config);manager.begin_session('text-diagnostic')
    try:
        texts=iter(args.text) if args.text else iter(lambda:input('Tú (vacío para salir): '),'')
        for index,text in enumerate(texts):
            decision,response=manager.interpret(text,'text-diagnostic',str(index))
            print(json.dumps({'decision':decision.model_dump(mode='json'),'response':response,'error':manager.last_error},ensure_ascii=False,indent=2))
    finally:manager.close()


if __name__=='__main__':main()
