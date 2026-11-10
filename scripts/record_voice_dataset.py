"""Voluntary benchmark corpus recording; saved only after explicit consent."""
import argparse
import json
import sys
import time
import wave
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from jarvis.core.config import data_dir,load
from jarvis.core.single_instance import SingleInstance
from jarvis.audio.capture import Capture
from jarvis.audio.converter import Converter


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--start',type=int,default=1)
    p.add_argument('--count',type=int,default=10)
    args=p.parse_args()
    phrases=json.loads((Path(__file__).resolve().parents[1]/'docs'/'voice_corpus.json').read_text(encoding='utf-8'))
    if input('Estas grabaciones se conservarán en la carpeta elegida. Escribe GUARDAR para autorizar: ').strip()!='GUARDAR':
        return
    args.output.mkdir(parents=True,exist_ok=True)
    config=load(data_dir())
    with SingleInstance():
        for index,phrase in enumerate(phrases[args.start-1:args.start-1+args.count],args.start):
            input(f'{index}: {phrase}\nEnter para grabar hasta 8 segundos; espera la indicación HABLA.')
            capture=Capture(config.device,500);converter=Converter(capture.rate);pcm=bytearray()
            try:
                capture.start()
                print('HABLA',flush=True)
                until=time.monotonic()+8
                while time.monotonic()<until:
                    _,block=capture.blocks.get(timeout=3)
                    pcm.extend(converter.convert(block))
            finally:
                capture.close()
            if input('¿Conservar esta muestra? [s/N] ').strip().lower()!='s':
                continue
            name=f'{index:03d}.wav'
            if (args.output/name).exists():
                raise FileExistsError('La muestra ya existe; usa otra carpeta o --start')
            with wave.open(str(args.output/name),'wb') as out:
                out.setnchannels(1);out.setsampwidth(2);out.setframerate(16000);out.writeframes(pcm)
            with (args.output/'manifest.jsonl').open('a',encoding='utf-8') as manifest:
                manifest.write(json.dumps({'file':name,'text':phrase},ensure_ascii=False)+'\n')


if __name__=='__main__':
    main()
