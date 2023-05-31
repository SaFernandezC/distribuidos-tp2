class Asker():
    def __init__(self, connection, metrics_queue, results_queue):
        self.connection = connection
        self.metrics_queue = metrics_queue
        self.results_queue = results_queue

    def run(self):
        self.metrics_queue.receive(self._callback)
        self.connection.start_consuming()
        self.connection.close()

    def _callback(self, body):
        data = body.decode()
        self.results_queue.put(data)
        self.connection.stop_consuming()