import json
import logging

INT_LENGTH = 4

class EofQueue():
    def __init__(self, channel, output_exchange, output_queue, input_queue):
        try:
            self.channel = channel
            self.output_exchange = output_exchange
            self.output_queue = output_queue
            self.input_queue = input_queue
            self.user_callback = None

            self.queue = channel.queue_declare(queue='eof_manager', durable=True)
            self.queue_name = self.queue.method.queue

            if not output_exchange:
                self.eof_msg = {"type":"work_queue", "queue": output_queue}
            else:
                self.eof_msg = {"type":"exchange", "exchange": output_exchange}
        except Exception as e:
            logging.error(f"Eof Queue: Error creating queue {e}")

    def receive(self, callback):
        try:
            self.user_callback = callback
            self.channel.basic_qos(prefetch_count=1)
            self.channel.basic_consume(queue=self.queue_name, on_message_callback=self._callback, auto_ack=False)
        except Exception as e:
            logging.error(f"Eof Queue: Error receiving messages {e}")

    def _callback(self, ch, method, properties, body):
        try:
            self.user_callback(body)
            ch.basic_ack(delivery_tag=method.delivery_tag)
        except Exception as e:
            logging.error(f"Eof Queue: Error on callback {e}")

    def send_eof(self, client_id, msg=None):
        try:
            if not msg:
                msg = self.eof_msg
            
            msg["client_id"] = client_id
            self.channel.basic_publish(exchange='',
                        routing_key=self.queue_name,
                        body=json.dumps(msg))
        except Exception as e:
            logging.error(f"Eof Queue: Error sending eof {e}")