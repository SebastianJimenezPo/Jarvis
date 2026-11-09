import time
import sounddevice as sd
from .buffers import AudioQueue


def devices(refresh=False):
    # Call only when no capture exists. PortAudio caches its Windows device inventory.
    if refresh:
        sd._terminate()
        sd._initialize()
    hosts = sd.query_hostapis()
    return [{"index": i, "name": d["name"], "rate": d["default_samplerate"],
             "host": hosts[d["hostapi"]]["name"]}
            for i, d in enumerate(sd.query_devices()) if d["max_input_channels"] > 0]


def select_device(preference):
    available = devices(refresh=True)
    wasapi = [d for d in available if d["host"] == "Windows WASAPI"]
    if preference == "auto":
        hosts = sd.query_hostapis()
        host = next((h for h in hosts if h["name"] == "Windows WASAPI"), None)
        index = host["default_input_device"] if host else sd.default.device[0]
        return next(d for d in available if d["index"] == index)
    matches = [d for d in wasapi if d["name"] == preference]
    if len(matches) != 1:
        raise RuntimeError(f"Micrófono fijo ausente o ambiguo: {preference}")
    return matches[0]


class Capture:
    def __init__(self, preference, capacity):
        self.device = select_device(preference)
        self.rate = int(self.device["rate"])
        self.blocks = AudioQueue(capacity)
        self.last_audio = time.monotonic()
        self.overflows = 0
        self.stream = None

    def _callback(self, data, frames, timing, status):
        if status:
            self.overflows += 1
        self.last_audio = time.monotonic()
        self.blocks.put((self.last_audio, data.copy()))

    def start(self):
        self.stream = sd.InputStream(device=self.device["index"], channels=1, dtype="float32",
                                     samplerate=self.rate, blocksize=round(self.rate * 0.02),
                                     callback=self._callback)
        self.stream.start()

    def close(self):
        if self.stream is not None:
            try:
                self.stream.abort()
            finally:
                self.stream.close()
                self.stream = None
