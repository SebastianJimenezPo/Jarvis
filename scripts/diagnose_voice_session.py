"""Voluntary bounded microphone session. Text opt-in; no personal audio files."""
import argparse
import json
import sys
import tempfile
import time
from dataclasses import replace
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def main():
    from jarvis.core.config import data_dir,load
    from jarvis.core.single_instance import SingleInstance
    from jarvis.core.lifecycle import LifecycleManager
    from jarvis.speech.models import registry
    from jarvis.speech.settings import load_voice,save_voice
    from jarvis.intelligence.settings import load_intelligence,save_intelligence
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds',type=int,default=90)
    parser.add_argument('--include-text',action='store_true',help='Autoriza texto de esta sesión en el informe local; no guardarlo en Git.')
    args=parser.parse_args()
    if not 10<=args.seconds<=300:parser.error('10–300 seconds required')
    root=data_dir();events=[];source=load(root)
    print('Cierra Jarvis. Esta prueba conserva micrófono, referencia y umbral; no guarda audio. Texto en informe:',args.include_text)
    with SingleInstance(),tempfile.TemporaryDirectory(prefix='jarvis-voluntary-diagnostic-') as directory:
        temporary=Path(directory);(temporary/'models').mkdir()
        entries=registry(root)
        for row in entries.values():
            row['path']=str(root/'models'/row['path']);row['sha256']={str(root/'models'/k):v for k,v in row['sha256'].items()}
        (temporary/'models'/'registry.json').write_text(json.dumps(entries),encoding='utf-8')
        # Reference installed embeddings in place; no copying or downloading.
        # Semantic routing remains off in this bounded capture diagnostic to
        # keep failures attributable; full semantic evaluation has its own script.
        save_intelligence(temporary,replace(load_intelligence(root),enabled=True,log_text=args.include_text,semantic_enabled=False))
        save_voice(temporary,replace(load_voice(root),enabled=True,log_transcripts=args.include_text))
        manager=LifecycleManager(replace(source,reference=str(source.reference_path(root))),temporary)
        notify=manager.voice.notify
        def observed(event):
            events.append(dict(event));notify(event)
        manager.voice.notify=observed
        manager.start();start=time.monotonic()
        try:
            while time.monotonic()-start<args.seconds:time.sleep(.1)
        finally:manager.stop()
    destination=root/'diagnostics'/'voice-voluntary.json';destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps({'origin':'Voluntary real microphone diagnostic; no audio saved. Temporary text flag never changes resident settings.',
        'text_authorized':args.include_text,'events':events},indent=2,ensure_ascii=False),encoding='utf-8')
    print(destination)


if __name__=='__main__':main()
