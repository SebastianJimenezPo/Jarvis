"""Voluntary guided wake attempts and labelled noise windows. Never saves microphone audio."""
import argparse
import json
import sys
import time
from dataclasses import replace
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def main():
    from jarvis.core.config import data_dir,load
    from jarvis.core.lifecycle import LifecycleManager
    from jarvis.core.single_instance import SingleInstance
    from jarvis.core.events import Kind
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempts',type=int,default=10)
    parser.add_argument('--window',type=float,default=5)
    parser.add_argument('--noise-seconds',type=float,default=30)
    args=parser.parse_args()
    if not 1<=args.attempts<=50 or not 2<=args.window<=15 or not 0<=args.noise_seconds<=300:parser.error('Invalid test bounds')
    root=data_dir();config=load(root);rows=[]
    print('Cierra Jarvis antes de comenzar. Se usará el micrófono y umbral actuales. No se guarda audio ni texto hablado.')
    with SingleInstance():
        manager=LifecycleManager(replace(config,active_seconds=1.0,confirmation=False),root)
        manager.voice.config=replace(manager.voice.config,enabled=False)
        observed=[]
        manager.bus.subscribe(lambda event:observed.append({'monotonic':time.monotonic(),'score':event.detail.get('score'),'accepted':True}) if event.kind==Kind.WAKEWORD_DETECTED else None)
        manager.start()
        try:
            deadline=time.monotonic()+20
            while manager.snapshot()['state']!='DORMANT':
                if time.monotonic()>deadline:raise RuntimeError('Micrófono/detector no preparado')
                time.sleep(.05)
            for index in range(args.attempts):
                input(f'Intento {index+1}/{args.attempts}: Enter y pronuncia Jarvis una vez dentro de {args.window:g} segundos. ')
                before=manager.snapshot()['activations'];start=time.monotonic();time.sleep(args.window)
                after=manager.snapshot();rows.append({'attempt':index+1,'labelled_utterances':1,'start_monotonic':start,
                    'accepted_detections':after['activations']-before,'detector_events':[event for event in observed if event['monotonic']>=start],
                    'threshold':config.threshold,'device':after['last_capture_device'],'state':after['state']})
                # Wait through cooldown before the next labelled attempt.
                time.sleep(config.cooldown_seconds+1)
            input('Ventana de ruido: no pronuncies Jarvis; Enter para comenzar. ')
            before=manager.snapshot()['activations'];time.sleep(args.noise_seconds)
            noise={'seconds':args.noise_seconds,'detections_without_labelled_wake':manager.snapshot()['activations']-before}
        finally:manager.stop()
    destination=root/'diagnostics'/'wake-guided.json';destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps({'attempts':rows,'noise':noise,'limits':'Only detector-reported scores/detections are observable. Labelled attempts supply the missed-attempt denominator; no rejected score is invented. Threshold/reference/device unchanged.'},indent=2,ensure_ascii=False),encoding='utf-8')
    print(destination)


if __name__=='__main__':main()
