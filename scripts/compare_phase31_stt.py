"""Same synthetic PCM once, three isolated STT profiles. No microphone or playback."""
import json
import multiprocessing as mp
import sys
import time
import hashlib
from dataclasses import replace
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

PHRASES=['Azul','Rojo','No','Sí','Cancela','Mejor azules','La otra','Al treinta','Más bajo','Déjalo así',
         'Pon las luces rojas','No, mejor azules','Y bájales el brillo','Mejor al treinta por ciento',
         'Por favor pon la luz principal de color rojo','No, mejor cambia las luces a color azul']


def run_profile(engine,threads,clips,sender):
    from jarvis.core.config import data_dir
    from jarvis.speech.recognition import make_engine
    from jarvis.speech.settings import VoiceConfig
    from jarvis.system.voice_resources import configure_voice_process
    from jarvis.speech.evaluation import error_counts
    import psutil
    configure_voice_process(threads);model=make_engine(data_dir(),replace(VoiceConfig(),engine=engine,cpu_threads=threads))
    start=time.perf_counter();model.load();loaded=time.perf_counter()-start;rows=[]
    try:
        for index,(text,audio) in enumerate(clips):
            model.start_turn(str(index));start=time.perf_counter()
            for offset in range(0,len(audio),512):
                model.feed_audio(audio[offset:offset+512])
                if engine.startswith('moonshine'):time.sleep(.032)
            final_start=time.perf_counter();actual=model.finish_turn()
            rows.append({'expected':text,'actual':actual,'errors':error_counts(text,actual),
                         'elapsed_seconds':time.perf_counter()-start,'finalize_seconds':time.perf_counter()-final_start})
        sender.send({'engine':engine,'cpu_threads':threads,'load_seconds':loaded,'rows':rows,
                     'rss_bytes':psutil.Process().memory_info().rss,'affinity':psutil.Process().cpu_affinity()})
    finally:model.unload();sender.close()


def main():
    import numpy as np
    from jarvis.core.config import data_dir
    from jarvis.speech.piper_adapter import PiperAdapter
    from jarvis.audio.converter import Converter
    voice=PiperAdapter(data_dir(),'es_MX-ald-medium');voice.load();clips=[]
    try:
        for text in PHRASES:
            chunks=list(voice.synthesize(text));rate=chunks[0].sample_rate
            samples=np.concatenate([np.zeros(rate//4,dtype=np.float32),*[c.audio_float_array for c in chunks],np.zeros(rate,dtype=np.float32)])
            pcm=Converter(rate).convert(samples);clips.append((text,np.frombuffer(pcm,dtype='<i2').astype(np.float32)/32768))
    finally:voice.unload()
    rows=[];context=mp.get_context('spawn')
    for engine,threads in [('moonshine-small',2),('moonshine-small',4),('whisper-base',2)]:
        receiver,sender=context.Pipe(False);process=context.Process(target=run_profile,args=(engine,threads,clips,sender));process.start();sender.close()
        try:
            if not receiver.poll(180):raise TimeoutError('STT comparison timed out')
            row=receiver.recv();rows.append(row);print(engine,threads,'completed',flush=True)
        finally:
            receiver.close();process.join(3)
            if process.is_alive():process.terminate();process.join(3)
            process.close()
    report={'method':__doc__,'source':'Piper es_MX-ald-medium generated once in RAM; fixed identical arrays across profiles. Moonshine receives 32-ms paced blocks; Whisper uses completed audio. Not physical speech or WER generalization.',
            'clips':[{'text':text,'sha256_pcm_float32':hashlib.sha256(audio.tobytes()).hexdigest(),'seconds':len(audio)/16000} for text,audio in clips], 'profiles':rows}
    Path('docs/reports/phase31-stt-comparison.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')


if __name__=='__main__':main()
