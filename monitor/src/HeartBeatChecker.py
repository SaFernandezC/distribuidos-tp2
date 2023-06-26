from common.Connection import Connection
from common.HeartBeater import HEARTBEATS, HEARTBEATS_TOPIC, ALIVE_ASK

import time
from threading import Thread, Lock
import logging
import subprocess

TIME_BETWEEN = 3
DEAD_TIME = 3 * TIME_BETWEEN


class HeartBeatChecker():
    def __init__(self, nodes_to_check, heartbeat_event):
        self.connection_send = Connection()
        self.connection_read = Connection()

        self.read_queue = self.connection_read.Consumer(HEARTBEATS)

        self.reader_lock = Lock()
        self.send_queue = self.connection_send.Publisher(HEARTBEATS_TOPIC, "fanout")
        self.containers_lock = Lock()
        self.containers = {}
        self.nodes = nodes_to_check
        self.set_timers_now()

        self.heartbeat_event = heartbeat_event

    def set_timers_now(self):
        with self.containers_lock:
            now = time.time()
            for node in self.nodes:
                self.containers.update({node: now})


    def restart_container(self, node_id):
        logging.info(f"Waking up node {node_id}")
        result = subprocess.run(['docker', 'start', node_id], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info('Command executed. Result={}. Output={}. Error={}'.format(result.returncode, result.stdout, result.stderr))


    def ask_alive(self):
        updated = False
        while True:
            if self.heartbeat_event.is_set():
                if not updated:
                    self.set_timers_now()
                updated = True
                with self.containers_lock:
                    for docker_id, last_contact in self.containers.items():
                        now = time.time()
                        gap = now - last_contact
                        if gap > DEAD_TIME:
                            self.restart_container(docker_id)
                self.send_queue.send(ALIVE_ASK)
                time.sleep(TIME_BETWEEN)
            else:
                updated = False


    def callback(self, body, tag_id):
        if not self.heartbeat_event.is_set():
            self.connection_read.stop_consuming()
            return
        now = time.time()
        container_id = body.decode()
        with self.containers_lock:
            self.containers.update({container_id: now})

        self.read_queue.ack(tag_id)

    def read_heartbeats(self):
        while True:
            if self.heartbeat_event.is_set():
                self.read_queue.receive(self.callback)
                self.connection_read.start_consuming()

    def run(self):
        self.reader = Thread(target=self.read_heartbeats)
        self.reader.start()
        self.ask_alive()
