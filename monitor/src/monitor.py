import socket
import threading
import time
import logging
import multiprocessing
from .utils import AtomicValue, Sender, Receiver
from .HeartBeatChecker import HeartBeatChecker
import signal
from common.Connection import Connection
from common.HeartBeater import HeartBeater

WIN_TIME = 15
WAIT_TIME = 2 * WIN_TIME
SLEEP_TIME = 1
TIMEOUT_THRESHOLD = 5

class Monitor:
    def __init__(self, replica_id, replicas, nodes):
        self.replica_id = replica_id
        self.replicas = replicas
        self.is_leader = AtomicValue(False)

        self.leader_id = AtomicValue(None)
        self.election_in_process = AtomicValue(False)
        
        self.other_election_start_lock = threading.Lock()
        self.other_election_start = None

        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.socket.bind(('', 5000 + self.replica_id))

        self.sender_queue = multiprocessing.Queue()
        self.receiver_queue = multiprocessing.Queue()

        self.sender_thread = threading.Thread(target=Sender(self.socket, self.sender_queue).run)
        self.sender_thread.start()

        self.receiver_thread = threading.Thread(target=Receiver(self.socket, self.receiver_queue).run)
        self.receiver_thread.start()

        self.last_response_lock = threading.Lock()
        self.leader_last_response_time = 0

        self.leader_timeout_threshold = TIMEOUT_THRESHOLD

        self.check_alive_thread = None

        self.election_start_time_lock = threading.Lock()
        self.election_start_time = None

        signal.signal(signal.SIGTERM, self._handle_sigterm)
        self.nodes = nodes

        self.heartbeat_event = threading.Event()
        self.heartbeat_thread = threading.Thread(target=HeartBeatChecker(self.nodes, self.heartbeat_event).run)
        self.heartbeat_thread.start()

        self.connection = Connection()
        self.node_id = f"monitor_{self.replica_id}"

    def start_heartbeater(self):
        self.heartbeater = HeartBeater(self.connection, self.node_id)
        self.heartbeater.start()
        self.connection.start_consuming()

    def run(self):
        logging.info(f"Replica {self.replica_id} starts listening")
        self.heartbeat_sender_thread = threading.Thread(target=self.start_heartbeater)
        self.heartbeat_sender_thread.start()
        self.check_alive_thread = threading.Thread(target=self.check_leader)
        self.check_alive_thread.start()
        self.listen()


    def proclamate_leader(self):
        self.send_message_to_all("COORDINATOR")
        self.leader_id.set(self.replica_id)
        self.is_leader.set(True)
        self.heartbeat_event.set()
        logging.info(f"Starts leader duties")
        self.election_in_process.set(False)


    def get_msg(self):
        pair = self.receiver_queue.get()
        msg = pair[0].decode()
        addr = pair[1]
        msg_from_replica = int(addr[1])-5000
        return msg, addr, msg_from_replica

    def win_election(self):
        with self.election_start_time_lock:
            if self.election_start_time == None: return False
            return time.time() - self.election_start_time > WIN_TIME
            
    def set_checkpoint(self):
            with self.last_response_lock:
                self.leader_last_response_time = time.time()

    def set_election_start(self, value):
            with self.election_start_time_lock:
                self.election_start_time = value

    def set_other_election_start(self, value):
            with self.other_election_start_lock:
                self.other_election_start = value

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
                    self.set_checkpoint()
                    self.leader_id.set(msg_from_replica)
                    self.election_in_process.set(False)
                    self.is_leader.set(False)
                    self.set_other_election_start(None)
                    self.heartbeat_event.clear()
                    logging.info(f"Replica {msg_from_replica} is the new leader.")

                elif msg == "ELECTION":
                    self.leader_id.set(None)
                    self.send_message_to_higher_replicas("ELECTION")
                    self.set_election_start(time.time())
                    self.election_in_process.set(True)

                    if self.replica_id > msg_from_replica:
                        print(f"Envio ANSWER A [{msg_from_replica}]")
                        self.sender_queue.put(("ANSWER", addr))
                
                elif msg == "ALIVE?":
                    self.sender_queue.put(("ALIVE", addr))
                
                elif msg == "ALIVE":
                    self.set_checkpoint()

                elif msg == "ANSWER":
                    self.set_election_start(None)
                    print(f"RECIBO ANSWER De [{msg_from_replica}]")
                    with self.other_election_start_lock:
                        self.other_election_start = time.time()
                    
    def new_election(self):
        logging.info(f"New Election")
        self.election_in_process.set(True)
        self.leader_id.set(None)
        self.send_message_to_higher_replicas("ELECTION")
        self.set_election_start(time.time())

    def election_due(self):
        with self.other_election_start_lock:
            aux = self.other_election_start
            if aux is None:
                return False
            else:
                return time.time() - aux > WAIT_TIME

    def check_leader(self):
        while True:
            if self.election_due():
                with self.election_start_time_lock:
                    if self.election_start_time is None:
                        self.election_in_process.set(False)
                        self.election_start_time = None

            if self.election_in_process.get():
                time.sleep(SLEEP_TIME)
                continue

            if self.is_leader.get():
                time.sleep(SLEEP_TIME)
                continue
            
            if self.leader_id.get() is None:
                self.new_election()
                continue

            with self.last_response_lock:
                # print("Comparo Tiempos")
                if time.time() - self.leader_last_response_time > self.leader_timeout_threshold and self.leader_id.get() is not None:
                    print(f"Leader {self.leader_id.get()} is down. New leader election")
                    self.new_election()

            leader = self.leader_id.get()
            if leader is not None:
                self.sender_queue.put(("ALIVE?", ('monitor_'+str(leader), 5000+leader)))
            time.sleep(SLEEP_TIME)

    def send_message_to_higher_replicas(self, message):
        for replica in self.replicas:
            if replica > self.replica_id:
                self.sender_queue.put((message, ('monitor_'+str(replica), 5000+replica)))

    def send_message_to_all(self, message):
        for replica in self.replicas:
            self.sender_queue.put((message, ('monitor_'+str(replica), 5000+replica)))


    def _handle_sigterm(self, *args):
        """
        Handles SIGTERM signal
        """
        logging.info('SIGTERM received - Shutting server down')
        self.stop()

    def stop(self):
        try:
            if self.check_alive_thread:
                self.check_alive_thread.join()
            if self.sender_thread:
                self.sender_thread.join()
            if self.heartbeat_sender_thread:
                self.sender_thread.join()
            if self.receiver_thread:
                self.receiver_thread.join()
            if self.heartbeat_thread:
                self.heartbeat_thread.join()
            self.connection.close()
        except Exception as e:
            logging.error(f"Error stopping monitor | error {e}")