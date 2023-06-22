from configparser import ConfigParser
from src.monitor import Monitor
import logging
import os

def initialize_config():
    config = ConfigParser(os.environ)
    # If config.ini does not exists original config object is not modified
    config.read("config.ini")

    config_params = {}
    try:
        config_params["logging_level"] = os.getenv('LOGGING_LEVEL', config["DEFAULT"]["LOGGING_LEVEL"])
        config_params["node_id"] = int(os.getenv('NODE_ID', config["DEFAULT"]["NODE_ID"]))
        config_params["nodes_id"] = os.getenv('NODES_ID', config["DEFAULT"]["NODES_ID"])
        config_params["port"] = int(os.getenv('PORT', config["DEFAULT"]["PORT"]))
        config_params["nodes"]= os.getenv('NODES', [])

    except KeyError as e:
        raise KeyError("Key was not found. Error: {} .Aborting packet-distributor".format(e))
    except ValueError as e:
        raise ValueError("Key could not be parsed. Error: {}. Aborting packet-distributor".format(e))

    return config_params


def main():
    config_params = initialize_config()
    logging_level = config_params["logging_level"] 
    node_id = config_params["node_id"] 
    nodes_id = eval(config_params["nodes_id"])
    port = config_params["port"] 
    nodes = eval(config_params["nodes"])

    initialize_log(logging_level)

    # Log config parameters at the beginning of the program to verify the configuration
    # of the component
    logging.info(f"action: config | result: success | logging_level: {logging_level} | node_id: {node_id} | nodes_id: {nodes_id}")

    try:
        monitor = Monitor(node_id, nodes_id, nodes)
        monitor.run()
    except OSError as e:
        logging.error(f'action: initialize_monitor | result: fail | error: {e}')

def initialize_log(logging_level):
    """
    Python custom logging initialization

    Current timestamp is added to be able to identify in docker
    compose logs the date when the log has arrived
    """
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging_level,
        datefmt='%Y-%m-%d %H:%M:%S',
    )


if __name__ == "__main__":
    main()
