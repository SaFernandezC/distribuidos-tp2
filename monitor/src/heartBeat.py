
import socket
import threading
import time
import logging
import multiprocessing
from .utils import AtomicValue
import pika
import json

class Sender():
    def __init__(self, channel):
        self.channel = channel
    
    def run(self):
        while True:
            self.channel.basic_publish(exchange='hartbeats', routing_key='heartbeat.request', body=b"ALIVE?")
            time.sleep(5)


class HartBeat:
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq', heartbeat=1800))
        self.channel = self.connection.channel()

        self.channel.exchange_declare(exchange='hartbeats', exchange_type='topic')

        result = self.channel.queue_declare('')
        self.queue_name = result.method.queue

        self.channel.queue_bind(exchange='hartbeats', queue=self.queue_name, routing_key='heartbeat.response')

        self.sender = threading.Thread(target=Sender(self.channel).run).start()


    # Como se cuantos hay
    def callback(self, ch, method, properties, body):
        body = json.loads(body.decode())
        

        print(" [x] %r:%r" % (method.routing_key, body))


    def run(self):
        self.channel.basic_consume(queue=self.queue_name, on_message_callback=self.callback, auto_ack=True)
        self.channel.start_consuming()
  