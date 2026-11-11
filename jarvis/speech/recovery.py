"""One sequential, bounded alternative STT process. PCM stays in RAM."""
import multiprocessing as mp
import time
from .models import resolve


def _transcribe(root,audio,threads,sender):
    from .faster_whisper_adapter import FasterWhisperAdapter
    engine=FasterWhisperAdapter(root,'whisper-base',threads)
    try:
        engine.load();engine.start_turn('recovery');engine.feed_audio(audio)
        sender.send({'text':engine.finish_turn()})
    except Exception as exc:sender.send({'error':type(exc).__name__})
    finally:engine.unload();sender.close()


def transcribe_alternative(root,audio,config,cancel):
    from jarvis.intelligence.ollama_client import RequestCancelled
    if not 8000<=len(audio)<=320000:raise ValueError('Recovery requires 0.5–20 seconds of PCM')
    resolve(root,'whisper-base')  # Explicit installation only; never fetch a model.
    context=mp.get_context('spawn');receiver,sender=context.Pipe(duplex=False)
    process=context.Process(target=_transcribe,args=(root,audio,config.cpu_threads,sender),name='jarvis-stt-recovery',daemon=True)
    process.start();sender.close();deadline=time.monotonic()+config.stt_recovery_timeout_seconds
    try:
        while not receiver.poll(.025):
            if cancel.is_set():raise RequestCancelled('Alternative STT cancelled')
            if time.monotonic()>=deadline:raise TimeoutError('Alternative STT timed out')
            if not process.is_alive():raise RuntimeError('Alternative STT exited')
        result=receiver.recv()
        if cancel.is_set():raise RequestCancelled('Alternative STT cancelled')
        if 'error' in result:raise RuntimeError('Alternative STT unavailable: '+result['error'])
        return result['text']
    finally:
        receiver.close();process.join(timeout=.1)
        if process.is_alive():process.terminate();process.join(timeout=2)
        process.close()
