from common.Connection import Connection
import ujson as json
from .utils import send
import signal
import logging

class Parser():
    def __init__(self, input_queue, routing_key, output_exchange, output_exchange_type):
        self.running = True
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        
        self.routing_key = routing_key
        self.connection = Connection()

        self.input_queue = self.connection.Consumer(queue_name=input_queue)
        self.eof_manager = self.connection.EofProducer(output_exchange, output_exchange_type, input_queue)
        self.output_queue = self.connection.Publisher(output_exchange, output_exchange_type)

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
            print("RECIBO EOF -> ENVIO EOF")
        else:
            send(self.output_queue, batch)
    
    def run(self):
        self.input_queue.receive(self._callback)
        self.connection.start_consuming()
        self.connection.close()