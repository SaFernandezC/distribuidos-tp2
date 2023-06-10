from common.Connection import Connection
import ujson as json
import signal
import logging

class StatusController:

    def __init__(self, input_queue_name, output_queue_name, qty_of_queries):
        self.running = True
        signal.signal(signal.SIGTERM, self._handle_sigterm)

        self.data = {}
        self.qty_of_queries = qty_of_queries

        self.connection = Connection()

        self.input_queue = self.connection.Consumer(input_queue_name)
        self.output_queue = self.connection.Producer(output_queue_name)

    def _handle_sigterm(self, *args):
        """
        Handles SIGTERM signal
        """
        logging.info('SIGTERM received - Shutting server down')
        self.connection.close()
        
    def _callback(self, body):
        line = json.loads(body.decode())
        client_id = line["client_id"]
        
        if client_id not in self.data:
            self.data[client_id] = {}

        self.data[client_id][line["query"]] = line["results"]
        # print(line)

        if len(self.data[client_id]) == self.qty_of_queries:
            self.output_queue.send(json.dumps(self.data))
            print(f"Resultado de cliente {client_id}: ", self.data)
    
    def run(self):
        self.input_queue.receive(self._callback)
        self.connection.start_consuming()
        self.connection.close()
