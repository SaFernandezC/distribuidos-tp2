from configparser import ConfigParser
from src.parser import Parser
import logging
import os

def initialize_config():
    config = ConfigParser(os.environ)
    # If config.ini does not exists original config object is not modified
    config.read("config.ini")

    config_params = {}
    try:
        config_params["logging_level"] = config.get("DEFAULT", "LOGGING_LEVEL", fallback=None)
        config_params["input_queue"] = config.get("DEFAULT", "INPUT_QUEUE", fallback=None)
        config_params["routing_key"] = config.get("DEFAULT", "ROUTING_KEY", fallback=None)
        config_params["output_exchange"] = config.get("DEFAULT", "OUTPUT_EXCHANGE", fallback=None)
        config_params["output_exchange_type"] = config.get("DEFAULT", "OUTPUT_EXCHANGE_TYPE", fallback=None)

    except KeyError as e:
        raise KeyError("Key was not found. Error: {} .Aborting packet-distributor".format(e))
    except ValueError as e:
        raise ValueError("Key could not be parsed. Error: {}. Aborting packet-distributor".format(e))

    return config_params


def main():
    config_params = initialize_config()
    logging_level = config_params["logging_level"] 
    input_queue = config_params["input_queue"]
    routing_key = config_params["routing_key"] 
    output_exchange = config_params["output_exchange"]
    output_exchange_type = config_params["output_exchange_type"]


    initialize_log(logging_level)

    # Log config parameters at the beginning of the program to verify the configuration
    # of the component
    logging.debug(f"action: config | result: success | logging_level: {logging_level}")

    try:
        parser = Parser(input_queue, routing_key, output_exchange, output_exchange_type)
        parser.run()
    except OSError as e:
        logging.error(f'action: initialize_distance_calculator | result: fail | error: {e}')

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
