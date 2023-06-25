from configparser import ConfigParser
import os
import logging
import ujson as json

SEND_WEATHERS = 'W'
SEND_STATIONS = 'S'
SEND_TRIPS = 'T'

SEND_FINISH = 'F'
SEND_DATA = 'D'
SEND_EOF = 'E'
ACK_OK = 0
ACK_ERROR = 1
ASK_DATA = 'A'

def _initialize_config():
    config = ConfigParser(os.environ)
    # If config.ini does not exists original config object is not modified
    path = os.path.dirname(os.path.realpath(__file__))
    configdir = '/'.join([path,'protocol.ini'])
    config.read(configdir)

    config_params = {}
    try:
        config_params["max_packet_size"] = int(os.getenv('MAX_PACKET_SIZE', config["DEFAULT"]["MAX_PACKET_SIZE"]))
        config_params["cant_bytes_len"] = int(os.getenv('CANT_BYTES_LEN', config["DEFAULT"]["CANT_BYTES_LEN"]))
        config_params["cant_bytes_ack"] = int(os.getenv('CANT_BYTES_ACK', config["DEFAULT"]["CANT_BYTES_ACK"]))
        config_params["cant_bytes_action"] = int(os.getenv('CANT_BYTES_ACTION', config["DEFAULT"]["CANT_BYTES_ACTION"]))

    except KeyError as e:
        raise KeyError("Key was not found. Error: {} .Aborting".format(e))
    except ValueError as e:
        raise ValueError("Key could not be parsed. Error: {}. Aborting".format(e))

    return config_params

class Protocol:
    def __init__(self):
        config_params = _initialize_config()
        self.max_packet_size = config_params["max_packet_size"]
        self.cant_bytes_len = config_params["cant_bytes_len"]
        self.cant_bytes_ack = config_params["cant_bytes_ack"]
        self.cant_bytes_action = config_params["cant_bytes_action"]

    def _divide_msg(self, bet, bet_size):
        """
        Returns size of packets to send as we can't 
        send more than 8192 bytes per packet
        """
        if bet_size < self.max_packet_size:
            return [bet]
        
        n = self.max_packet_size
        chunks = [bet[i:i+n] for i in range(0, bet_size, n)]
        return chunks

    def _send_chunk(self, skt, chunk, chunk_size):
        """
        Send chunk divided into parts that do not
        exceed size limit (8192b)
        """
        skt.send_msg(chunk_size.to_bytes(self.cant_bytes_len, byteorder='big'))

        divided_chunk = self._divide_msg(chunk, chunk_size)
        for part in divided_chunk:
            skt.send_msg(part)

    def send_weather(self, skt, city, data):
        skt.send_msg(bytes(SEND_DATA, 'utf-8'))
        skt.send_msg(bytes(SEND_WEATHERS, 'utf-8'))
        batch = bytes(json.dumps({"type": "weathers", "city": city, "data": data}), 'utf-8')
        batch_size = len(batch)
        self._send_chunk(skt, batch, batch_size)
        logging.debug(f'action: weather batch sended | result: success | city: {city} | msg_len: {batch_size}')

    def send_weather_eof(self, skt):
        skt.send_msg(bytes(SEND_EOF, 'utf-8'))
        skt.send_msg(bytes(SEND_WEATHERS, 'utf-8'))
        self.send_eof(skt, "weathers")
        logging.debug(f'action: weather eof sended | result: success')

    def send_station(self, skt, city, data):
        skt.send_msg(bytes(SEND_DATA, 'utf-8'))
        skt.send_msg(bytes(SEND_STATIONS, 'utf-8'))
        batch = bytes(json.dumps({"type": "stations", "city": city, "data": data}), 'utf-8')
        batch_size = len(batch)
        self._send_chunk(skt, batch, batch_size)
        logging.debug(f'action: stations batch sended | result: success | city: {city} | msg_len: {batch_size}')

    def send_stations_eof(self, skt):
        skt.send_msg(bytes(SEND_EOF, 'utf-8'))
        skt.send_msg(bytes(SEND_STATIONS, 'utf-8'))
        self.send_eof(skt, "stations")
        logging.debug(f'action: stations eof sended | result: success')

    def send_trip(self, skt, city, data):
        skt.send_msg(bytes(SEND_DATA, 'utf-8'))
        skt.send_msg(bytes(SEND_TRIPS, 'utf-8'))
        batch = bytes(json.dumps({"type": "trips", "city": city, "data": data}), 'utf-8')
        batch_size = len(batch)
        self._send_chunk(skt, batch, batch_size)
        logging.debug(f'action: trips batch sended | result: success | city: {city} | msg_len: {batch_size}')

    def send_trips_eof(self, skt):
        skt.send_msg(bytes(SEND_EOF, 'utf-8'))
        skt.send_msg(bytes(SEND_TRIPS, 'utf-8'))
        self.send_eof(skt, "trips")
        logging.debug(f'action: trips eof sended | result: success')

    def send_eof(self, skt, type):        
        batch = bytes(json.dumps({"type":type, "eof": True}), 'utf-8')
        batch_size = len(batch)
        self._send_chunk(skt, batch, batch_size)
        logging.debug(f'action: send eof | result: success')

    def finish_sending_data(self, skt):
        skt.send_msg(bytes(SEND_FINISH, 'utf-8'))

    def ask_results(self, skt):
        skt.send_msg(bytes(ASK_DATA, 'utf-8'))
        res = json.loads(self._recv_chunk(skt))
        if res["ready"] == False:
            return False, {}
        else:
            return True, res["data"]
            # return True, json.loads(res["data"])

    def recv_ack(self, skt):
        """
        Receives ACK and returns it
        """ 
        ack_bytes = skt.recv_msg(self.cant_bytes_ack)
        ack = int.from_bytes(ack_bytes, byteorder='big')

        response = True if ack == ACK_OK else False
        logging.debug(f'action: Receive ack | result: success | ip: {skt.get_addr()} | msg: {response}')
        return response

    def _recv_chunk(self, skt):
        batch_size_bytes = skt.recv_msg(self.cant_bytes_len)
        batch_size = int.from_bytes(batch_size_bytes, byteorder='big')
        batch = skt.recv_msg(batch_size).decode()
        return batch

    def send_status(self, skt, id, status):
        msg = {"id": id, "status": status}
        batch = bytes(json.dumps(msg), 'utf-8')
        batch_size = len(batch)
        self._send_chunk(skt, batch, batch_size)

    def recv_status(self, skt): 
        status = self._recv_chunk(skt)
        return json.loads(status)
        