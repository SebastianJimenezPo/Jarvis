import sounddevice as sd


class SpeechPlaybackManager:
    def __init__(self,device='auto'):
        self.device=device

    def play(self,chunks,cancel,emit):
        stream=None
        first=True
        try:
            for chunk in chunks:
                if cancel.is_set():
                    break
                if stream is None:
                    device=None
                    if self.device!='auto':
                        matches=[i for i,d in enumerate(sd.query_devices()) if d['name']==self.device and d['max_output_channels']>0]
                        if len(matches)!=1:
                            raise RuntimeError('Salida ausente o ambigua')
                        device=matches[0]
                    stream=sd.OutputStream(samplerate=chunk.sample_rate,channels=chunk.sample_channels,
                                           dtype='float32',device=device,blocksize=0)
                    stream.start()
                block=max(1,int(chunk.sample_rate*0.02))
                for offset in range(0,len(chunk.audio_float_array),block):
                    if cancel.is_set():
                        stream.abort()
                        return
                    if first:
                        emit('playback_started')
                        first=False
                    stream.write(chunk.audio_float_array[offset:offset+block])
            if stream:
                stream.stop()
        finally:
            if stream:
                stream.close()
