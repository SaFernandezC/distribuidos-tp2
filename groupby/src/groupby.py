from common.Connection import Connection
import ujson as json
from .utils import default, find_dup_trips_year, find_stations_query_3
import signal
import logging

class Groupby:

    def __init__(self, input_queue_name, output_queue_name, query, primary_key, agg, field_to_agregate, send_data_function):
        
        self.running = True
        signal.signal(signal.SIGTERM, self._handle_sigterm)
        
        self.key = self._parse_key(primary_key)
        self.agg_function = self._define_agg(agg)
        self.field_to_agregate = field_to_agregate
        self.send_data_function = send_data_function
        self.query = query

        self.connection = Connection()
        self.input_queue = self.connection.Consumer(input_queue_name)
        self.output_queue = self.connection.Producer(output_queue_name)

        self.group_table = {}

    def _handle_sigterm(self, *args):
        """
        Handles SIGTERM signal
        """
        logging.info('SIGTERM received - Shutting server down')
        self.connection.close()

    def _parse_key(self, key):
        return key.split(',')

    def _sum(self):
        return 0

    def _avg(self, key, item):
        if key in self.group_table:
            self.group_table[key]['count'] = self.group_table[key]['count'] + 1
            self.group_table[key]['sum'] = self.group_table[key]['sum'] + float(item[self.field_to_agregate])
            self.group_table[key][self.field_to_agregate] = self.group_table[key]['sum'] / self.group_table[key]['count']
        else: 
            value = float(item[self.field_to_agregate])
            self.group_table[key] = {self.field_to_agregate:value, "count": 1, "sum": value}

    def _count(self, key, item):
        if key in self.group_table:
            if item[self.field_to_agregate] in self.group_table[key]:
                self.group_table[key][item[self.field_to_agregate]] += 1
            else:
                self.group_table[key][item[self.field_to_agregate]] = 1
        else:
            self.group_table[key] = {item[self.field_to_agregate]: 1}

    def _define_agg(self, agg):
        if agg == 'avg':
            return self._avg
        elif agg == 'sum':
            return self._sum
        else: return self._count

    def _check_key_len(self, key, item):
        values = []
        for _i in key:
            values.append(item[_i])

        if len(values) == 1:
            return values[0]
        return tuple(values)

    def _group(self, item):
        key_dict = self._check_key_len(self.key, item)
        self.agg_function(key_dict, item)

    def _callback(self, body):
        batch = json.loads(body.decode())
        if "eof" in batch:
            self.connection.stop_consuming()
            function = eval(self.send_data_function)
            filtered = function(self.group_table)
            self.output_queue.send(json.dumps({"query": self.query, "results": filtered}))
        else:
            for line in batch["data"]:
                self._group(line)

    def run(self):
        self.input_queue.receive(self._callback)
        self.connection.start_consuming()
        self.connection.close()
