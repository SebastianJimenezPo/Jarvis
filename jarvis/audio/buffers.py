from collections import deque
from queue import Queue, Full, Empty


class AudioQueue:
    def __init__(self, capacity):
        self.queue = Queue(capacity)
        self.dropped = self.peak = 0

    def put(self, block):
        try:
            self.queue.put_nowait(block)
        except Full:
            self.dropped += 1
            return
        self.peak = max(self.peak, self.queue.qsize())

    def get(self, timeout=0.2):
        return self.queue.get(timeout=timeout)


class RingBuffer:
    def __init__(self, max_bytes):
        self.capacity = max_bytes
        self.data = bytearray()

    def append(self, block: bytes):
        if self.capacity:
            self.data.extend(block)
            excess = len(self.data) - self.capacity
            if excess > 0:
                del self.data[:excess]

    def snapshot(self) -> bytes:
        return bytes(self.data)

    def clear(self):
        self.data.clear()
