from common.Connection import Connection
import ujson as json
import signal
import logging
from common.HeartBeater import HeartBeater
from common.AtomicWrite import atomic_write, load_memory
from hashlib import sha256
import random
import time

class StatusController:

    def __init__(self, input_queue_name, output_queue_name, qty_of_queries, node_id):
        signal.signal(signal.SIGTERM, self._handle_sigterm)

        self.qty_of_queries = qty_of_queries

        self.connection = Connection()

        self.input_queue = self.connection.Consumer(input_queue_name)
        self.output_queue = self.connection.Producer(output_queue_name)
        self.hearbeater = HeartBeater(self.connection, node_id)

        self.get_previous_state()

    def get_previous_state(self):
        previous_state = load_memory("./data.txt")
        self.data = previous_state.get('data', {})

    def _handle_sigterm(self, *args):
        """
        Handles SIGTERM signal
        """
        logging.info('SIGTERM received - Shutting server down')
        self.connection.close()

    def caer(self, location):
        num = random.random()
        if num <= 0.25:
            print(f"ME CAIGO EN {location} At {time.time()}")
            resultado = 1/0
        
    def _callback(self, body, ack_tag):        
        line = json.loads(body.decode())
        client_id = str(line["client_id"])
        
        if client_id not in self.data:
            self.data[client_id] = {}

        self.data[client_id][line["query"]] = line["results"]

        if len(self.data[client_id]) == self.qty_of_queries:
            data_to_send = {"client_id": client_id, "data": self.data[client_id]}
            self.output_queue.send(json.dumps(data_to_send))
            # print(f"Resultado de cliente {client_id}: ", self.data[client_id])

        data = {
            "data": self.data,
        }
        atomic_write("./data.txt", json.dumps(data))
        self.caer("a")
        self.input_queue.ack(ack_tag)

    def run(self):
        self.hearbeater.start()
        self.input_queue.receive(self._callback)
        self.connection.start_consuming()
        self.connection.close()
