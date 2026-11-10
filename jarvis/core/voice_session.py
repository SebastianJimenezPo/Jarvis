"""Light supervisor on lifecycle thread. No model imports or inference here."""
import multiprocessing as mp
import queue
import time
from jarvis.speech.settings import load_voice,VoiceConfig
from jarvis.speech.models import resolve


class VoiceSessionManager:
    def __init__(self,root,notify,config=None):
        self.root,self.notify=root,notify
        initial_error=None
        try:
            self.config=config or load_voice(root)
        except (ValueError,TypeError,OSError) as exc:
            self.config=VoiceConfig()
            initial_error=f'Configuración de voz inválida; núcleo Fase 1 conservado: {exc}'
        self.context=mp.get_context('spawn')
        self.process=None
        self.job=None
        self.active=False
        self.session_id=None
        self.state='IDLE'
        self.error=initial_error
        self.last_activity=time.monotonic()
        self.last_progress=self.last_activity
        self.metrics={'sessions_opened':0,'sessions_closed':0,'empty_transcripts':0,'errors':0,'cancelled':0,'audio_dropped':0,'turns':0}
        self.last_transcript=None
        self.timings={}

    def available(self):
        if not self.config.enabled:
            return False
        try:
            resolve(self.root,self.config.engine)
            resolve(self.root,'silero')
            if self.config.tts_enabled:
                resolve(self.root,self.config.voice)
            return True
        except Exception as exc:
            self.error=str(exc)
            self.state='UNAVAILABLE'
            return False

    def _ensure_worker(self):
        if self.process and self.process.is_alive():
            return
        self.close()
        from jarvis.speech.worker import voice_worker
        self.inbox=self.context.Queue(maxsize=round(self.config.pending_audio_seconds/0.02)+4)
        self.outbox=self.context.Queue(maxsize=128)
        self.cancel_event=self.context.Event()
        self.process=self.context.Process(target=voice_worker,args=(self.inbox,self.outbox,self.cancel_event,str(self.root),self.config),name='jarvis-voice')
        self.process.start()
        from jarvis.system.process_job import ProcessJob
        from types import SimpleNamespace
        self.job=ProcessJob(SimpleNamespace(_handle=self.process.sentinel))

    def start(self,session_id,preroll=b'',test_tts=False,acoustic_activation=False):
        self._ensure_worker()
        self.active=True
        self.session_id=str(session_id)
        self.state='PREPARING'
        self.last_progress=time.monotonic()
        self.error=None
        self.cancel_event.clear()
        self.inbox.put_nowait(('test_tts' if test_tts else 'session',self.session_id,preroll,acoustic_activation))
        self.metrics['sessions_opened']+=1

    def feed(self,pcm,timestamp):
        if not self.active or self.state not in ('PREPARING','WAITING_FOR_SPEECH','LISTENING','WAITING_FOR_FOLLOWUP'):
            return
        try:
            self.inbox.put_nowait(('audio',self.session_id,timestamp,pcm))
        except queue.Full:
            self.metrics['audio_dropped']+=1
            self._error('Búfer de arranque lleno; sesión cancelada para evitar transcripción incompleta')

    def cancel(self):
        if self.process:
            self.cancel_event.set()

    def _error(self,error):
        session=self.session_id
        self.error=error
        self.metrics['errors']+=1
        self.close()
        self.notify({'kind':'voice_error','session_id':session,'error':error,'monotonic':time.monotonic()})

    def poll(self):
        if not self.process:
            return
        try:
            while True:
                event=self.outbox.get_nowait()
                if event.get('session_id')!=self.session_id or not self.active:
                    continue
                self.last_progress=time.monotonic()
                kind=event['kind']
                if kind=='voice_state':
                    self.state=event['state']
                elif kind=='transcript':
                    if self.config.log_transcripts:
                        self.last_transcript=event['text']
                    else:
                        event.pop('text',None)
                elif kind=='session_end':
                    self.active=False
                    self.state='IDLE'
                    self.metrics['sessions_closed']+=1
                    self.last_activity=time.monotonic()
                elif kind=='voice_error':
                    self._error(event['error'])
                    return
                elif kind in ('empty_transcript','cancelled'):
                    self.metrics['empty_transcripts' if kind=='empty_transcript' else 'cancelled']+=1
                elif kind=='turn_completed':
                    self.metrics['turns']+=1
                if 'seconds' in event or 'load_seconds' in event or kind=='transcription_timing':
                    self.timings[kind]={k:v for k,v in event.items() if 'seconds' in k}
                self.notify(event)
        except queue.Empty:
            pass
        if not self.process.is_alive():
            self._error(f'El proceso de voz terminó: {self.process.exitcode}')
        elif self.active:
            timeout=(self.config.preparation_timeout_seconds if self.state=='PREPARING' else
                     max(self.config.processing_timeout_seconds,self.config.followup_seconds+self.config.max_turn_seconds+5))
            if time.monotonic()-self.last_progress>timeout:
                self._error('Timeout del proceso de voz')
        elif time.monotonic()-self.last_activity>=self.config.retain_seconds:
            self.close()

    def close(self):
        if self.process:
            self.cancel_event.set()
            try:
                self.inbox.put_nowait(('stop',))
            except queue.Full:
                pass
            self.process.join(timeout=0.3)
            if self.process.is_alive():
                self.process.terminate()
                self.process.join(timeout=3)
            self.process.close()
            self.process=None
            for q in (self.inbox,self.outbox):
                q.cancel_join_thread()
                q.close()
            if self.job:
                self.job.close()
                self.job=None
        self.active=False
        self.state='IDLE'

    def snapshot(self):
        return {'enabled':self.config.enabled,'engine':self.config.engine,'model':self.config.engine,
                'voice':self.config.voice,'tts_enabled':self.config.tts_enabled,'state':self.state,
                'session_id':self.session_id,'last_error':self.error,'last_transcript':self.last_transcript,
                'worker_pid':self.process.pid if self.process else None,'metrics':self.metrics.copy(),'timings':self.timings.copy()}
