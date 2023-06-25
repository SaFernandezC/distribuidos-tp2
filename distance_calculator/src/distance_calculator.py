from common.Connection import Connection
import ujson as json
from haversine import haversine
import signal
import logging
from common.HeartBeater import HeartBeater

class DistanceCalculator:

    def __init__(self, input_queue_name, output_queue_name, node_id):

        self.running = True
        signal.signal(signal.SIGTERM, self._handle_sigterm)

        self.connection = Connection()
        self.input_queue = self.connection.Consumer(input_queue_name)
        self.eof_manager = self.connection.EofProducer(None, output_queue_name, node_id)
        self.output_queue = self.connection.Producer(output_queue_name)
        self.hearbeater = HeartBeater(self.connection, node_id)

    def _handle_sigterm(self, *args):
        """
        Handles SIGTERM signal
        """
        logging.info('SIGTERM received - Shutting server down')
        self.connection.close()

    def _callback(self, body, ack_tag):
        batch = json.loads(body.decode())
        client_id = batch["client_id"]
        
        if "eof" in batch:
            self.eof_manager.send_eof(client_id)
        elif "clean" in batch:
            self.eof_manager.send_eof(client_id, msg_type="clean")
        else:
            data = []
            for item in batch["data"]:
                distance = haversine((item['start_latitude'], item['start_longitude']), (item['end_latitude'], item['end_longitude']))
                res = {"end_name": item["end_name"], "distance": distance}
                data.append(res)
            self.output_queue.send(json.dumps({"client_id": client_id, "data": data}))
        self.input_queue.ack(ack_tag)

    def run(self):
        self.hearbeater.start()
        self.input_queue.receive(self._callback)
        self.connection.start_consuming()
        self.connection.close()