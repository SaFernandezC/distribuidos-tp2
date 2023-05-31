from configparser import ConfigParser
import os
import logging
import json

SEND_WEATHERS = 'W'
SEND_STATIONS = 'S'
SEND_TRIPS = 'T'
ACK_OK = 0
ACK_ERROR = 1

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
        config_params["cant_bytes_key"] = int(os.getenv('CANT_BYTES_KEY', config["DEFAULT"]["CANT_BYTES_KEY"]))

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
        self.cant_bytes_key = config_params["cant_bytes_key"]

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

    def _recv_chunk(self, skt):
        batch_size_bytes = skt.recv_msg(self.cant_bytes_len)
        batch_size = int.from_bytes(batch_size_bytes, byteorder='big')
        batch = skt.recv_msg(batch_size).decode()
        return batch

    def recv_data(self, skt):
        return self._recv_chunk(skt)

    def recv_action(self, skt):
        return skt.recv_msg(self.cant_bytes_action).decode()
    
    def recv_key(self, skt):
        key = skt.recv_msg(self.cant_bytes_key).decode()
        if key == SEND_TRIPS: return "trip"
        if key == SEND_STATIONS: return "station"
        if key == SEND_WEATHERS: return "weather"


    def send_result(self, skt, ready, data=""):
        msg = bytes(json.dumps({"ready": ready, "data":data}),  'utf-8')
        msg_size = len(msg)
        self._send_chunk(skt, msg, msg_size)

    def send_ack(self, skt, status):
        """
        Receives status=true for OK_ACK or status=false for ERROR
        Sends ACK
        """ 
        msg = ACK_OK if status == True else ACK_ERROR
        skt.send_msg(msg.to_bytes(self.cant_bytes_ack, byteorder='big'))
        logging.debug(f'action: Send ack | result: success | ip: {skt.get_addr()} | msg: {status}')

    def recv_ack(self, skt):
        """
        Receives ACK and returns it
        """ 
        ack_bytes = skt.recv_msg(self.cant_bytes_ack)
        ack = int.from_bytes(ack_bytes, byteorder='big')

        response = True if ack == ACK_OK else False
        logging.debug(f'action: Receive ack | result: success | ip: {skt.get_addr()} | msg: {response}')
        return response
