"""Synthetic acoustic fixtures verify plumbing, NEVER real voice accuracy."""
import json
import struct
import subprocess
import wave
import numpy as np
import pytest
from jarvis.wakeword.rustpotter_adapter import RustpotterDetector, engine_path


@pytest.fixture(scope="module")
def reference(tmp_path_factory):
    if not engine_path().exists():
        pytest.skip("Rust executable has not been built")
    folder = tmp_path_factory.mktemp("referencia sintética")
    paths = []
    for i in range(6):
        t = np.arange(12000) / 16000
        audio = (np.sin(2 * np.pi * (280 * t + 800 * t ** 2)) * np.sin(np.pi * t / 0.75) * 0.4 * 32767).astype("<i2")
        path = folder / f"sample{i}.wav"
        with wave.open(str(path), "wb") as output:
            output.setnchannels(1)
            output.setsampwidth(2)
            output.setframerate(16000)
            output.writeframes(audio.tobytes())
        paths.append(str(path))
    target = folder / "synthetic.rpw"
    result = subprocess.run([str(engine_path()), "calibrate", str(target), *paths], capture_output=True,
                            timeout=30, creationflags=subprocess.CREATE_NO_WINDOW)
    assert result.returncode == 0, result.stderr
    return target, audio.tobytes()


def test_real_rust_transport_silence_noise_and_reference(reference):
    path, audio = reference
    detector = RustpotterDetector(path, 0.5, 0.2)
    try:
        detector.start()
        assert detector.frame_bytes <= 4096
        for _ in range(100):
            assert not detector.process(bytes(detector.frame_bytes))["detected"]
        rng = np.random.default_rng(42)
        for _ in range(100):
            noise = rng.integers(-1000, 1000, detector.frame_bytes // 2, dtype=np.int16).astype("<i2")
            assert not detector.process(noise.tobytes())["detected"]
        hits = []
        pcm = bytes(16000) + audio + bytes(32000)
        for start in range(0, len(pcm) - detector.frame_bytes + 1, detector.frame_bytes):
            result = detector.process(pcm[start:start + detector.frame_bytes])
            if result["detected"]:
                hits.append(result)
        assert hits, "Synthetic exact-reference match should be detected"
        assert isinstance(hits[0]['avg_score'],(int,float))
        assert hits[0]['partial_matches']>=1
        assert isinstance(hits[0]['reference_scores'],dict)
        detector.close()
        detector.start()
        assert not detector.process(bytes(detector.frame_bytes))["detected"]
        process = detector.process_handle
        process.kill()
        process.wait()
        with pytest.raises((OSError, RuntimeError, TimeoutError)):
            detector.process(bytes(detector.frame_bytes))
    finally:
        detector.close()
    assert process.poll() is not None


def test_partial_reads_and_invalid_frame(reference):
    path, _ = reference
    process = subprocess.Popen([str(engine_path()), "detect", str(path), "0.5", "0.2"],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        ready = json.loads(process.stdout.readline())
        packet = struct.pack("<I", ready["frame_bytes"]) + bytes(ready["frame_bytes"])
        for part in [packet[:1], packet[1:3], packet[3:9], packet[9:]]:
            process.stdin.write(part)
            process.stdin.flush()
        assert json.loads(process.stdout.readline())["type"] == "result"
        process.stdin.write(struct.pack("<I", 10000000))
        process.stdin.flush()
        assert json.loads(process.stdout.readline())["type"] == "error"
        assert process.wait(timeout=3) == 1
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        for pipe in (process.stdin, process.stdout, process.stderr):
            pipe.close()
