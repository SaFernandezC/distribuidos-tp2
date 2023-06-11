import logging

class Monitor():
    def __init__(self, node_id, num_nodes, host, port):
        self.node_id = node_id
        self.num_nodes = num_nodes
        self.coordinator = None
        self.election_in_progress = False
        self.host = host
        self.port = port

    