"""Bounded local STT comparison. No Groq, downloads, microphone capture or playback.

Default: six newly generated synthetic clips, identical arrays across profiles.
--dataset: local JSON array of {audio: WAV path, text: reference}; mono 16-bit PCM.
Personal recordings/reports should remain under ignored build/, never Git.
"""
import argparse
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import sys
import wave
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.compare_phase31_stt import run_profile


def main():
    import numpy as np
    from jarvis.core.config import data_dir
    from jarvis.speech.piper_adapter import PiperAdapter
    from jarvis.audio.converter import Converter
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',type=Path)
    parser.add_argument('--output',type=Path,default=Path('build/next-stt-comparison.json'))
    args=parser.parse_args()
    if args.output.exists():parser.error('Preserve previous results')
    clips=[]
    if args.dataset:
        records=json.loads(args.dataset.read_text(encoding='utf-8'))
        if not isinstance(records,list) or not 1<=len(records)<=8:parser.error('Expected 1..8 clips')
        for row in records:
            path=Path(row['audio'])
            if not path.is_absolute():path=args.dataset.parent/path
            with wave.open(str(path),'rb') as source:
                if source.getnchannels()!=1 or source.getsampwidth()!=2 or source.getnframes()/source.getframerate()>20:
                    parser.error('Expected mono 16-bit WAV, at most 20 seconds')
                pcm=np.frombuffer(source.readframes(source.getnframes()),dtype='<i2').astype(np.float32)/32768
                audio=np.frombuffer(Converter(source.getframerate()).convert(pcm),dtype='<i2').astype(np.float32)/32768
            clips.append((row['text'],audio))
    else:
        voice=PiperAdapter(data_dir(),'es_MX-ald-medium');voice.load()
        try:
            for text in ['Spotify','Cancela','Sí','Mejor Spotify','Abre una aplicación','Abre Steam, pero todavía no hagas nada']:
                chunks=list(voice.synthesize(text));rate=chunks[0].sample_rate
                audio=np.concatenate([np.zeros(rate//4,dtype=np.float32),*[c.audio_float_array for c in chunks],np.zeros(rate,dtype=np.float32)])
                clips.append((text,np.frombuffer(Converter(rate).convert(audio),dtype='<i2').astype(np.float32)/32768))
        finally:voice.unload()
    profiles=[];context=mp.get_context('spawn')
    for engine in ('moonshine-small','whisper-base'):
        receiver,sender=context.Pipe(False)
        process=context.Process(target=run_profile,args=(engine,2,clips,sender));process.start();sender.close()
        try:
            if not receiver.poll(60):raise TimeoutError('Local comparison exceeded its deadline')
            result=receiver.recv();profiles.append(result)
            print(engine,'finished',flush=True)
        finally:
            receiver.close();process.join(3)
            if process.is_alive():process.terminate();process.join(3)
            process.close()
    report=dict(method=__doc__,origin='local supplied recordings' if args.dataset else 'new synthetic Piper generation, not the exact first integration stimuli',
        clips=[dict(text=text,sha256_float32=hashlib.sha256(audio.tobytes()).hexdigest(),seconds=len(audio)/16000) for text,audio in clips],
        profiles=profiles,limits='Same arrays across recognizers; no default/config changes. Synthetic accuracy is not physical user accuracy. Moonshine feed is paced; elapsed time is not a directly comparable decoding benchmark.')
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
