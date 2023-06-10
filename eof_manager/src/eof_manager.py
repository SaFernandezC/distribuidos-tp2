import ujson as json
from common.Connection import Connection
import time
import signal
import logging

import copy

INT_LENGTH = 4

class EofManager:

    def __init__(self):

        self.base_exchanges, self.base_work_queues = self._load_config()

        # self.eof_msg = json.dumps({"eof": True})
        self.connection = Connection()
        self.eof_consumer = self.connection.Consumer('eof_manager')
        self.exchange_connections, self.queues_connection = self._declare_queues()

        self.running = True
        signal.signal(signal.SIGTERM, self._handle_sigterm)

        # Hay que persistir todo esto?
        self.active_clients = []
        self.work_queues_per_client = {}
        self.exchanges_per_client = {}


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
            "joiner_1": self.connection.Producer("joiner_1"),
            "groupby_query_1": self.connection.Producer("groupby_query_1"),
            "joiner_2": self.connection.Producer("joiner_2"),
            "groupby_query_2": self.connection.Producer("groupby_query_2"),
            "joiner_3": self.connection.Producer("joiner_3"),
            "distance_calculator": self.connection.Producer("distance_calculator"),
            "groupby_query_3": self.connection.Producer("groupby_query_3"),
            "trip": self.connection.Producer("trip"),
            "weather": self.connection.Producer("weather"),
            "station": self.connection.Producer("station"),
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

    def build_eof_msg(self, client_id):
        return json.dumps({"client_id":client_id, "eof": True})

    def _exchange_with_queues(self, client_id, line):
        exchange = self.exchanges_per_client[client_id][line["exchange"]]
        writing = exchange["writing"]
        exchange["eof_received"] += 1
        queues_binded = exchange["queues_binded"]

        if exchange["eof_received"] == writing:
            for queue_name, queue_data in queues_binded.items():
                listening = queue_data["listening"]
                for i in range(listening):
                    self.queues_connection[queue_name].send(self.build_eof_msg(client_id))
                    # print(f"{time.asctime(time.localtime())} ENVIO EOF A COLA {queue_name} DE EXCHANFE: ", line["exchange"])


    def _exchange_without_queues(self, client_id, line):
        exchange = self.exchanges_per_client[client_id][line["exchange"]]
        writing = exchange["writing"]
        exchange["eof_received"] += 1    
        # print(f"{time.asctime(time.localtime())} Exch sin colas EOF PARCIAL :", exchange["eof_received"])
        if exchange["eof_received"] == writing:
            self.exchange_connections[line["exchange"]].send(self.build_eof_msg(client_id))

    def _queue(self, client_id, line):
        queue = line["queue"]
        writing = self.work_queues_per_client[client_id][queue]["writing"]
        listening = self.work_queues_per_client[client_id][queue]["listening"]

        self.work_queues_per_client[client_id][queue]["eof_received"] += 1

        if self.work_queues_per_client[client_id][queue]["eof_received"] == writing:
            for i in range(listening):
                print(f"{time.asctime(time.localtime())} ENVIO EOF DE {client_id} A: {queue} donde hay {listening} listening")
                self.queues_connection[line["queue"]].send(self.build_eof_msg(client_id))

    def add_new_client(self, client_id):
        logging.info(f"Adding new client: {client_id}")
        self.active_clients.append(client_id)
        self.exchanges_per_client[client_id] = copy.deepcopy(self.base_exchanges)
        self.work_queues_per_client[client_id] = copy.deepcopy(self.base_work_queues)

    def _callback(self, body):
        line = json.loads(body.decode())
        client_id = line["client_id"]

        if client_id not in self.active_clients:
            self.add_new_client(client_id)

        if line["type"] == "exchange":
            if len(self.base_exchanges[line["exchange"]]["queues_binded"]) == 0:
                self._exchange_without_queues(client_id, line)
            else:
                self._exchange_with_queues(client_id, line)

        if line["type"] == "work_queue":
            self._queue(client_id, line)

    def run(self):
        self.eof_consumer.receive(self._callback)
        self.connection.start_consuming()
        self.connection.close()