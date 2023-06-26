from common.Connection import Connection
import ujson as json
from .utils import send
import signal
import logging
from common.HeartBeater import HeartBeater

INT_LENGTH = 4

class Parser():
    def __init__(self, input_queue, routing_key, output_exchange, output_exchange_type, node_id):
        self.running = True
        signal.signal(signal.SIGTERM, self._handle_sigterm)

        self.routing_key = routing_key
        self.connection = Connection()

        self.input_queue = self.connection.Consumer(queue_name=input_queue)
        self.eof_manager = self.connection.EofProducer(output_exchange, output_exchange_type, node_id)
        self.output_queue = self.connection.Publisher(output_exchange, output_exchange_type)
        self.hearbeater = HeartBeater(self.connection, node_id)
        self.node_id = node_id

    def _handle_sigterm(self, *args):
        """
        Handles SIGTERM signal
        """
        logging.info('SIGTERM received - Shutting server down')
        self.connection.close()

    def handle_eof(self, body, batch):
        client_id = batch["client_id"]
        if "eof" in batch:
            msg_type = "eof"
        elif "clean" in batch:
            msg_type = "clean"
        else:
            return False
            
        if batch["dst"] == self.node_id:
            self.eof_manager.send_eof(client_id, msg_type=msg_type)
        else:
            self.input_queue.send(body)
        
        return True

    def _callback(self, body, ack_tag):
        batch = json.loads(body.decode())
        eof = self.handle_eof(body, batch)
            
        if not eof:
            client_id = batch["client_id"]
            send(self.output_queue, batch["data"], client_id)
        self.input_queue.ack(ack_tag)
    
    def run(self):
        self.hearbeater.start()
        self.input_queue.receive(self._callback)
        self.connection.start_consuming()
        self.connection.close()