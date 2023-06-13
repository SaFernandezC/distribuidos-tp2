import threading

class AtomicValue:
    def __init__(self, initial_value):
        self.value = initial_value
        self.lock = threading.Lock()

    def set(self, value):
        with self.lock:
            self.value = value

    def get(self):
        with self.lock:
            return self.value