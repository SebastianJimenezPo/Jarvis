import numpy as np
import soxr


class Converter:
    """Stateful anti-aliased resampling; input mono float32, output s16le/16 kHz."""
    def __init__(self, rate):
        self.resampler = None if rate == 16000 else soxr.ResampleStream(rate, 16000, 1, dtype="float32", quality="HQ")

    def convert(self, samples):
        mono = np.asarray(samples, dtype=np.float32).reshape(-1)
        if self.resampler:
            mono = self.resampler.resample_chunk(mono)
        return (np.clip(mono, -1, 1) * 32767).astype("<i2").tobytes()
