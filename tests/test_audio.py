import numpy as np
import pytest
from jarvis.audio.buffers import RingBuffer, AudioQueue
from jarvis.audio.converter import Converter
from jarvis.wakeword.calibration import trim_voice


def test_ring_and_queue_boundaries():
    ring = RingBuffer(10)
    ring.append(b"12345678")
    ring.append(b"abcdefgh")
    assert ring.snapshot() == b"78abcdefgh"
    ring.clear()
    assert ring.snapshot() == b""
    disabled = RingBuffer(0)
    disabled.append(b"abc")
    assert disabled.snapshot() == b""
    queue = AudioQueue(2)
    for i in range(1000):
        queue.put(i)
    assert queue.dropped == 998 and queue.peak == 2
    assert queue.get() == 0


@pytest.mark.parametrize("rate", [16000, 44100, 48000])
def test_streaming_conversion(rate):
    samples = (0.4 * np.sin(2 * np.pi * 440 * np.arange(rate * 2) / rate)).astype(np.float32)
    converter = Converter(rate)
    pcm = b"".join(converter.convert(chunk) for chunk in np.array_split(samples, 100))
    output = np.frombuffer(pcm, dtype="<i2")
    assert 30000 < len(output) <= 32000
    assert 12000 < np.max(output) < 14000
    peak = np.argmax(abs(np.fft.rfft(output))) * 16000 / len(output)
    assert abs(peak - 440) < 2


def test_conversion_clamps_and_silence_rejected():
    pcm = Converter(16000).convert(np.array([-2, 2], dtype=np.float32))
    assert np.frombuffer(pcm, dtype="<i2").tolist() == [-32767, 32767]
    with pytest.raises(ValueError, match="silenciosa"):
        trim_voice(bytes(64000))
