from collections import deque
import numpy as np


class SpeechTurnSegmenter:
    """Audio-time segmentation: onset hysteresis, trailing silence and hard speech cap."""
    def __init__(self,config):
        self.config=config
        self.reset()

    def reset(self):
        self.pre=deque(maxlen=12)  # 384 ms including onset confirmation
        self.active=False
        self.voiced_ms=self.silent_ms=self.duration_ms=0

    def feed(self,frame,probability):
        ms=len(frame)/16
        voiced=probability>=self.config.vad_threshold
        started=False
        if not self.active:
            self.pre.append(frame.copy())
            self.voiced_ms=self.voiced_ms+ms if voiced else 0
            if self.voiced_ms < self.config.speech_start_ms:
                return None,None,False
            self.active=True
            started=True
            payload=np.concatenate(list(self.pre))
            self.pre.clear()
        else:
            payload=frame
        self.duration_ms+=ms
        self.silent_ms=0 if voiced else self.silent_ms+ms
        reason=('max_duration' if self.duration_ms>=self.config.max_turn_seconds*1000
                else 'silence' if self.silent_ms>=self.config.end_silence_ms else None)
        return payload,reason,started
