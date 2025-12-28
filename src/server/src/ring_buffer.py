import threading


class RingBuffer:
    def __init__(self, max_size):
        self.max_size = int(max_size)
        self.buffer = []
        # index points to the next write position when buffer is full
        self.index = 0
        self.lock = threading.Lock()

    def add(self, item):
        """Add an item to the ring buffer in a thread-safe way."""
        with self.lock:
            if len(self.buffer) < self.max_size:
                self.buffer.append(item)
                # keep index pointing to next write location
                self.index = len(self.buffer) % self.max_size
            else:
                self.buffer[self.index] = item
                self.index = (self.index + 1) % self.max_size

    def get_all(self):
        """Return a snapshot list of items ordered oldest->newest."""
        with self.lock:
            if not self.buffer:
                return []
            # If buffer not yet full, items are in insertion order
            if len(self.buffer) < self.max_size:
                return list(self.buffer)
            # When full, index points to the oldest item
            return list(self.buffer[self.index:] + self.buffer[:self.index])

    def latest(self, n=1):
        """Return the latest `n` items (oldest->newest order for the returned slice).

        This method avoids calling `get_all()` inside the same lock to prevent
        deadlocks by performing the same snapshot logic while holding the lock.
        """
        with self.lock:
            if not self.buffer:
                return []
            if n <= 0:
                return []
            # produce ordered list oldest->newest
            if len(self.buffer) < self.max_size:
                items = list(self.buffer)
            else:
                items = list(self.buffer[self.index:] + self.buffer[:self.index])
            return items[-n:]