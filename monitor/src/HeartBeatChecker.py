from common.Connection import Connection
from common.HeartBeater import HEARTBEATS, HEARTBEATS_TOPIC, ALIVE_ASK

import time
# import docker
from threading import Thread, Lock
import logging
import subprocess

TIME_BETWEEN = 20
DEAD_TIME = 10 * TIME_BETWEEN


class HeartBeatChecker():
    def __init__(self, nodes_to_check):
        self.connection_send = Connection()
        self.connection_read = None

        self.reader_lock = Lock()
        self.send_queue = self.connection_send.Publisher(HEARTBEATS_TOPIC, "fanout")
        self.containers_lock = Lock()
        self.containers = {}
        now = time.time()
        self.reader = None
        self.read_id = None
        for node in nodes_to_check:
            self.containers.update({node: now})

    def restart_container(self, node_id):
        logging.info(f"Waking up node {node_id}")
        result = subprocess.run(['docker', 'start', node_id], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logging.info('Command executed. Result={}. Output={}. Error={}'.format(result.returncode, result.stdout, result.stderr))


    def callback(self, body, tag_id):
        now = time.time()
        container_id = body.decode()
        print(f"Recibi Heartbeat de {container_id}")
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
        self.connection_read = Connection()
        self.read_queue = self.connection_read.Consumer(HEARTBEATS)
        self.read_id = self.read_queue.receive(self.callback)
        self.connection_read.start_consuming()

    def run(self):
        self.reader = Thread(target=self.read_heartbeats)
        self.reader.start()
        self.ask_alive()


















# import threading
# import pika

# class ConsumerThread(threading.Thread):
#     def __init__(self, connection_params, queue_name):
#         super().__init__()
#         self.connection_params = connection_params
#         self.queue_name = queue_name
#         self.connection = None
#         self.channel = None
#         self.consumer_tag = None

#     def run(self):
#         self.connection = pika.BlockingConnection(self.connection_params)
#         self.channel = self.connection.channel()

#         # Declare the queue
#         self.channel.queue_declare(queue=self.queue_name)

#         # Start consuming messages
#         self.consumer_tag = self.channel.basic_consume(
#             queue=self.queue_name,
#             on_message_callback=self.on_message
#         )

#         # Blocking call to start consuming
#         self.channel.start_consuming()

#     def on_message(self, channel, method, properties, body):
#         # Process the received message
#         print("Received message:", body)

#         # Check if you want to stop consuming
#         if some_condition:
#             self.stop_consuming()

#     def stop_consuming(self):
#         # Cancel the consumption by sending the basic_cancel command
#         self.channel.basic_cancel(consumer_tag=self.consumer_tag)

#         # Close the connection and channel
#         self.channel.close()
#         self.connection.close()

# # Usage
# connection_params = pika.ConnectionParameters('localhost')
# queue_name = 'my_queue'

# consumer_thread = ConsumerThread(connection_params, queue_name)
# consumer_thread.start()

# # ... do some other work ...

# # Stop the consumer thread
# consumer_thread.stop_consuming()
# consumer_thread.join()
