from configparser import ConfigParser
from src.joiner import Joiner
import logging
import os


def initialize_config():
    config = ConfigParser(os.environ)
    # If config.ini does not exists original config object is not modified
    config.read("config.ini")

    config_params = {}
    try:
        config_params["logging_level"] = config.get("DEFAULT", "LOGGING_LEVEL", fallback=None)
        config_params["input_exchange_1"] = config.get("DEFAULT", "INPUT_EXCHANGE_1", fallback=None)
        config_params["input_exchange_type_1"] = config.get("DEFAULT", "INPUT_EXCHANGE_TYPE_1", fallback=None)
        config_params["input_queue_name_2"] = config.get("DEFAULT", "INPUT_QUEUE_NAME_2", fallback=None)
        config_params["output_queue_name"] = config.get("DEFAULT", "OUTPUT_QUEUE_NAME", fallback=None)
        config_params["primary_key"] = config.get("DEFAULT", "PRIMARY_KEY", fallback='')
        config_params["primary_key_2"] = config.get("DEFAULT", "PRIMARY_KEY_2", fallback='')
        config_params["select"] = config.get("DEFAULT", "SELECT", fallback=None)
        config_params["joiner_function"] = config.get("DEFAULT", "JOINER_FUNCTION", fallback='join_func_default')
        config_params["id"] = os.getenv('ID', None)

    except KeyError as e:
        raise KeyError("Key was not found. Error: {} .Aborting packet-distributor".format(e))
    except ValueError as e:
        raise ValueError("Key could not be parsed. Error: {}. Aborting packet-distributor".format(e))

    return config_params


def main():
    config_params = initialize_config()
    logging_level = config_params["logging_level"] 
    input_exchange_1 = config_params["input_exchange_1"]
    input_exchange_type_1 = config_params["input_exchange_type_1"]
    input_queue_name_2 = config_params["input_queue_name_2"] 
    output_queue_name = config_params["output_queue_name"]
    primary_key = config_params["primary_key"]
    primary_key_2 = config_params["primary_key_2"]
    select = config_params["select"]
    joiner_function = config_params["joiner_function"]
    node_id = config_params["id"]

    initialize_log(logging_level)

    # Log config parameters at the beginning of the program to verify the configuration
    # of the component
    logging.debug(f"action: config | result: success | logging_level: {logging_level}")

    try:
        joiner = Joiner(input_exchange_1, input_exchange_type_1, input_queue_name_2, output_queue_name,
                        primary_key, primary_key_2, select, joiner_function, node_id)
        joiner.run()
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
