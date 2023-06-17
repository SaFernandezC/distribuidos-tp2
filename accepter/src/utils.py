class Asker():
    def __init__(self, connection, metrics_queue, results_queue):
        self.connection = connection
        self.metrics_queue = metrics_queue
        self.results_queue = results_queue
        self.stopped = False

    def run(self):
        self.metrics_queue.receive(self._callback)
        if not self.stopped:
            self.stop()

    def _callback(self, body, ack_tag):
        data = body.decode()
        self.results_queue.put(data)
        self.connection.stop_consuming()
        self.metrics_queue.ack(ack_tag)
    
    def stop(self):
        self.connection.stop_consuming()
        self.connection.close()
        self.stopped = True