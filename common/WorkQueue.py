import logging

class WorkQueue():
    def __init__(self, channel, queue_name):
        try:
            self.channel = channel
            self.queue = channel.queue_declare(queue=queue_name, durable=True)
            self.queue_name = self.queue.method.queue
            self.user_callback = None
        except Exception as e:
            logging.error(f"Work Queue: Error creating queue {e}")

    def receive(self, callback):
        try:
            self.user_callback = callback
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(queue=self.queue_name, on_message_callback=self._callback, auto_ack=False)
        except Exception as e:
            logging.error(f"Work Queue: Error receiving message {e}")

    def _callback(self, ch, method, properties, body):
        try:
            self.user_callback(body)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logging.error(f"Work Queue: Error on callback {e}")


    # def send_ack(self, ack_list):
    #     self.channel.basic_ack(delivery_tag=ack_list)

    def send(self, message):
        try:
            self.channel.basic_publish(exchange='',
                        routing_key=self.queue_name,
                        body=message)
        except Exception as e:
            logging.error(f"Work Queue: Error sending message {e}")