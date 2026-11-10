import time
from .models import resolve


class MoonshineAdapter:
    def __init__(self,root,name,threads=4,on_partial=lambda text:None):
        self.root,self.name,self.threads,self.on_partial=root,name,threads,on_partial
        self.transcriber=None
        self.stream=None

    def load(self):
        from moonshine_voice import ModelArch,Transcriber
        path,meta=resolve(self.root,self.name,verify=True)
        self.transcriber=Transcriber(path,ModelArch(meta['arch']),update_interval=0.5,
                                    options={'ort_provider':'cpu','log_output_text':'false'})

    def start_turn(self,turn_id):
        self.cancel_turn()
        self.stream=self.transcriber.create_stream(update_interval=0.5)
        self.stream.add_listener(lambda event: self.on_partial(event.line.text)
                                 if getattr(event,'line',None) and event.line.text else None)
        self.stream.start()
        self.last_update=0

    def feed_audio(self,samples,sample_rate=16000):
        self.stream.add_audio(samples.tolist(),sample_rate)

    def finish_turn(self):
        transcript=self.stream.stop()
        text=' '.join(line.text for line in transcript.lines).strip()
        self.cancel_turn()
        return text

    def cancel_turn(self):
        if self.stream is not None:
            self.stream.close()
            self.stream=None

    def unload(self):
        self.cancel_turn()
        if self.transcriber:
            self.transcriber.close()
            self.transcriber=None
