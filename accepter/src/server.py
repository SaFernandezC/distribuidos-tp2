import time
import logging
import signal
from common.Socket import Socket
from .protocol import Protocol
import multiprocessing
from common.Connection import Connection
from .utils import Asker, CleanSender, SharedInteger
from .client import Client
from common.HeartBeater import HeartBeater
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

MAX_CLIENTS = 5

class Server:
    def __init__(self, port, listen_backlog, node_id):  # TO DO: Add File
        self._server_socket = Socket()
        self._server_socket.bind('', port)
        self._server_socket.listen(listen_backlog)

        self.is_alive = True
        signal.signal(signal.SIGTERM, self._handle_sigterm)

        self.protocol = Protocol()
        self.results = {}
        self.shared_lock = threading.Lock()
        # self.metrics_queue = self.connection.Consumer(queue_name='metrics')
        self.asker = Asker(self.results, self.shared_lock, node_id)
        self.ask_results = threading.Thread(target=self.asker.run)

        self.client_threads = []
        self.node_id = node_id
        self.get_previous_state()
        self.clean_previous_clients()

    def get_previous_state(self):
        previous_state = load_memory("./data.txt")
        self.current_clients = previous_state.get('current_clients', [])
        aux_id = previous_state.get('id_counter', 0)
        self.id_counter = SharedInteger(aux_id)
    
    def clean_previous_clients(self):
        cleaner = CleanSender(self.node_id)
        for client in self.current_clients:
            cleaner.send_clean(client)
        self.current_clients = []
        
    def run(self):
        """
        Main process: starts other processes and iterate accepting new clients.
        After accepting a new client pushes it to clients queue
        """
        self.ask_results.start()
        while self.is_alive:
            client_sock = self.__accept_new_connection()
            if client_sock:
                client = Client(client_sock, self.protocol, self.results, self.shared_lock, self.current_clients, self.id_counter)
                thread = threading.Thread(target=client.run)
                thread.start()
                self.client_threads.append(thread)
            elif client_sock is None:
                time.sleep(1)

    def __accept_new_connection(self):
        """
        Accept new connections
        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """
        logging.info('action: accept_connections | result: in_progress')
        
        with self.shared_lock:
            if len(self.current_clients) >= MAX_CLIENTS: #TODO: PONER CONSTANTES
                print("Reject Client")
                return None
        
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