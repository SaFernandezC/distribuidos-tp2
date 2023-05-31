from common.Connection import Connection
import ujson as json
from .utils import default, join_func_query3
import signal
import logging
import time

class Joiner():
    def __init__(self, input_exchange_1, input_exchange_type_1, input_queue_name_2, output_queue_name,
                primary_key, primary_key_2, select, joiner_function):

        self.side_table = {}
        self.fields_to_select = self._parse_select(select)
        self.key1 = self._parse_key(primary_key)
        self.key2 = self._parse_key(primary_key_2)

        self.connection = Connection()
        self.eof_manager = self.connection.EofProducer(None, output_queue_name, input_queue_name_2)
        self.input_queue1 = self.connection.Subscriber(exchange_name=input_exchange_1, exchange_type=input_exchange_type_1)
        self.input_queue2 = self.connection.Consumer(input_queue_name_2)
        self.output_queue = self.connection.Producer(output_queue_name)

        self.running = True
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        self.joiner_function = joiner_function

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

    def _add_item(self, item):
        values = []
        for _i in self.key1:
            values.append(item[_i])
            del item[_i]
        
        self.side_table[tuple(values)] = item

    def _callback_queue1(self, body):
        batch = json.loads(body.decode())
        if "eof" in batch:
            print(f"{time.asctime(time.localtime())} RECIBO EOF CALLBACK 1 ---> DEJO DE ESCUCHAR, {batch}")
            self.connection.stop_consuming()
        else:
            for item in batch["data"]:
                self._add_item(item)

    def _select(self, row):
        if not self.fields_to_select: return row
        return {key: row[key] for key in self.fields_to_select}

    def _join(self, item):
        function = eval(self.joiner_function)
        return function(self.key2, item, self.side_table)

    def _callback_queue2(self, body):
        batch = json.loads(body.decode())
        if "eof" in batch:
            print(f"{time.asctime(time.localtime())} RECIBO EOF CALLBACK 2 ---> DEJO DE ESCUCHAR, {batch}")
            self.connection.stop_consuming()
            self.eof_manager.send_eof()
        else:
            data = []
            for item in batch["data"]:
                joined, res = self._join(item)

                if joined:
                    data.append(self._select(res))
            self.output_queue.send(json.dumps({"data":data}))

    def run(self):
        self.input_queue1.receive(self._callback_queue1)
        self.connection.start_consuming()

        self.input_queue2.receive(self._callback_queue2)
        self.connection.start_consuming()
        self.connection.close()