import ujson as json
from common.Connection import Connection
import time
import signal
import logging
from hashlib import sha256
from common.HeartBeater import HeartBeater
import copy
from common.AtomicWrite import atomic_write, load_memory
import random

EOF_TYPE = "eof_received"
CLEAN_TYPE = "clean_received"
INT_LENGTH = 4

class EofManager:

    def __init__(self, node_id):

        self.base_exchanges, self.base_work_queues = self._load_config()

        # self.eof_msg = json.dumps({"eof": True})
        self.connection = Connection()
        self.eof_consumer = self.connection.Consumer('eof_manager')
        self.exchange_connections, self.queues_connection = self._declare_queues()
        self.hearbeater = HeartBeater(self.connection, node_id)

        self.running = True
        signal.signal(signal.SIGTERM, self._handle_sigterm)

        self.get_previous_state()

    def get_previous_state(self):
        previous_state = load_memory("./data.txt")
        self.work_queues_per_client = previous_state.get('work_queues_per_client', {})
        self.exchanges_per_client = previous_state.get('exchanges_per_client', {})
        self.active_clients = previous_state.get('active_clients', [])
        self.ids_processed = previous_state.get('ids_processed', {})

    def _handle_sigterm(self, *args):
        """
        Handles SIGTERM signal
        """
        logging.info('SIGTERM received - Shutting server down')
        self.connection.close()

    def _declare_queues(self):
        exchanges = {
            "joiner_query_1": self.connection.Publisher("joiner_query_1", 'fanout'),
            "joiner_query_2": self.connection.Publisher("joiner_query_2", 'fanout'),
            "joiner_query_3": self.connection.Publisher("joiner_query_3", 'fanout'),
        }

        queues = {
            "prectot_filter": self.connection.Producer("prectot_filter"),
            "filter_trips_query1": self.connection.Producer("filter_trips_query1"),
            "filter_trips_year": self.connection.Producer("filter_trips_year"),
            "filter_trips_query3": self.connection.Producer("filter_trips_query3"),
            "filter_stations_query2": self.connection.Producer("filter_stations_query2"),
            "filter_stations_query3": self.connection.Producer("filter_stations_query3"),
            "date_modifier": self.connection.Producer("date_modifier"),
            "joiner_query_1": self.connection.Producer("joiner_query_1"),
            "groupby_query_1": self.connection.Producer("groupby_query_1"),
            "joiner_query_2": self.connection.Producer("joiner_query_2"),
            "groupby_query_2": self.connection.Producer("groupby_query_2"),
            "joiner_query_3": self.connection.Producer("joiner_query_3"),
            "distance_calculator": self.connection.Producer("distance_calculator"),
            "groupby_query_3": self.connection.Producer("groupby_query_3"),
            "trip_parser": self.connection.Producer("trip"),
            "weather_parser": self.connection.Producer("weather"),
            "station_parser": self.connection.Producer("station"),
        }
        return exchanges, queues

    def _load_config(self):
        with open("exchanges.json", "r") as file:
            exchanges = json.loads(file.read())
            file.close()
        with open("queues.json", "r") as file:
            work_queues = json.loads(file.read())
            file.close()
        return exchanges, work_queues

    def build_eof_msg(self, client_id, message_type, dst=None):
        if message_type == EOF_TYPE:
            return json.dumps({"client_id":client_id, "eof": True, "dst": dst})
        elif message_type == CLEAN_TYPE:
            return json.dumps({"client_id":client_id, "clean": True, "dst": dst})

    def _exchange_with_queues(self, client_id, line, message_type):
        exchange = self.exchanges_per_client[client_id][line["exchange"]]
        writing = exchange["writing"]
        exchange[message_type] += 1
        queues_binded = exchange["queues_binded"]

        if exchange[message_type] == writing:
            for queue_name, queue_data in queues_binded.items():
                listening = queue_data["listening"]
                for i in range(listening):
                    dest_key = f"{queue_name}_{i+1}"
                    self.queues_connection[queue_name].send(self.build_eof_msg(client_id, message_type, dest_key))

    def _exchange_without_queues(self, client_id, line, message_type):
        exchange = self.exchanges_per_client[client_id][line["exchange"]]
        writing = exchange["writing"]
        exchange[message_type] += 1    
        if exchange[message_type] == writing:
            exchange = line["exchange"]
            self.exchange_connections[line["exchange"]].send(self.build_eof_msg(client_id, message_type))

    def _queue(self, client_id, line, message_type):
        queue = line["queue"]
        writing = self.work_queues_per_client[client_id][queue]["writing"]
        listening = self.work_queues_per_client[client_id][queue]["listening"]

        self.work_queues_per_client[client_id][queue][message_type] += 1

        if self.work_queues_per_client[client_id][queue][message_type] == writing:
            for i in range(listening):
                dest_key = f"{queue}_{i+1}"
                self.queues_connection[queue].send(self.build_eof_msg(client_id, message_type, dest_key))
            
            # if queue.find("groupby") > 0:
            #     self.groupby_sent[client_id] += 1


    def process_eof(self, line, client_id):
        if "eof" in line:
            message_type = EOF_TYPE
        elif "clean" in line:
            message_type = CLEAN_TYPE
        else:
            return

        if line["type"] == "exchange":
            if len(self.base_exchanges[line["exchange"]]["queues_binded"]) == 0:
                self._exchange_without_queues(client_id, line, message_type)
            else:
                self._exchange_with_queues(client_id, line, message_type)

        if line["type"] == "work_queue":
            self._queue(client_id, line, message_type)


    def add_new_client(self, client_id):
        # logging.info(f"Adding new client: {client_id}")
        self.active_clients.append(client_id)
        self.exchanges_per_client[client_id] = copy.deepcopy(self.base_exchanges)
        self.work_queues_per_client[client_id] = copy.deepcopy(self.base_work_queues)


    def add_message_id(self, message_id, client_id):
        if not client_id in self.ids_processed:
            self.ids_processed[client_id] = []

        already_added = message_id in self.ids_processed[client_id]

        if not already_added:
            self.ids_processed[client_id].append(message_id)

        return already_added

    def save_memory(self):
        data = {
            "work_queues_per_client": self.work_queues_per_client,
            "exchanges_per_client": self.exchanges_per_client,
            "active_clients": self.active_clients,
            "ids_processed": self.ids_processed
        }
        atomic_write("./data.txt", json.dumps(data))


    def _callback(self, body, ack_tag):
        message_id = int(sha256(body).hexdigest(), 16)

        line = json.loads(body.decode())
        client_id = str(line["client_id"])

        if client_id not in self.active_clients:
            self.add_new_client(client_id)
        
        duplicated = self.add_message_id(message_id, client_id)
        if duplicated:
            self.eof_consumer.ack(ack_tag)
            return

        self.process_eof(line, client_id)
        self.save_memory()
        self.eof_consumer.ack(ack_tag)

    def run(self):
        self.hearbeater.start()
        self.eof_consumer.receive(self._callback)
        self.connection.start_consuming()
        self.connection.close()