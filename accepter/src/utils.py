from common.Connection import Connection
from common.HeartBeater import HeartBeater
import ujson as json

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