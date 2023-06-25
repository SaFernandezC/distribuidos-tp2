import logging
import signal
from common.Socket import Socket
from .protocol import Protocol
# import multiprocessing
# from common.Connection import Connection
from .utils import Asker, CleanSender
from .client import Client
# from common.HeartBeater import HeartBeater
import ujson as json
from common.AtomicWrite import atomic_write, load_memory

import threading

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

class Server:
    def __init__(self, port, listen_backlog, node_id):  # TO DO: Add File
        self._server_socket = Socket()
        self._server_socket.bind('', port)
        self._server_socket.listen(listen_backlog)

        self.is_alive = True
        self.node_id = node_id
        signal.signal(signal.SIGTERM, self._handle_sigterm)

        self.get_previous_state()

        self.protocol = Protocol()

        self.shared_lock = threading.Lock()
        
        self.asker = Asker(self.results, self.shared_lock, node_id)
        self.ask_results = threading.Thread(target=self.asker.run)
        self.client_threads = []
        


    def get_previous_state(self):
        previous_state = load_memory("./data.txt")
        self.clients_state = previous_state.get('clients_state', {})
        self.results = previous_state.get('results', {})
        self.id_counter = previous_state.get('id_counter', 0)   

    # def check_previous_state(self):
    #     clean_sender = CleanSender(self.node_id)
    #     for client_id, status in self.clients_state.items():
    #         if status == SENDING:
    #             clean_sender.send_clean(client_id)

    def save_memory(self):
        with self.shared_lock:
            data = {
                "clients_state": self.clients_state,
                "results": self.results,
                "id_counter": self.id_counter,
            }
            atomic_write("./data.txt", json.dumps(data))

    def run(self):
        """
        Main process: starts other processes and iterate accepting new clients.
        After accepting a new client pushes it to clients queue
        """
        self.ask_results.start()
        while self.is_alive:
            client_sock = self.__accept_new_connection()
            if client_sock:
                # client_id = str(self.id_counter)
                client = Client(client_sock, self.protocol, self.results, self.shared_lock, self.clients_state, self.id_counter)
                thread = threading.Thread(target=client.run)
                thread.start()
                self.client_threads.append(thread)

                # self.clients_state[client_id] = SENDING
                # self.id_counter += 1
                # self.save_memory()
                # Save state
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
            self.ask_results.join()
            self.connection.close()
            self._server_socket.close()

            for thread in self.client_threads:
                if thread.is_alive():
                    thread.join()

        except OSError as e:
            logging.error("action: stop server | result: fail | error: {}".format(e))
        finally:
            logging.info('Server stopped')  