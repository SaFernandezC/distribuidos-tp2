import logging
from common.Connection import Connection
import ujson as json

FINISH = 'F'
SEND_DATA = 'D'
SEND_EOF = 'E'
SEND_WEATHERS = 'W'
SEND_STATIONS = 'S'
SEND_TRIPS = 'T'
ASK_DATA = 'A'
INT_LENGTH = 4

class Client:
    def __init__(self, id, client_sock, protocol, results, results_lock):
        self.id = id
        self.client_sock = client_sock
        self.protocol = protocol
        self.results = results
        self.results_lock = results_lock

        self.connection = Connection()
        self.eof_manager = self.connection.EofProducer(None, None, None)
        self.trips_queue = self.connection.Producer(queue_name="trip")
        self.weathers_queue = self.connection.Producer(queue_name="weather")
        self.stations_queue = self.connection.Producer(queue_name="station")

    def recv_data(self, key):
        logging.debug(f'action: receiving data')
        data = self.protocol.recv_data(self.client_sock)
        batch = json.dumps({"client_id": self.id, "data": json.loads(data)})
        if key == "trip":
            self.trips_queue.send(batch)
        elif key == "station":
            self.stations_queue.send(batch)
        else:
            self.weathers_queue.send(batch)
        self.protocol.send_ack(self.client_sock, True)

    def send_eof(self, key):
        self.eof_manager.send_eof(self.id, {"type":"work_queue", "queue": key})

    def recv_eof(self, key): 
        logging.debug(f'action: receiving eof')
        data = self.protocol.recv_data(self.client_sock)
        self.send_eof(key)
        self.protocol.send_ack(self.client_sock, True)

    def ask_for_data(self):
        with self.results_lock:
            print(self.results)
            if not self.id in self.results:
                self.protocol.send_result(self.client_sock, False)
            else:
                self.protocol.send_result(self.client_sock, True, self.results[self.id])

    def run(self):
        while True:
            # if not self.is_alive:
            #     break
            action = self.protocol.recv_action(self.client_sock)
            if action == SEND_DATA:
                key = self.protocol.recv_key(self.client_sock)
                self.recv_data(key)
            elif action == SEND_EOF:
                key = self.protocol.recv_key(self.client_sock)
                self.recv_eof(key)
            elif action == FINISH:
                self.protocol.send_ack(self.client_sock, True)
                break
            elif action == ASK_DATA:
                self.ask_for_data()

