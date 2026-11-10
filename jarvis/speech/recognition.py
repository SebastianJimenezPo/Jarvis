from dataclasses import dataclass
from typing import Protocol, Callable
import time


@dataclass(frozen=True)
class TranscriptEvent:
    session_id: str
    turn_id: str
    text: str
    final: bool
    timestamp: float
    engine: str
    error: str | None = None


class SpeechRecognitionEngine(Protocol):
    def load(self) -> None: ...
    def start_turn(self, turn_id: str) -> None: ...
    def feed_audio(self, samples, sample_rate: int = 16000) -> None: ...
    def finish_turn(self) -> str: ...
    def cancel_turn(self) -> None: ...
    def unload(self) -> None: ...


class TranscriptManager:
    def __init__(self, session_id, engine, emit: Callable):
        self.session_id,self.engine,self.emit=session_id,engine,emit
        self.finalized=set()

    def publish(self,turn,text,final):
        if turn in self.finalized:
            return
        if final:
            self.finalized.add(turn)
        self.emit(TranscriptEvent(self.session_id,turn,text,final,time.monotonic(),self.engine))


def make_engine(root,config,on_partial=lambda text:None):
    if config.engine.startswith('moonshine'):
        from .moonshine_adapter import MoonshineAdapter
        return MoonshineAdapter(root,config.engine,config.cpu_threads,on_partial)
    from .faster_whisper_adapter import FasterWhisperAdapter
    return FasterWhisperAdapter(root,config.engine,config.cpu_threads)
