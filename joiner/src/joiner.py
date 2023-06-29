from common.Connection import Connection
import ujson as json
from .utils import join_func_default, join_func_query3
import signal
import logging
from common.HeartBeater import HeartBeater
from common.AtomicWrite import atomic_write, load_memory
from hashlib import sha256

MESSAGES_BATCH = 10
CALLBACK_1 = "1"
CALLBACK_2 = "2"

class Joiner():
    def __init__(self, input_exchange_1, input_exchange_type_1, input_queue_name_2, output_queue_name,
                primary_key, primary_key_2, select, joiner_function, node_id):

        self.node_id = node_id
        self.side_table = {}
        self.fields_to_select = self._parse_select(select)
        self.key1 = self._parse_key(primary_key)
        self.key2 = self._parse_key(primary_key_2)

        self.connection = Connection()
        self.eof_manager = self.connection.EofProducer(None, output_queue_name, node_id)
        self.input_queue1 = self.connection.Subscriber(exchange_name=input_exchange_1, exchange_type=input_exchange_type_1, queue_name=node_id)
        self.input_queue2 = self.connection.Consumer(input_queue_name_2)
        self.output_queue = self.connection.Producer(output_queue_name)
        self.hearbeater = HeartBeater(self.connection, node_id)

        self.running = True
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        self.joiner_function = joiner_function

        self.eof_received = []
        self.clean_received = {}

        self.tags_to_ack = [] # [messages]
        self.ids_processed = {}  # {Client_id: [ids]}

        self.get_previous_state()

    def get_previous_state(self):
        previous_state = load_memory("./data.txt")
        self.side_table = previous_state.get('side_table', {})
        self.ids_processed = previous_state.get('ids_processed', {})
        self.eof_received = previous_state.get('eof_received', [])
        self.clean_received = previous_state.get('clean_received', {})

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
            
            self.side_table[client_id][str(tuple(values))] = item

    def add_message_id(self, message_id, client_id):
        if not client_id in self.ids_processed:
            self.ids_processed[client_id] = []

        already_added = message_id in self.ids_processed[client_id]

        if not already_added:
            self.ids_processed[client_id].append(message_id)

    
    def save_memory(self):
        data = {
            "side_table": self.side_table,
            "ids_processed": self.ids_processed,
            "eof_received": self.eof_received,
            "clean_received": self.clean_received,
        }
        atomic_write("./data.txt", json.dumps(data))

    def ack(self, forced):
        if len(self.tags_to_ack) >= MESSAGES_BATCH or forced:
            self.save_memory()
            self.input_queue1.ack(self.tags_to_ack)
            self.tags_to_ack = []
    
    def clean_client(self, client_id, callback_caller):
        cleans_checked = self.clean_received.get(client_id, None)
        if cleans_checked is None:
            self.clean_received.update({client_id: callback_caller})
            if callback_caller == CALLBACK_1:
                self.eof_received.append(client_id)
            self.save_memory()

        elif callback_caller != cleans_checked:
            if client_id in self.eof_received:
                self.eof_received.remove(client_id)
            self.side_table.pop(client_id, None)
            self.ids_processed.pop(client_id, None)
            self.clean_received.pop(client_id)
            self.save_memory()
            print(f"Borro {client_id}")

    def _callback_queue1(self, body, ack_tag):
        message_id = int(sha256(body).hexdigest(), 16)

        batch = json.loads(body.decode())
        client_id = str(batch["client_id"])
        
        duplicated = self.add_message_id(message_id, client_id)
        if duplicated:
            self.input_queue1.ack(ack_tag)
            return
            
        self.tags_to_ack.append(ack_tag)

        if "eof" in batch:
            if client_id not in self.eof_received:
                self.eof_received.append(client_id)
        elif "clean" in batch:
            self.clean_client(client_id, CALLBACK_1)
        else:
            self._add_item(client_id, batch["data"])

        force_ack = "clean" in batch or "eof" in batch
        self.ack(force_ack)

    def _select(self, row):
        if not self.fields_to_select: return row
        return {key: row[key] for key in self.fields_to_select}

    def _join(self, client_id, item):
        if client_id not in self.side_table:
            return False, None
        function = eval(self.joiner_function)
        return function(self.key2, item, self.side_table[client_id])
    
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
            if "clean" in batch:
                self.clean_client(client_id, CALLBACK_2)
        else:
            self.input_queue2.send(body)

        return True

    def _callback_queue2(self, body, ack_tag):
        batch = json.loads(body.decode())
        client_id = str(batch["client_id"])        

        is_clean = "clean" in batch

        if client_id not in self.eof_received and not is_clean:
            self.input_queue2.nack(ack_tag)
            return

        eof = self.handle_eof(body, batch)
        if not eof:
            data = []                
            for item in batch["data"]:
                joined, res = self._join(client_id, item)

                if joined:
                    data.append(self._select(res))

            if len(data) > 0:
                id = ack_tag
                self.output_queue.send(json.dumps({"client_id": client_id, "data": data, "message_id": id}))
                # self.output_queue.send(json.dumps({"client_id": client_id, "data": data, "message_id": id}))
        self.input_queue2.ack(ack_tag)

    def run(self):
        self.hearbeater.start()
        self.input_queue1.receive(self._callback_queue1, prefetch_count=MESSAGES_BATCH)
        self.input_queue2.receive(self._callback_queue2)
        self.connection.start_consuming()
        self.connection.close()