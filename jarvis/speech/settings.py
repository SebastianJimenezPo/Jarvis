import json
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass(frozen=True)
class VoiceConfig:
    version: int = 1
    enabled: bool = False
    engine: str = "moonshine-small"
    voice: str = "es_MX-ald-medium"
    tts_enabled: bool = True
    log_transcripts: bool = False
    diagnostic_echo: bool = False
    first_wait_seconds: float = 6.0
    followup_seconds: float = 25.0
    max_turn_seconds: float = 20.0
    preparation_timeout_seconds: float = 60.0
    processing_timeout_seconds: float = 60.0
    retain_seconds: float = 90.0
    speech_start_ms: int = 200
    end_silence_ms: int = 650
    vad_threshold: float = 0.5
    echo_guard_seconds: float = 0.4
    volume: float = 0.75
    output_device: str = "auto"
    cpu_threads: int = 4
    pending_audio_seconds: float = 40.0
    max_session_seconds: float = 600.0

    def validate(self):
        for name, value in asdict(self).items():
            expected = type(getattr(VoiceConfig(), name))
            if (expected is float and type(value) not in (float, int)) or (expected is not float and type(value) is not expected):
                raise ValueError(f"voice.{name}: tipo incorrecto")
        if self.version != 1 or self.engine not in ("moonshine-small", "moonshine-tiny", "whisper-base", "whisper-small"):
            raise ValueError("Versión o motor de voz inválido")
        for field, low, high in [("first_wait_seconds",1,60),("followup_seconds",1,120),
            ("max_turn_seconds",1,60),("preparation_timeout_seconds",5,180),
            ("processing_timeout_seconds",5,180),("retain_seconds",0,600),
            ("speech_start_ms",32,1000),("end_silence_ms",200,2000),
            ("vad_threshold",0.01,0.99),("echo_guard_seconds",0.1,2),
            ("volume",0,1),("cpu_threads",1,8),("pending_audio_seconds",5,90),
            ("max_session_seconds",30,1800)]:
            if not low <= getattr(self,field) <= high:
                raise ValueError(f"voice.{field}: fuera de rango {low}..{high}")
        if not self.voice or not self.output_device:
            raise ValueError("Voz o salida vacía")
        return self


def load_voice(root: Path):
    path = root / "voice.json"
    if not path.exists():
        return VoiceConfig()
    return VoiceConfig(**json.loads(path.read_text(encoding="utf-8"))).validate()


def save_voice(root, config):
    config.validate()
    root.mkdir(parents=True,exist_ok=True)
    path=root/"voice.tmp"
    path.write_text(json.dumps(asdict(config),indent=2),encoding="utf-8")
    path.replace(root/"voice.json")
