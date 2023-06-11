import socket
import threading
import time
import logging

class Monitor:
    def __init__(self, replica_id, replicas):
        self.replica_id = replica_id
        self.replicas = replicas
        self.leader_id = None
        self.is_leader = False
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('', 5000 + self.replica_id))
        self.socket.listen(5)
        self.connections = []
        self.checkpoint = 0

        self.start()

    def start(self):
        self.connect_to_higher_replicas()
        self.accept_connections()

    def connect_to_higher_replicas(self):
        for higher_replica in self.replicas:
            if higher_replica > self.replica_id:
                try:
                    higher_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    higher_socket.connect(('monitor'+str(higher_replica), 5000 + higher_replica))
                    self.connections.append(higher_socket)
                except ConnectionRefusedError:
                    print(f'Replica {self.replica_id} failed to connect to higher replica {higher_replica}')

    def accept_connections(self):
        while True:
            conn, _ = self.socket.accept()
            self.connections.append(conn)
            threading.Thread(target=self.handle_client, args=(conn,)).start()

    def handle_client(self, conn):
        while True:
            data = conn.recv(1024).decode()
            if data == "ELECTION":
                if self.leader_id is None or self.leader_id < self.replica_id:
                    conn.sendall(b"OK")
                    self.start_election()
                else:
                    conn.sendall(b"NOT_OK")
            elif data == "COORDINATOR":
                self.leader_id = self.replica_id
                # self.send_message_to_all("COORDINATOR")
                print(f"Replica {self.replica_id} is the new leader.")

    def start_election(self):
        print(f"Replica {self.replica_id} is starting an election.")
        self.send_message_to_higher_replicas("ELECTION")

    def send_message_to_higher_replicas(self, message):
        for conn in self.connections:
            conn.sendall(message.encode())

    def send_message_to_all(self, message):
        for conn in self.connections:
            conn.sendall(message.encode())

    def check_leader(self):
        while True:
            if self.leader_id is not None:
                try:
                    leader_socket = self.connections[self.leader_id - self.replica_id - 1]
                    leader_socket.sendall(b"ALIVE?")
                    response = leader_socket.recv(1024).decode()
                    if response != "ALIVE!":
                        print(f"Leader (Replica {self.leader_id}) is no longer alive.")
                        self.leader_id = None
                except IndexError:
                    print(f"Invalid leader ID: {self.leader_id}")
                    self.leader_id = None
                except ConnectionResetError:
                    print(f"Leader (Replica {self.leader_id}) connection reset.")
                    self.leader_id = None
            time.sleep(5)

    def check_coordinator(self):
        while True:
            for conn in self.connections:
                conn.sendall(b"ALIVE?")
                response = conn.recv(1024).decode()
                if response.startswith("ALIVE!"):
                    new_leader_id = int(response.split(":")[1])
                    if self.leader_id != new_leader_id:
                        print(f"Replica {self.replica_id} found new leader: Replica {new_leader_id}")
                        self.leader_id = new_leader_id
            time.sleep(5)

    def start_election_process(self):
        self.start_election()
        self.check_leader()

    def start_coordinator_process(self):
        self.check_coordinator()


    def proclamate_leader(self):
        self.send_message_to_all("COORDINATOR")
        self.leader_id = self.replica_id
        self.is_leader = True
        self.set_checkpoint()

    def set_checkpoint(self):
        self.checkpoint = time.time()

    def run(self):
        if self.replica_id == 3:
            self.proclamate_leader()
            logging.info(f"Replica {self.replica_id} proclamates leader")
        else:
            logging.info(f"Replica {self.replica_id} starts election")
            self.start_election_process()

        return 0
