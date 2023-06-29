import threading
import logging

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
    
    def get_lock(self):
        return self.lock

    def get_unsafe_value(self):
        return self.value

    def set_unsafe_value(self, value):
        self.value = value

class Sender:
    def __init__(self, skt, queue):
        self.queue = queue
        self.skt = skt

    def run(self):
        while True:
            try:
                while True:
                    msg = self.queue.get()
                    self.skt.sendto(msg[0].encode(), msg[1])
            except Exception as e:
                logging.error("Sender: error sending message | error: {}".format(e))

class Receiver:
    def __init__(self, skt, queue):
        self.queue = queue
        self.skt = skt

    def run(self):
        try:
            while True:
                pair = self.skt.recvfrom(1024)
                self.queue.put(pair)
        except Exception as e:
            logging.error("Sender: error receiving message | error: {}".format(e))