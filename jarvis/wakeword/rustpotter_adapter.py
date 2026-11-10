import json
import queue
import struct
import subprocess
import threading
from pathlib import Path
from jarvis.system.process_job import ProcessJob


def engine_path() -> Path:
    return Path(__file__).resolve().parents[2] / "rust" / "target" / "release" / "jarvis-wakeword.exe"


class RustpotterDetector:
    """One frame in flight: bounded transport, per-frame acknowledgement watchdog."""
    def __init__(self, reference, threshold, avg_threshold, executable=None):
        self.command = [str(executable or engine_path()), "detect", str(reference), str(threshold), str(avg_threshold)]
        self.process_handle = None
        self.reader = None
        self.job = None
        self.responses = queue.Queue(maxsize=4)
        self.frame_bytes = 0

    def _read(self):
        try:
            while True:
                line = self.process_handle.stdout.readline(4097)
                if not line:
                    raise RuntimeError("Detector cerrado inesperadamente")
                if len(line) > 4096:
                    raise RuntimeError("Respuesta del detector excede el límite")
                self.responses.put_nowait(json.loads(line))
        except Exception as exc:
            try:
                self.responses.put_nowait(exc)
            except queue.Full:
                return

    def _response(self, timeout=2):
        try:
            value = self.responses.get(timeout=timeout)
        except queue.Empty as exc:
            raise TimeoutError("Detector no responde") from exc
        if isinstance(value, Exception):
            raise value
        if value.get("type") == "error":
            raise RuntimeError(value.get("message"))
        return value

    def start(self):
        # A previous reader reports EOF on orderly close. Never reuse that response.
        self.responses = queue.Queue(maxsize=4)
        self.process_handle = subprocess.Popen(self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                              stderr=subprocess.DEVNULL, bufsize=0,
                                              creationflags=subprocess.CREATE_NO_WINDOW)
        self.job = ProcessJob(self.process_handle)
        self.reader = threading.Thread(target=self._read, name="detector-output")
        self.reader.start()
        ready = self._response(15)
        if (ready.get("type") != "ready" or ready.get("protocol") != 1 or
                ready.get("sample_rate") != 16000 or ready.get("encoding") != "s16le"):
            raise RuntimeError("Protocolo incompatible")
        self.frame_bytes = ready["frame_bytes"]
        if type(self.frame_bytes) is not int or not 2 <= self.frame_bytes <= 2048 or self.frame_bytes % 2:
            raise RuntimeError("Tamaño de trama inválido")

    def process(self, pcm: bytes) -> dict:
        if len(pcm) != self.frame_bytes:
            raise ValueError("Trama de audio incompleta")
        packet = struct.pack("<I", len(pcm)) + pcm
        # <=2052 bytes and one outstanding frame, below the 4096-byte Windows pipe capacity.
        view = memoryview(packet)
        while view:
            written = self.process_handle.stdin.write(view)
            if not written:
                raise BrokenPipeError("No se pudo enviar audio")
            view = view[written:]
        result = self._response()
        if result.get("type") != "result":
            raise RuntimeError("Respuesta de trama inválida")
        return result

    def close(self):
        process = self.process_handle
        if process is None:
            return
        if process.poll() is None:
            try:
                process.stdin.close()
                process.wait(timeout=1)
            except (OSError, subprocess.TimeoutExpired):
                process.kill()
                process.wait(timeout=3)
        if self.reader:
            self.reader.join(timeout=3)
        for stream in (process.stdin, process.stdout):
            if stream and not stream.closed:
                stream.close()
        self.process_handle = None
        if self.job:
            self.job.close()
            self.job = None
