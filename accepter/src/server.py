import logging
import signal
from .socket_wrapper import Socket
from .protocol import Protocol
import multiprocessing
from common.Connection import Connection
from .utils import Asker
import ujson as json

import threading

FINISH = 'F'
SEND_DATA = 'D'
SEND_EOF = 'E'
SEND_WEATHERS = 'W'
SEND_STATIONS = 'S'
SEND_TRIPS = 'T'
ASK_DATA = 'A'
INT_LENGTH = 4

class Server:
    def __init__(self, port, listen_backlog):  # TO DO: Add File
        self._server_socket = Socket()
        self._server_socket.bind('', port)
        self._server_socket.listen(listen_backlog)
        
        self.is_alive = True
        signal.signal(signal.SIGTERM, self._handle_sigterm)

        self.protocol = Protocol()
        self.connection = Connection()

        self.eof_manager = self.connection.EofProducer(None, None, None)
        self.trips_queue = self.connection.Producer(queue_name="trip")
        self.weathers_queue = self.connection.Producer(queue_name="weather")
        self.stations_queue = self.connection.Producer(queue_name="station")

        # self.metrics_queue = self.connection.Consumer(queue_name='metrics')
        # self.results_queue = multiprocessing.Queue()
        # self.asker = Asker(self.connection, self.metrics_queue, self.results_queue)
        # self.ask_results = multiprocessing.Process(target=self.asker.run, args=())

        self.id_counter = self._init_id_counter()
        self.client_threads = []

    def _init_id_counter(self):
        return 0

    def recv_data(self, client_sock, key, client_id):
        logging.debug(f'action: receiving data')
        data = self.protocol.recv_data(client_sock)
        # data = client_id.to_bytes(INT_LENGTH, byteorder='big') + data
        batch = json.dumps({"client_id": client_id, "data": json.loads(data)})

        if key == "trip":
            self.trips_queue.send(batch)
        elif key == "station":
            self.stations_queue.send(batch)
        else:
            self.weathers_queue.send(batch)
        self.protocol.send_ack(client_sock, True)

    def send_eof(self, key, client_id):
        self.eof_manager.send_eof(client_id, {"type":"work_queue", "queue": key})

    def recv_eof(self, client_sock, key, client_id): 
        logging.debug(f'action: receiving eof')
        data = self.protocol.recv_data(client_sock)
        self.send_eof(key, client_id)
        self.protocol.send_ack(client_sock, True)


    def ask_for_data(self, client_sock, client_id):
        # result_queue = self.connection.Subscriber("results", 'topic', None, client_id)
        # result_queue.receive(callback)

        # def callback(body):
        #     data = body.decode()
        #     self.protocol.send_result(client_sock, True, data)
        # logging.info(f"Sending results for client: {client_id}")
        self.protocol.send_result(client_sock, True)

    def handle_con(self, client_sock, client_id):
        while True:
            if not self.is_alive:
                break
            action = self.protocol.recv_action(client_sock)
            if action == SEND_DATA:
                key = self.protocol.recv_key(client_sock)
                self.recv_data(client_sock, key, client_id)
            elif action == SEND_EOF:
                key = self.protocol.recv_key(client_sock)
                self.recv_eof(client_sock, key, client_id)
            elif action == FINISH:
                self.protocol.send_ack(client_sock, True)
                break
            elif action == ASK_DATA:
                self.ask_for_data(client_sock, client_id)
    
    def run(self):
        """
        Main process: starts other processes and iterate accepting new clients.
        After accepting a new client pushes it to clients queue
        """
        # self.ask_results.start()
        while self.is_alive:
            client_sock = self.__accept_new_connection()
            if client_sock:
                # self.handle_con(client_sock)
                thread = threading.Thread(target=self.handle_con, args=[client_sock, self.id_counter])
                thread.start()              
                self.client_threads.append(thread)
                self.id_counter += 1
            elif self.is_alive:
                self.stop()

    def __accept_new_connection(self):
        """
        Accept new connections
        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """
        logging.info('action: accept_connections | result: in_progress')
        c = self._server_socket.accept()
        addr = c.get_addr()
        logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
        return c

    def _handle_sigterm(self, *args):
        """
        Handles SIGTERM signal
        """
        logging.info('SIGTERM received - Shutting server down')
        self.stop()

    def stop(self):
        """
        Stops the server
        """
        self.is_alive = False
        try:
            # self.ask_results.join()
            self.connection.close()
            self._server_socket.close()

            for thread in self.client_threads:
                if thread.is_alive():
                    thread.join()

        except OSError as e:
            logging.error("action: stop server | result: fail | error: {}".format(e))
        finally:
            logging.info('Server stopped')  