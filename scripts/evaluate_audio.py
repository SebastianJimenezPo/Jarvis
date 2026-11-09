"""Offline PCM WAV evaluation. Only explicitly supplied files are read; no recording."""
import argparse
import json
import sys
import time
import wave
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from jarvis.audio.converter import Converter
from jarvis.core.config import load, data_dir
from jarvis.wakeword.rustpotter_adapter import RustpotterDetector


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wav", type=Path)
    parser.add_argument("--data-dir", type=Path, default=data_dir())
    parser.add_argument("--expected-end", type=float, nargs="*", default=None,
                        help="Fin de cada palabra esperada, en segundos del archivo")
    args = parser.parse_args()
    config = load(args.data_dir)
    with wave.open(str(args.wav), "rb") as source:
        if source.getsampwidth() != 2 or source.getcomptype() != "NONE":
            parser.error("Se requiere WAV PCM signed 16-bit")
        rate, channels = source.getframerate(), source.getnchannels()
        samples = np.frombuffer(source.readframes(source.getnframes()), dtype="<i2")
    mono = samples.reshape(-1, channels).astype(np.float32).mean(axis=1) / 32768
    converter = Converter(rate)
    # Padding flushes streaming filter delay and permits trailing detection finalization.
    pcm = converter.convert(np.concatenate([mono, np.zeros(rate, dtype=np.float32)]))
    detector = RustpotterDetector(config.reference_path(args.data_dir), config.threshold, config.avg_threshold)
    detections = []
    start = time.perf_counter()
    try:
        detector.start()
        size = detector.frame_bytes
        for offset in range(0, len(pcm) - size + 1, size):
            response = detector.process(pcm[offset:offset + size])
            if response["detected"]:
                detections.append({"audio_seconds": (offset + size) / 32000, "score": response.get("score")})
    finally:
        detector.close()
    expected = args.expected_end
    latencies, matched = [], set()
    if expected is not None:
        for end in expected:
            candidate = next((i for i, d in enumerate(detections)
                              if i not in matched and -0.3 <= d["audio_seconds"] - end <= 1.5), None)
            if candidate is not None:
                matched.add(candidate)
                latencies.append(detections[candidate]["audio_seconds"] - end)
    print(json.dumps({"detections": detections, "processing_wall_seconds": time.perf_counter() - start,
                      "input_seconds": len(mono) / rate, "hits": len(matched) if expected is not None else None,
                      "misses": len(expected) - len(matched) if expected is not None else None,
                      "false_activations": len(detections) - len(matched) if expected is not None else None,
                      "latency_seconds_relative_to_annotated_word_end": latencies if expected is not None else None,
                      "note": "Offline, includes streaming filter delay; does not measure microphone or UI latency."}, indent=2))


if __name__ == "__main__":
    main()
