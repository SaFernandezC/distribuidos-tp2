import socket
import threading
import time
import logging
import multiprocessing
from .utils import AtomicValue
from .HeartBeatChecker import HeartBeatChecker
import signal

class Sender:
    def __init__(self, skt, queue):
        self.queue = queue
        self.skt = skt

    def run(self):
        while True:
            try:
                while True:
                    msg = self.queue.get()
                    self.skt.sendto(msg[0].encode(), msg[1])
                    # print(f"Send {msg[0]}")
            except Exception as e:
                logging.error("Sender: error sending message | error: {}".format(e))

class Receiver:
    def __init__(self, skt, queue):
        self.queue = queue    
        self.skt = skt    
    
    def run(self):
        try:
            while True:
                pair = self.skt.recvfrom(1024)
                self.queue.put(pair)
        except Exception as e:
            logging.error("Sender: error receiving message | error: {}".format(e))

WAIT_TIME = 10

class Monitor:
    def __init__(self, replica_id, replicas):
        self.replica_id = replica_id
        self.replicas = replicas
        self.is_leader = False

        self.leader_id = AtomicValue(None)
        self.election_in_process = AtomicValue(False)

        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.socket.bind(('', 5000 + self.replica_id))

        self.sender_queue = multiprocessing.Queue()
        self.receiver_queue = multiprocessing.Queue()

        self.sender_thread = threading.Thread(target=Sender(self.socket, self.sender_queue).run).start()
        self.receiver_thread = threading.Thread(target=Receiver(self.socket, self.receiver_queue).run).start()

        self.checkpoint = 0

        self.last_response_lock = threading.Lock() # Hacer un AtomicValue
        self.leader_last_response_time = 0
        self.leader_timeout_threshold = 5 

        self.check_alive_thread = None

        self.election_start_time_lock = threading.Lock() # Hacer un AtomicValue
        self.election_start_time = None

        self.heartbeat_thread = None

        self.alive = True
        signal.signal(signal.SIGTERM, self._handle_sigterm)


    def run(self):
        if self.replica_id == 3:
            logging.info(f"Replica {self.replica_id} starts listening")
            self.check_alive_thread = threading.Thread(target=self.check_leader)
            self.check_alive_thread.start()
            self.listen()
        else:
            logging.info(f"Replica {self.replica_id} starts listening")
            self.check_alive_thread = threading.Thread(target=self.check_leader)
            self.check_alive_thread.start()
            self.listen()

    def proclamate_leader(self):
        self.send_message_to_all("COORDINATOR")
        self.leader_id.set(self.replica_id)
        self.is_leader = True
        self.election_in_process.set(False)
        # LLAMADO A HACER LAS TAREAS DEL LIDER
        self.heartbeat_thread = threading.Thread(target=HeartBeatChecker().run).start()
        logging.info(f"Starts leader duties")


    def get_msg(self):
        pair = self.receiver_queue.get()
        msg = pair[0].decode()
        addr = pair[1]
        msg_from_replica = int(addr[1])-5000
        return msg, addr, msg_from_replica

    def win_election(self):
        with self.election_start_time_lock:
            if self.election_start_time == None: return False
            return time.time() - self.election_start_time > WAIT_TIME
    
    def set_checkpoint(self):
        with self.last_response_lock:
            self.leader_last_response_time = time.time()
    
    def set_election_start(self, value):
        with self.election_start_time_lock:
            self.election_start_time = value

    def listen(self):
        while True:

            winner = self.win_election()
            if not self.receiver_queue.empty() or winner:

                if winner:
                    self.set_election_start(None)
                    self.proclamate_leader()
                    continue
                
                msg, addr, msg_from_replica = self.get_msg()
                if msg == "COORDINATOR":
                    # TODO: Si yo era lider joinear mi self.hartBeat()
                    self.set_checkpoint()
                    self.leader_id.set(msg_from_replica)
                    self.election_in_process.set(False)
                    self.is_leader = False
                    logging.info(f"Replica {msg_from_replica} is the new leader.")

                elif msg == "ELECTION":
                    self.leader_id.set(None)
                    self.send_message_to_higher_replicas("ELECTION")
                    self.set_election_start(time.time())
                    self.election_in_process.set(True)

                    if self.replica_id > msg_from_replica:
                        self.sender_queue.put(("ANSWER", addr))   
                
                elif msg == "ALIVE?":
                    self.sender_queue.put(("ALIVE", addr))
                
                elif msg == "ALIVE":
                    self.set_checkpoint()

                elif msg == "ANSWER":
                    self.set_election_start(None)
                

    def new_election(self):
        logging.info(f"New Election")
        self.election_in_process.set(True)
        self.leader_id.set(None)
        self.send_message_to_higher_replicas("ELECTION")
        self.set_election_start(time.time())

    def check_leader(self):
        while True:
            if self.election_in_process.get():
                time.sleep(1)
                continue

            if self.is_leader:
                time.sleep(1)
                continue
            
            if self.leader_id.get() is None:
                self.new_election()
                continue

            with self.last_response_lock:
                if time.time() - self.leader_last_response_time > self.leader_timeout_threshold and self.leader_id.get() is not None:
                    print(f"Leader {self.leader_id.get()} is down. New leader election")
                    self.new_election()

            leader = self.leader_id.get()
            if leader is not None:
                self.sender_queue.put(("ALIVE?", ('monitor'+str(leader), 5000+leader)))
            time.sleep(1)

    def send_message_to_higher_replicas(self, message):
        for replica in self.replicas:
            if replica > self.replica_id:
                self.sender_queue.put((message, ('monitor'+str(replica), 5000+replica)))

    def send_message_to_all(self, message):
        for replica in self.replicas:
            self.sender_queue.put((message, ('monitor'+str(replica), 5000+replica)))


    def _handle_sigterm(self, *args):
        """
        Handles SIGTERM signal
        """
        logging.info('SIGTERM received - Shutting server down')
        self.stop()

    def stop(self):
        try:
            self.alive = False
            self.sender_thread.join()
            self.receiver_thread.join()
            self.heartbeat_thread.join()
        except Exception as e:
            logging.error(f"Error stopping monitor | error {e}")