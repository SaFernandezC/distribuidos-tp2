from common.Connection import Connection
import ujson as json
import signal
import sys
import logging

class DateModifier():
    def __init__(self, input_queue_name, output_exchange, output_exchange_type):

        self.running = True
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        self.connection = Connection()
        self.input_queue = self.connection.Consumer(input_queue_name)
        self.eof_manager = self.connection.EofProducer(output_exchange, output_exchange_type, input_queue_name)
        self.output_queue = self.connection.Publisher(output_exchange, output_exchange_type)

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

    def _callback(self, body):
        batch = json.loads(body.decode())
        if "eof" in batch:
            self.connection.stop_consuming()
            self.eof_manager.send_eof()
        else:
            for item in batch["data"]:
                item['date'] = self._restar_dia(item['date'])
            self.output_queue.send(json.dumps({"data":batch["data"]}))
    
    def run(self):
        self.input_queue.receive(self._callback)
        self.connection.start_consuming()
        self.connection.close()
