from common.Connection import Connection
from common.HeartBeater import HEARTBEATS, HEARTBEATS_TOPIC, ALIVE_ASK

import time
import docker
from threading import Thread, Lock
import logging

TIME_BETWEEN = 20
DEAD_TIME = 5 * TIME_BETWEEN


class HeartBeatChecker():
    def __init__(self, nodes_to_check):
        self.connection = Connection()
        self.read_queue = self.connection.Consumer(HEARTBEATS)
        self.send_queue = self.connection.Publisher(HEARTBEATS_TOPIC)
        self.containers_lock = Lock()
        self.containers = {}
        now = time.time()
        for node in nodes_to_check:
            self.containers.update({node: now})

    def restart_container(self, node_id):
        logging.info(f"Waking up node {node_id}")
        result = subprocess.run(['docker', 'start', node_id], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info('Command executed. Result={}. Output={}. Error={}'.format(result.returncode, result.stdout, result.stderr))

    def restart_container(self, container_id):
        client = docker.from_env()
        try:
            container = client.containers.get(container_id)
            container.stop()
            container.start()

            print(f"Container {container_id} has been reset.")
        except docker.errors.NotFound:
            print(f"Container {container_id} not found.")
        except docker.errors.APIError as e:
            print(f"An error occurred while resetting the container: {e}")

    def callback(self, body, tag_id):
        now = time.time()
        container_id = body
        with self.containers_lock:
            self.containers.update({container_id: now})

        self.read_queue.ack(tag_id)

    def ask_alive(self):
        while True:
            with self.containers_lock:
                for docker_id, last_contact in self.containers.items():
                    now = time.time()
                    gap = now - last_contact
                    if gap > DEAD_TIME:
                        self.restart_container(docker_id)

            self.send_queue.send(ALIVE_ASK)
            time.sleep(TIME_BETWEEN)

    def read_heartbeats(self):
        self.read_queue.receive()
        self.connection.start_consuming()

    def run(self):
        sender = Thread(self.read_heartbeats)
        sender.start()
        self.ask_alive()
