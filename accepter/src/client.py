import logging
from common.Connection import Connection
from common.AtomicWrite import atomic_write
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
    def __init__(self, client_sock, protocol, results, shared_lock, current_clients, id_counter):
        with shared_lock:
            self.client_sock = client_sock
            self.protocol = protocol
            self.results = results
            self.shared_lock = shared_lock
            self.current_clients = current_clients
            
            current = id_counter.get()
            self.id = str(current)
            self.id_counter = id_counter
            id_counter.increment()

            self.current_clients.append(self.id)

            self.connection = Connection()
            self.eof_manager = self.connection.EofProducer(None, None, "Accepter")
            self.trips_queue = self.connection.Producer(queue_name="trip")
            self.weathers_queue = self.connection.Producer(queue_name="weather")
            self.stations_queue = self.connection.Producer(queue_name="station")
        self.save_memory()

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
        self.eof_manager.send_eof(self.id, {"type":"work_queue", "queue": key+"_parser"})
    
    def send_clean(self):
        for key in ['trip', 'station', 'weather']:
            self.eof_manager.send_eof(self.id, {"type":"work_queue", "queue": key+"_parser"}, msg_type="clean")

    def recv_eof(self, key): 
        logging.debug(f'action: receiving eof')
        data = self.protocol.recv_data(self.client_sock)
        self.send_eof(key)
        self.protocol.send_ack(self.client_sock, True)
    
    def save_memory(self):
        with self.shared_lock:
            data = {
                "current_clients": self.current_clients,
                "id_counter": self.id_counter.get(),
            }
            atomic_write("./data.txt", json.dumps(data))

    def ask_for_data(self):
        with self.shared_lock:
            if not self.id in self.results:
                self.protocol.send_result(self.client_sock, False)
            else:
                self.protocol.send_result(self.client_sock, True, self.results[self.id])

    def run(self):
        while True:
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
                
        with self.shared_lock:
            if self.id in self.current_clients:
                self.current_clients.remove(self.id)
        self.save_memory()
        self.send_clean()
            


