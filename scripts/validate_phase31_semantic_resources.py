"""Actual ONNX lifecycle in a fresh process; Python tracked allocations are not total RAM."""
import json
import multiprocessing as mp
import sys
import time
from dataclasses import replace
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))


def semantic_child(sender):
    import psutil
    import tracemalloc
    from jarvis.core.config import data_dir
    from jarvis.intelligence.dialogue_manager import DialogueManager
    from jarvis.intelligence.settings import IntelligenceConfig
    from jarvis.system.voice_resources import configure_voice_process
    configure_voice_process(2);tracemalloc.start();process=psutil.Process();rows=[]
    class Client:
        last_metrics={}
        def chat(self,*args,**kwargs):return 'La RAM guarda datos temporales.'
        def unload(self):pass
    manager=DialogueManager(data_dir(),replace(IntelligenceConfig(),llm_enabled=True),client=Client())
    def record(stage):
        rows.append({'stage':stage,'memory_info':process.memory_info()._asdict(),'python_traced_current_bytes':tracemalloc.get_traced_memory()[0],
            'semantic_loaded':manager.semantic.provider is not None})
    try:
        manager.interpret('Abre Steam');manager.interpret('¿Qué es la RAM?');record('direct_and_general_without_e5')
        manager.interpret('La música está demasiado fuerte');record('semantic_loaded')
        manager.interpret('Explícamelo más fácil');record('general_after_semantic')
        manager.semantic.unload();record('explicit_onnx_unload')
        manager.interpret('La música está demasiado fuerte');record('fresh_semantic_reload')
        sender.send(rows)
    finally:manager.close();sender.close()


def main():
    import psutil
    from jarvis.core.config import data_dir
    from jarvis.core.voice_session import VoiceSessionManager
    from jarvis.speech.settings import VoiceConfig
    context=mp.get_context('spawn');receiver,sender=context.Pipe(False)
    process=context.Process(target=semantic_child,args=(sender,));process.start();sender.close()
    try:
        if not receiver.poll(60):raise TimeoutError('Semantic lifecycle timed out')
        rows=receiver.recv()
    finally:
        receiver.close();process.join(3)
        if process.is_alive():process.terminate();process.join(3)
        released=not process.is_alive();process.close()
    events=[];voice=VoiceSessionManager(data_dir(),events.append,replace(VoiceConfig(),enabled=True,tts_enabled=False,first_wait_seconds=1,retain_seconds=20.0))
    start=time.monotonic();worker_seen=False
    try:
        voice.start('resource-test',bytes(32000))
        while time.monotonic()-start<35:
            voice.poll();worker_seen=worker_seen or voice.process is not None
            if worker_seen and voice.process is None:break
            time.sleep(.05)
        result={'configured_retention_seconds':20,'elapsed_until_worker_released':time.monotonic()-start,
                'worker_released':voice.process is None,'voice_error':voice.error}
    finally:voice.close()
    report={'method':__doc__,'semantic_stages':rows,'semantic_process_exited':released,'silent_voice_worker':result,
        'limits':'RSS includes Python interpreter plus native allocations and mappings. tracemalloc only tracks participating Python allocations; subtracting it from RSS is not a measurement of native/reserved memory. Windows private/pagefile fields are reported raw, not claimed as virtual reservation. External Ollama is excluded; its separate benchmark includes its own full tree. No mic or playback.'}
    Path('docs/reports/phase31-semantic-lifecycle.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print('Semantic and worker lifecycle completed',flush=True)


if __name__=='__main__':main()
