from common.Connection import Connection
from common.HeartBeater import HeartBeater
import ujson as json

class CleanSender():
    def __init__(self, node_id):
        self.connection = Connection()
        self.eof_manager = self.connection.EofProducer(None, None, node_id)

    def send_clean(self, client_id):
        for key in ['trip', 'station', 'weather']:
            self.eof_manager.send_eof(client_id, {"type":"work_queue", "queue": key}, msg_type="clean")

class SharedInteger():
    def __init__(self, initial_value):
        self.value = initial_value
    
    def increment(self):
        self.value += 1
    
    def get(self):
        return self.value

class Asker():
    def __init__(self, results, results_lock, node_id):
        self.connection = Connection()
        self.metrics_queue = self.connection.Consumer(queue_name='metrics')

        self.results = results
        self.results_lock = results_lock
        self.stopped = False
        self.heartbeater = HeartBeater(self.connection, node_id)

    def run(self):
        self.metrics_queue.receive(self._callback)
        self.heartbeater.start()
        self.connection.start_consuming()

    def _callback(self, body, ack_tag):
        body = json.loads(body.decode())
        with self.results_lock:
            self.results[body["client_id"]] = body["data"]
            
        self.metrics_queue.ack(ack_tag)

    def stop(self):
        self.connection.stop_consuming()
        self.connection.close()
        self.stopped = True