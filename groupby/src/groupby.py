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

        self.tags_to_ack = []  # [messages]
        self.ids_processed = {}  # {Client_id: [ids]}


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

    def _avg(self, key, item, group_table):
        if key in group_table:
            group_table[key]['count'] = group_table[key]['count'] + 1
            group_table[key]['sum'] = group_table[key]['sum'] + float(item[self.field_to_agregate])
            group_table[key][self.field_to_agregate] = group_table[key]['sum'] / group_table[key]['count']
        else: 
            value = float(item[self.field_to_agregate])
            group_table[key] = {self.field_to_agregate:value, "count": 1, "sum": value}

    def _count(self, key, item, group_table):
        if key in group_table:
            if item[self.field_to_agregate] in group_table[key]:
                group_table[key][item[self.field_to_agregate]] += 1
            else:
                group_table[key][item[self.field_to_agregate]] = 1
        else:
            group_table[key] = {item[self.field_to_agregate]: 1}

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

    def _group(self, client_id, batch):
        if client_id not in self.group_table:
            self.group_table[client_id] = {}

        for item in batch:
            key_dict = self._check_key_len(self.key, item)
            self.agg_function(key_dict, item, self.group_table[client_id])


    # def add_message_id(self, message_id, client_id):
    #     if not self.ids_proccesed[client_id]:
    #         self.ids_processed[client_id] = []

    #     already_added = message_id in self.ids_proccesed[client_id]

    #     if not already_added:
    #         self.ids_proccesed[client_id].append(message_id)

    #     return already_added

    #def ack(self, forced):
        #if len(self.tags_to_ack) > MESSAGES_BATCH or forced:
            # Bajo A Disco group table/ids
            # {
            #     "group_table": self.group_table,
            #     "ids_processed": self.ids_processed,
            # }
            # send_ack
            # self.tags_to_ack = []


    def _callback(self, body):
        batch = json.loads(body.decode())
        client_id = batch["client_id"]

        # message_id = hash(batch)
        # #self.tags_to_ack.append(tag)
        # duplicated = self.add_message_id(self, message_id, client_id)
        # if duplicated:
        #     #self.ack()
        #     return

        if "eof" in batch:
            function = eval(self.send_data_function)
            filtered = function(self.group_table[client_id])
            self.output_queue.send(json.dumps({"client_id": client_id, "query": self.query, "results": filtered}))
        else:
            self._group(client_id, batch["data"])

        # if "clean" in batch or "eof" in batch:
        #     self.ids_processed.pop(client_id, None)
        #     self.group_table.pop(client_id, None)

        # Bajo A Disco group table/ids
        # {
        #     "group_table": self.group_table,
        #     "ids_processed": self.ids_processed,
        # }

        # #self.ack()

    def run(self):
        self.input_queue.receive(self._callback)
        self.connection.start_consuming()
        self.connection.close()
