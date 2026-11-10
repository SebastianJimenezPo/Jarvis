import numpy as np
from .models import resolve


class FasterWhisperAdapter:
    def __init__(self,root,name,threads=4):
        self.root,self.name,self.threads=root,name,threads
        self.model=None
        self.audio=[]
        self.samples=0

    def load(self):
        from faster_whisper import WhisperModel
        path,_=resolve(self.root,self.name,verify=True)
        self.model=WhisperModel(str(path),device='cpu',compute_type='int8',cpu_threads=self.threads,
                                num_workers=1,local_files_only=True)

    def start_turn(self,turn_id):
        self.cancel_turn()

    def feed_audio(self,samples,sample_rate=16000):
        if sample_rate!=16000:
            raise ValueError('Se requiere 16 kHz')
        self.samples+=len(samples)
        if self.samples>16000*65:
            raise BufferError('Turno excede límite de memoria STT')
        self.audio.append(samples.copy())

    def finish_turn(self):
        if not self.audio:
            return ''
        segments,_=self.model.transcribe(np.concatenate(self.audio),language='es',beam_size=1,
                                         vad_filter=False,condition_on_previous_text=False)
        text=' '.join(s.text.strip() for s in segments)
        self.cancel_turn()
        return text

    def cancel_turn(self):
        self.audio=[]
        self.samples=0

    def unload(self):
        self.cancel_turn()
        self.model=None
