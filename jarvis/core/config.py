"""Versioned, strict user configuration. Invalid files are never silently replaced."""
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path


def data_dir() -> Path:
    return Path(os.environ.get("LOCALAPPDATA", Path.home())) / "JarvisCore"


@dataclass(frozen=True)
class Config:
    version: int = 1
    listening: bool = True
    device: str = "auto"
    reference: str = "jarvis.rpw"
    threshold: float = 0.5
    avg_threshold: float = 0.2
    cooldown_seconds: float = 3.0
    active_seconds: float = 10.0
    confirmation: bool = True
    log_level: str = "INFO"
    preroll_seconds: float = 1.5
    queue_blocks: int = 25
    retry_initial_seconds: float = 1.0
    retry_max_seconds: float = 30.0
    retry_limit: int = 6

    def validate(self):
        defaults = Config()
        for key, value in asdict(self).items():
            expected = type(getattr(defaults, key))
            if expected is float:
                if type(value) not in (float, int):
                    raise ValueError(f"{key}: se requiere un número")
            elif type(value) is not expected:
                raise ValueError(f"{key}: tipo incorrecto")
        ranges = {"threshold": (0.01, 1), "avg_threshold": (0, 1),
                  "cooldown_seconds": (0, 60), "active_seconds": (1, 300),
                  "preroll_seconds": (0, 5), "queue_blocks": (2, 100),
                  "retry_initial_seconds": (0.5, 60), "retry_max_seconds": (1, 300),
                  "retry_limit": (1, 20)}
        for key, (low, high) in ranges.items():
            if not low <= getattr(self, key) <= high:
                raise ValueError(f"{key}: fuera del rango {low}..{high}")
        if self.version != 1 or self.log_level not in ("DEBUG", "INFO", "WARNING", "ERROR"):
            raise ValueError("Versión o nivel de registro no admitido")
        if not self.device or not self.reference or self.retry_max_seconds < self.retry_initial_seconds:
            raise ValueError("Dispositivo, referencia o política de reintentos inválidos")
        return self

    def reference_path(self, root: Path) -> Path:
        path = Path(self.reference)
        return path if path.is_absolute() else root / "references" / path


def load(root: Path) -> Config:
    root.mkdir(parents=True, exist_ok=True)
    path = root / "config.json"
    if not path.exists():
        save(root, Config())
    return Config(**json.loads(path.read_text(encoding="utf-8"))).validate()


def save(root: Path, config: Config):
    config.validate()
    root.mkdir(parents=True, exist_ok=True)
    temp = root / "config.tmp"
    temp.write_text(json.dumps(asdict(config), indent=2), encoding="utf-8")
    temp.replace(root / "config.json")
