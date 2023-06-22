from common.Connection import Connection
import ujson as json

class Asker():
    def __init__(self, results, results_lock):
        self.connection = Connection()
        self.metrics_queue = self.connection.Consumer(queue_name='metrics')

        self.results = results
        self.results_lock = results_lock
        self.stopped = False

    def run(self):
        self.metrics_queue.receive(self._callback)
        self.connection.start_consuming()
        # if not self.stopped:
        #     self.stop()

    def _callback(self, body, ack_tag):
        body = json.loads(body.decode())
        print(body)
        with self.results_lock:
            self.results[body["client_id"]] = body["data"]
            
        self.metrics_queue.ack(ack_tag)
def stop(self):
        self.connection.stop_consuming()
        self.connection.close()
        self.stopped = True