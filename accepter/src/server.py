import logging
import signal
from .socket_wrapper import Socket
from .protocol import Protocol
import multiprocessing
from common.Connection import Connection
from .utils import Asker
from .client import Client
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

        # self.metrics_queue = self.connection.Consumer(queue_name='metrics')
        # self.results_queue = multiprocessing.Queue()
        # self.asker = Asker(self.connection, self.metrics_queue, self.results_queue)
        # self.ask_results = multiprocessing.Process(target=self.asker.run, args=())

        self.id_counter = self._init_id_counter()
        self.client_threads = []

    def _init_id_counter(self):
        return 0
    
    def run(self):
        """
        Main process: starts other processes and iterate accepting new clients.
        After accepting a new client pushes it to clients queue
        """
        # self.ask_results.start()
        while self.is_alive:
            client_sock = self.__accept_new_connection()
            if client_sock:     
                client = Client(self.id_counter, client_sock, self.protocol)
                thread = threading.Thread(target=client.run)
                thread.start()
                self.client_threads.append(thread) # Guardar el cliente tambien?
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