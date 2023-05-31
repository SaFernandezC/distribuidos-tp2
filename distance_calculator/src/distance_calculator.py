from common.Connection import Connection
import ujson as json
from haversine import haversine
import signal
import logging

class DistanceCalculator:

    def __init__(self, input_queue_name, output_queue_name):

        self.running = True
        signal.signal(signal.SIGTERM, self._handle_sigterm)

        self.connection = Connection()
        self.input_queue = self.connection.Consumer(input_queue_name)
        self.eof_manager = self.connection.EofProducer(None, output_queue_name, input_queue_name)
        self.output_queue = self.connection.Producer(output_queue_name)
    
    def _handle_sigterm(self, *args):
        """
        Handles SIGTERM signal
        """
        logging.info('SIGTERM received - Shutting server down')
        self.connection.close()

    def _callback(self, body):
        batch = json.loads(body.decode())
        if "eof" in batch:
            self.connection.stop_consuming()
            self.eof_manager.send_eof()
        else:
            data = []
            for item in batch["data"]:
                distance = haversine((item['start_latitude'], item['start_longitude']), (item['end_latitude'], item['end_longitude']))
                res = {"end_name": item["end_name"], "distance": distance}
                data.append(res)
            self.output_queue.send(json.dumps({"data":data}))

    
    def run(self):
        self.input_queue.receive(self._callback)
        self.connection.start_consuming()
        self.connection.close()