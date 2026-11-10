from .models import resolve


class PiperAdapter:
    def __init__(self,root,voice,threads=4,volume=0.75):
        self.root,self.name,self.threads,self.volume=root,voice,threads,volume
        self.voice=None

    def load(self):
        from piper import PiperVoice
        from piper.config import PiperConfig
        import onnxruntime as ort
        import json
        path,_=resolve(self.root,self.name,verify=True)
        options=ort.SessionOptions()
        options.intra_op_num_threads=self.threads
        options.inter_op_num_threads=1
        self.voice=PiperVoice(session=ort.InferenceSession(str(path),sess_options=options,providers=['CPUExecutionProvider']),
                              config=PiperConfig.from_dict(json.loads(path.with_suffix('.onnx.json').read_text(encoding='utf-8'))))

    def synthesize(self,text):
        from piper import SynthesisConfig
        return self.voice.synthesize(text,syn_config=SynthesisConfig(volume=self.volume))

    def cancel(self):
        # ONNX call is synchronous; playback cancellation is checked between chunks.
        # Supervisor can terminate the worker for bounded pause/shutdown.
        return

    def unload(self):
        self.voice=None
