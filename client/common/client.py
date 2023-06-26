from .socket import Socket
from .protocol import Protocol
import logging
import signal
import json


class Client:
    def __init__(self, server_ip, server_port, lines_per_batch):
        try:
            self.client_socket = Socket()
            self.protocol = Protocol()
            self.lines_per_batch = lines_per_batch
            self.client_socket.connect(server_ip, server_port)
            signal.signal(signal.SIGTERM, self._handle_sigterm)
        except Exception as e:
            self.stop()
            logging.error("action: create client | result: fail | error: {}".format(e))
            raise Exception("Server Not Available")


    def send_finish(self):
        logging.info(f'action: send finish | sending finish')
        try:
            self.protocol.finish_sending_data(self.client_socket)
            ack = self.protocol.recv_ack(self.client_socket)
            if(ack):
                logging.info(f'action: send finish | result: success')
            else:
                logging.info(f'action: send finish | result: fail')
        except Exception as e:
            logging.error("action: send weathers | result: fail | error: {}".format(e))
  

    def send_weathers(self, weathers):
        try:
            for city, path in weathers.items():
                self.send_data(city, path, self.protocol.send_weather)
            self.protocol.send_weather_eof(self.client_socket)
            ack = self.protocol.recv_ack(self.client_socket)
            if(ack):
                logging.debug(f'action: send weathers | result: success')
            else:
                logging.debug(f'action: send weathers | result: fail')
        except Exception as e:
            logging.error("action: send weathers | result: fail | error: {}".format(e))


    def send_stations(self, stations):
        try:
            for city, path in stations.items():
                self.send_data(city, path, self.protocol.send_station)
            self.protocol.send_stations_eof(self.client_socket)
            ack = self.protocol.recv_ack(self.client_socket)
            if(ack):
                logging.debug(f'action: send stations | result: success')
            else:
                logging.debug(f'action: send stations | result: fail')
        except Exception as e:
            logging.error("action: send stations | result: fail | error: {}".format(e))


    def send_trips(self, trips):
        try:
            for city, path in trips.items():
                self.send_data(city, path, self.protocol.send_trip)
            self.protocol.send_trips_eof(self.client_socket)
            ack = self.protocol.recv_ack(self.client_socket)
            if(ack):
                logging.debug(f'action: send trips | result: success')
            else:
                logging.debug(f'action: send trips | result: fail')
        except Exception as e:
            logging.error("action: send trips | result: fail | error: {}".format(e))

    def send_data(self, city, file_path, send_function):
        """
        Iterates until all bets from file are sent.
        Then calls ask_for_winners() function
        """
        finished = False
        try:
            with open(file_path) as file:
                file.readline() # Avoid first line
                while not finished:
                    finished, batch = self.next_batch(file)
                    send_function(self.client_socket, city, batch)
                    ack = self.protocol.recv_ack(self.client_socket)
                    if(ack):
                        logging.debug(f'action: send data ack | result: success')
                    else:
                        logging.debug(f'action: send data ack | result: fail')
        except Exception as e:
            logging.error("action: send data | result: fail | error: {}".format(e)) 


    def next_batch(self, file):
        """
        Reads next lines batch from file.
        Returns lines and True if that is last_batch, else False
        """
        lines = []
        for i in range(self.lines_per_batch):
            line = file.readline().strip()
            if not line:
                return True, lines
            lines.append(line)
        return False, lines

    def ask_results(self):
        return self.protocol.ask_results(self.client_socket)

    def _handle_sigterm(self, *args):
        """
        Handles SIGTERM signal
        """
        logging.info('SIGTERM received - Shutting client down')
        self.stop()

    def stop(self):
        """
        Stops the client
        """
        try:
            self.client_socket.close()
            logging.info("action: stop client | result: success")  
        except OSError as e:
            logging.error("action: stop client | result: fail | error: {}".format(e))