import shutil
import subprocess
import tempfile
import time
import wave
from pathlib import Path
import numpy as np
from jarvis.audio.capture import Capture
from jarvis.audio.converter import Converter
from .rustpotter_adapter import engine_path, RustpotterDetector


def trim_voice(pcm: bytes) -> bytes:
    """Conservative energy trimming for explicit recordings, not continuous VAD."""
    data = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768
    window = 320
    usable = data[:len(data) // window * window].reshape(-1, window)
    energy = np.sqrt(np.mean(usable ** 2, axis=1))
    if not len(energy) or energy.max() < 0.01:
        raise ValueError("Grabación demasiado baja o silenciosa; repite más cerca")
    if np.mean(np.abs(data) >= 0.99) > 0.02:
        raise ValueError("Grabación saturada; reduce la ganancia")
    active = np.flatnonzero(energy >= max(0.008, energy.max() * 0.15))
    start = max(0, int(active[0]) * window - 1600)
    end = min(len(data), (int(active[-1]) + 1) * window + 1600)
    if end - start < 4800:
        raise ValueError("Muestra demasiado corta")
    return pcm[start * 2:end * 2]


def calibrate(config, root, count=6):
    if not engine_path().is_file():
        raise FileNotFoundError("Compila primero el auxiliar Rust")
    print("Se grabarán muestras temporales de Jarvis. Se borran al terminar; queda la referencia acústica local.")
    if input("Escribe GRABAR para autorizar la captura: ").strip() != "GRABAR":
        print("Calibración cancelada.")
        return
    target = config.reference_path(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="jarvis-calibration-") as directory:
        samples = []
        for i in range(count):
            while True:
                input(f"Muestra {i + 1}/{count}: pulsa Enter y di Jarvis una vez durante los próximos 2 segundos.")
                capture = Capture(config.device, 150)
                converter = Converter(capture.rate)
                recording = bytearray()
                try:
                    capture.start()
                    until = time.monotonic() + 2.2
                    while time.monotonic() < until:
                        _, block = capture.blocks.get(timeout=3)
                        recording.extend(converter.convert(block))
                finally:
                    capture.close()
                try:
                    pcm = trim_voice(bytes(recording))
                except ValueError as exc:
                    print(exc)
                    continue
                path = Path(directory) / f"sample-{i}.wav"
                with wave.open(str(path), "wb") as output:
                    output.setnchannels(1)
                    output.setsampwidth(2)
                    output.setframerate(16000)
                    output.writeframes(pcm)
                samples.append(str(path))
                break
        generated = Path(directory) / "jarvis.rpw"
        result = subprocess.run([str(engine_path()), "calibrate", str(generated), *samples],
                                capture_output=True, text=True, timeout=90,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout)
        detector = RustpotterDetector(generated, config.threshold, config.avg_threshold)
        try:
            detector.start()
        finally:
            detector.close()
        # Copy then atomic replace on the same volume; do not destroy a working reference on failure.
        staged = target.with_suffix(".tmp")
        shutil.copyfile(generated, staged)
        staged.replace(target)
    print(f"Referencia guardada: {target}. Prueba detecciones y ajusta los umbrales; aún no está validada su precisión.")
