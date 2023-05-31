from .utils import compare, apply_operator
from common.Connection import Connection
import ujson as json
import signal
import logging

SIN_FILTROS = 0
SIN_SELECCIONES = 0

class Filter:
    def __init__(self, fields_to_select, raw_filters, amount_filters, operators, input_exchange, input_exchange_type,
                input_queue_name, output_exchange, output_exchange_type, output_queue_name):

        self.fields_to_select = self._parse_fields_to_select(fields_to_select)
        self.amount_filters = amount_filters
        self.filters = self._parse_filters(raw_filters)
        self.operators = self._parse_operators(operators)

        self.running = True
        signal.signal(signal.SIGTERM, self._handle_sigterm)

        self.connection = Connection()
        self.eof_manager = self.connection.EofProducer(output_exchange, output_queue_name, input_queue_name)

        self.input_queue = self.connection.Subscriber(exchange_name=input_exchange, exchange_type=input_exchange_type, queue_name=input_queue_name)

        if output_exchange_type == 'fanout':
            self.output_queue = self.connection.Publisher(output_exchange, output_exchange_type)
        else: self.output_queue = self.connection.Producer(queue_name=output_queue_name)


    def _handle_sigterm(self, *args):
        """
        Handles SIGTERM signal
        """
        logging.info('SIGTERM received - Shutting server down')
        self.connection.close()


    def _parse_fields_to_select(self, fields_list):
        if fields_list:
            return fields_list.split(',')
        else: return None

    def _parse_filters(self, raw_filters):
        filters = []
        for i in range(self.amount_filters):
            filters.append(raw_filters[i].split(','))
        return filters

    def _parse_operators(self, operators):
        if operators and self.amount_filters > 1:
            return operators.split(',')
        else: return None

    def _filter_integer(self, filter, data):
        field = filter[2]
        op = filter[3]
        left = float(filter[4])
        return compare(op, float(data[field]), left)

    def _filter_string(self, filter, data):
        field = filter[2]
        op = filter[3]
        left = filter[4]
        return compare(op, data[field], left)

    def filter(self, filter, data):
        if filter[1] == 'int':
            return self._filter_integer(filter, data)
        else:
            return self._filter_string(filter, data)

    def select(self, row):
        if not self.fields_to_select: return row
        return {key: row[key] for key in self.fields_to_select}

    def apply_logic_operator(self, results):
        size = len(results)
        if size == 1:
            return results[0]
        
        for i in range(len(self.operators)):
            results[i+1] = apply_operator(self.operators[i], results[i], results[i+1])

        return results[i+1]
    
    def run(self):
        self.input_queue.receive(self._callback)
        self.connection.start_consuming()
        self.connection.close()

    def _callback(self, body):
        batch = json.loads(body.decode())
        if "eof" in batch:
            self.connection.stop_consuming()
            self.eof_manager.send_eof()
            print("Recibo eof -> Envio EOF")
        else:
            data = []
            for item in batch["data"]:
                filtered = True
                filter_results = []
                if self.amount_filters != SIN_FILTROS:
                    for filtro in self.filters:
                        filter_results.append(self.filter(filtro, item))

                    filtered = self.apply_logic_operator(filter_results)
                    
                if filtered:
                    data.append(self.select(item))
            self.output_queue.send(json.dumps({"data":data}))