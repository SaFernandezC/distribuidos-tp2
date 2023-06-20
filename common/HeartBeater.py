from time import sleep

from utils import get_docker_id
from Connection import Connection

HEARTBEATS_TOPIC = "heartbeat_ask"
HEARTBEATS = "heartbeat_reply"
ALIVE_ASK = "ALIVE?"


class HeartBeater():
    def __init__(self, connection: Connection) -> None:
        self.id = get_docker_id()

        self.connection = connection
        self.read_queue = self.connection.Subscriber(HEARTBEATS_TOPIC)
        self.send_queue = self.connection.Producer(HEARTBEATS)

    def callback(self, body, ack_tag):
        if body == ALIVE_ASK:
            self.send_queue.send(self.id)

        self.read_queue.ack(ack_tag)

    def start(self):
        self.read_queue.receive(self.callback)
