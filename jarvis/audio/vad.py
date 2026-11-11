import numpy as np
from jarvis.speech.models import resolve


class SpeechActivityDetector:
    """Silero ONNX v6.2 recurrent model, CPU only, fixed 512-sample frames."""
    def __init__(self,root):
        import onnxruntime as ort
        path,_=resolve(root,'silero',verify=True)
        options=ort.SessionOptions()
        options.intra_op_num_threads=1
        options.inter_op_num_threads=1
        options.add_session_config_entry('session.intra_op.allow_spinning','0')
        options.add_session_config_entry('session.inter_op.allow_spinning','0')
        self.model=ort.InferenceSession(str(path),sess_options=options,providers=['CPUExecutionProvider'])
        self.reset()

    def reset(self):
        self.state=np.zeros((2,1,128),dtype=np.float32)
        self.context=np.zeros((1,64),dtype=np.float32)

    def probability(self,samples):
        if len(samples)!=512:
            raise ValueError('Silero requiere 512 muestras a 16 kHz')
        data=np.concatenate([self.context,samples.reshape(1,-1)],axis=1)
        output,self.state=self.model.run(None,{'input':data,'state':self.state,'sr':np.array(16000,dtype=np.int64)})
        self.context=data[:,-64:].copy()
        return float(output[0][0])
