from common.Connection import Connection
import ujson as json
import signal
import sys
import logging
from common.HeartBeater import HeartBeater

class DateModifier():
    def __init__(self, input_queue_name, output_exchange, output_exchange_type, node_id):
        self.node_id = node_id
        self.running = True
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        self.connection = Connection()
        self.input_queue = self.connection.Consumer(input_queue_name)
        self.eof_manager = self.connection.EofProducer(output_exchange, output_exchange_type, node_id)
        self.output_queue = self.connection.Publisher(output_exchange, output_exchange_type)
        self.hearbeater = HeartBeater(self.connection, node_id)

    def _handle_sigterm(self, *args):
        """
        Handles SIGTERM signal
        """
        logging.info('SIGTERM received - Shutting server down')
        self.connection.close()
        
    def _restar_dia(self, fecha):
        # Convertir la fecha en una tupla de tres elementos
        anio, mes, dia = map(int, fecha.split('-'))

        # Restar un día al día
        dia = dia - 1

        # Ajustar los valores de los otros elementos de la tupla si es necesario
        if dia == 0:
            mes = mes - 1
            if mes == 0:
                anio = anio - 1
                mes = 12
            dia = self._dias_en_mes(mes, anio)

        # Convertir la tupla de vuelta a una cadena de fecha
        nueva_fecha = f'{anio:04d}-{mes:02d}-{dia:02d}'
        return nueva_fecha

    def _dias_en_mes(self, mes, anio):
        if mes in [1, 3, 5, 7, 8, 10, 12]:
            return 31
        elif mes == 2:
            if self._es_bisiesto(anio):
                return 29
            else:
                return 28
        else:
            return 30

    def _es_bisiesto(self, anio):
        if anio % 4 == 0:
            if anio % 100 == 0:
                if anio % 400 == 0:
                    return True
                else:
                    return False
            else:
                return True
        else:
            return False
    
    def handle_eof(self, body, batch):
        client_id = batch["client_id"]
        if "eof" in batch:
            msg_type = "eof"
        elif "clean" in batch:
            msg_type = "clean"
        else:
            return False

        if batch["dst"] == self.node_id:
            self.eof_manager.send_eof(client_id, msg_type=msg_type)
        else:
            self.input_queue.send(body)
        
        return True

    def _callback(self, body, ack_tag):
        batch = json.loads(body.decode())
        client_id = batch["client_id"]
        eof = self.handle_eof(body, batch)
        if not eof:
            for item in batch["data"]:
                item['date'] = self._restar_dia(item['date'])
            self.output_queue.send(json.dumps({"client_id": client_id, "data":batch["data"]}))
        self.input_queue.ack(ack_tag)

    def run(self):
        self.hearbeater.start()
        self.input_queue.receive(self._callback)
        self.connection.start_consuming()
        self.connection.close()
