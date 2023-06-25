import logging
from common.Connection import Connection
import ujson as json
from common.AtomicWrite import atomic_write, load_memory

FINISH = 'F'
SEND_DATA = 'D'
SEND_EOF = 'E'
SEND_WEATHERS = 'W'
SEND_STATIONS = 'S'
SEND_TRIPS = 'T'
ASK_DATA = 'A'
INT_LENGTH = 4

SENDING = "sending"
WAITING = "waiting"
FINISH = "finish"

class Client:
    def __init__(self, client_sock, protocol, results, shared_lock, clients_state, id_counter):
        self.id = None
        self.client_sock = client_sock
        self.protocol = protocol
        self.results = results
        self.shared_lock = shared_lock
        self.clients_state = clients_state
        self.id_counter = id_counter

        self.connection = Connection()
        self.eof_manager = self.connection.EofProducer(None, None, "Accepter")
        self.trips_queue = self.connection.Producer(queue_name="trip")
        self.weathers_queue = self.connection.Producer(queue_name="weather")
        self.stations_queue = self.connection.Producer(queue_name="station")

        self.check_status()

    def check_status(self):
        status_recv = self.protocol.recv_status(self.client_sock)
        with self.shared_lock:
            recv_id = status_recv["id"]
            status = status_recv["status"]
            prev_state = None
            if recv_id is not None:
                prev_state = self.clients_state.get(recv_id)

            if recv_id == None and status == SENDING:
                self.id = self.id_counter
                self.id_counter += 1
                error = False
            elif recv_id == None and status != SENDING:
                error = True
            elif recv_id is not None and recv_id not in self.clients_state:
                error = True
            elif status == FINISH and prev_state == SENDING:
                error = True

            if error:
                self.id = self.id_counter
                self.id_counter += 1

            self.save_memory()
        status_send = {"id": self.id, "error": error}
        self.protocol.send_status(self.client_sock, status_send)

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
    
    def send_clean(self):
        for key in ['trip', 'station', 'weather']:
            self.eof_manager.send_eof(self.id, {"type":"work_queue", "queue": key}, msg_type="clean")

    def recv_eof(self, key): 
        logging.debug(f'action: receiving eof')
        data = self.protocol.recv_data(self.client_sock)
        self.send_eof(key)
        self.protocol.send_ack(self.client_sock, True)

    def ask_for_data(self):
        # Aca
        with self.shared_lock:
            if self.clients_state[self.id] != WAITING:
                self.clients_state[self.id] = WAITING
                self.save_memory()
            if not self.id in self.results:
                self.protocol.send_result(self.client_sock, False)
            else:
                self.protocol.send_result(self.client_sock, True, self.results[self.id])

    def save_memory(self):
        data = {
            "clients_state": self.clients_state,
            "results": self.results,
            "id_counter": self.id_counter,
        }
        atomic_write("./data.txt", json.dumps(data))

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
                with self.shared_lock:
                    self.clients_state[self.id] = FINISH
                    self.save_memory()
                self.send_clean()
                self.protocol.send_ack(self.client_sock, True)
                break
            elif action == ASK_DATA:
                self.ask_for_data()

