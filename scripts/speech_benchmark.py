"""Offline benchmark of explicitly supplied WAV files; no recording or downloads."""
import argparse
import json
import subprocess
import sys
import time
import wave
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',type=Path,required=True,help='JSONL: file, text; WAV relative to manifest')
    parser.add_argument('--engines',nargs='+',default=['moonshine-small','moonshine-tiny','whisper-base'])
    parser.add_argument('--output',type=Path,default=Path('build/stt-benchmark.json'))
    parser.add_argument('--data-dir',type=Path)
    parser.add_argument('--single-engine',default=None)
    parser.add_argument('--repeats',type=int,default=2)
    args=parser.parse_args()
    if not args.single_engine:
        reports=[]
        args.output.parent.mkdir(parents=True,exist_ok=True)
        for engine in args.engines:
            result=args.output.with_name(engine+'.json')
            command=[sys.executable,__file__,'--dataset',str(args.dataset.resolve()),'--output',str(result.resolve()),
                     '--single-engine',engine,'--repeats',str(args.repeats)]
            if args.data_dir:
                command+=['--data-dir',str(args.data_dir)]
            subprocess.run(command,check=True,timeout=1800,creationflags=subprocess.CREATE_NO_WINDOW)
            reports.append(json.loads(result.read_text(encoding='utf-8')))
        args.output.write_text(json.dumps({'engines':reports,'note':'Same supplied WAVs; STT only, no VAD segmentation in these accuracy scores.'},indent=2,ensure_ascii=False),encoding='utf-8')
        print(args.output)
        return
    import numpy as np
    import psutil
    from dataclasses import replace
    from jarvis.core.config import data_dir
    from jarvis.speech.settings import VoiceConfig
    from jarvis.speech.recognition import make_engine
    from jarvis.speech.evaluation import error_counts
    from jarvis.audio.converter import Converter
    root=args.data_dir or data_dir()
    engine=make_engine(root,replace(VoiceConfig(),engine=args.single_engine))
    start=time.perf_counter();engine.load();load=time.perf_counter()-start
    process=psutil.Process();before=process.cpu_times();rss_peak=process.memory_info().rss
    rows=[];start=time.perf_counter()
    entries=[json.loads(line) for line in args.dataset.read_text(encoding='utf-8').splitlines() if line.strip()]
    for entry in entries:
        with wave.open(str(args.dataset.parent/entry['file']),'rb') as wav:
            if wav.getsampwidth()!=2:
                raise ValueError('Se requiere WAV PCM16')
            rate,channels=wav.getframerate(),wav.getnchannels()
            raw=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2').reshape(-1,channels).mean(axis=1).astype(np.float32)/32768
        samples=np.frombuffer(Converter(rate).convert(np.concatenate([raw,np.zeros(rate,dtype=np.float32)])),dtype='<i2').astype(np.float32)/32768
        for repeat in range(args.repeats):
            t0=time.perf_counter();engine.start_turn(f"{entry['file']}:{repeat}")
            for offset in range(0,len(samples),1600):
                engine.feed_audio(samples[offset:offset+1600])
            text=engine.finish_turn();elapsed=time.perf_counter()-t0
            rss_peak=max(rss_peak,process.memory_info().rss)
            rows.append({'file':entry['file'],'reference':entry['text'],'text':text,'repeat':repeat,
                         'seconds':elapsed,'audio_seconds':len(raw)/rate,'rtf':elapsed/(len(raw)/rate),
                         **error_counts(entry['text'],text)})
    elapsed=time.perf_counter()-start;after=process.cpu_times()
    t0=time.perf_counter();engine.unload();unload=time.perf_counter()-t0
    t0=time.perf_counter();engine.load();reload_seconds=time.perf_counter()-t0;engine.unload()
    durations=[r['seconds'] for r in rows]
    words=sum(r['reference_words'] for r in rows);characters=sum(r['reference_characters'] for r in rows)
    report={'engine':args.single_engine,'load_seconds':load,'reload_seconds':reload_seconds,'unload_seconds':unload,
            'transcriptions':len(rows),'wer':sum(r['word_errors'] for r in rows)/words if words else None,
            'cer':sum(r['character_errors'] for r in rows)/characters if characters else None,
            'latency_mean_seconds':float(np.mean(durations)) if durations else None,
            'latency_median_seconds':float(np.median(durations)) if durations else None,
            'latency_p95_seconds':float(np.percentile(durations,95)) if durations else None,
            'rss_peak_sampled_bytes':rss_peak,'cpu_machine_percent':100*((after.user+after.system)-(before.user+before.system))/elapsed/(psutil.cpu_count() or 1),
            'empty_transcripts':sum(not r['text'].strip() for r in rows),
            'silence_hallucinations':sum(not r['reference'].strip() and bool(r['text'].strip()) for r in rows),
            'audio_origin':'Supplied dataset: caller must identify real or synthetic in accompanying report','rows':rows}
    args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')


if __name__=='__main__':
    main()
