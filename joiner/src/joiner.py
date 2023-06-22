from common.Connection import Connection
import ujson as json
from .utils import default, join_func_query3
import signal
import logging
import time
from common.utils import get_docker_id
from common.HeartBeater import HeartBeater


class Joiner():
    def __init__(self, input_exchange_1, input_exchange_type_1, input_queue_name_2, output_queue_name,
                primary_key, primary_key_2, select, joiner_function, node_id):

        self.side_table = {}
        self.fields_to_select = self._parse_select(select)
        self.key1 = self._parse_key(primary_key)
        self.key2 = self._parse_key(primary_key_2)

        self.docker_id = get_docker_id()

        self.connection = Connection()
        self.eof_manager = self.connection.EofProducer(None, output_queue_name, input_queue_name_2)
        self.input_queue1 = self.connection.Subscriber(exchange_name=input_exchange_1, exchange_type=input_exchange_type_1, queue_name=self.docker_id)
        self.input_queue2 = self.connection.Consumer(input_queue_name_2)
        self.output_queue = self.connection.Producer(output_queue_name)
        self.hearbeater = HeartBeater(self.connection, node_id)

        self.running = True
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        self.joiner_function = joiner_function

        self.eof_received = []

    def _handle_sigterm(self, *args):
        """
        Handles SIGTERM signal
        """
        logging.info('SIGTERM received - Shutting server down')
        self.connection.close()

    def _parse_key(self, key):
        splitted = key.split(',')
        return tuple(splitted)

    def _parse_select(self, select):
        if select:
            return select.split(',')
        else: return None

    def _add_item(self, client_id, data):
        if client_id not in self.side_table:
            self.side_table[client_id] = {}

        for item in data:
            values = []
            for _i in self.key1:
                values.append(item[_i])
                del item[_i]

            self.side_table[client_id][tuple(values)] = item

    def _callback_queue1(self, body, ack_tag):
        batch = json.loads(body.decode())
        client_id = batch["client_id"]
        print(f"Callback 1: {client_id} -> {batch.keys()}")
        # print(f"cliente: {client_id} -> {batch}")
        if "eof" in batch:
            # Problema de perdida de mensajes si no hay nadie escuchando ahi (solucionado con colas durables y persistente)
            print(f"Eof de {client_id}")
            if client_id not in self.eof_received:
                self.eof_received.append(client_id)
        else:
            self._add_item(client_id, batch["data"])

        self.input_queue1.ack(ack_tag)

    def _select(self, row):
        if not self.fields_to_select: return row
        return {key: row[key] for key in self.fields_to_select}

    def _join(self, client_id, item):
        function = eval(self.joiner_function)
        return function(self.key2, item, self.side_table[client_id])

    def _callback_queue2(self, body, ack_tag):
        batch = json.loads(body.decode())
        client_id = batch["client_id"]

        if client_id not in self.eof_received:
            self.input_queue2.nack(ack_tag)
            return

        if "eof" in batch:
            print(f"{time.asctime(time.localtime())} RECIBO EOF CALLBACK 2 ---> DEJO DE ESCUCHAR, {batch}")
            # self.connection.stop_consuming()
            self.eof_manager.send_eof(client_id)
        else:
            data = []
            for item in batch["data"]:
                joined, res = self._join(client_id, item)

                if joined:
                    data.append(self._select(res))
            self.output_queue.send(json.dumps({"client_id": client_id, "data": data}))

        self.input_queue2.ack(ack_tag)

    def run(self):
        self.hearbeater.start()
        self.input_queue1.receive(self._callback_queue1)
        self.input_queue2.receive(self._callback_queue2)
        self.connection.start_consuming()
        self.connection.close()