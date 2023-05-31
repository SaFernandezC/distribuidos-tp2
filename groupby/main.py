from configparser import ConfigParser
from src.groupby import Groupby
import logging
import os


def initialize_config():
    config = ConfigParser(os.environ)
    # If config.ini does not exists original config object is not modified
    config.read("config.ini")

    config_params = {}
    try:
        config_params["logging_level"] = config.get("DEFAULT", "LOGGING_LEVEL", fallback=None)
        config_params["input_queue_name"] = config.get("DEFAULT", "INPUT_QUEUE_NAME", fallback=None)
        config_params["output_queue_name"] = config.get("DEFAULT", "OUTPUT_QUEUE_NAME", fallback=None)
        config_params["query"] = config.get("DEFAULT", "QUERY", fallback=None)
        config_params["primary_key"] = config.get("DEFAULT", "PRIMARY_KEY", fallback=None)
        config_params["agg"] = config.get("DEFAULT", "AGG", fallback=None)
        config_params["field_to_agregate"] = config.get("DEFAULT", "FIELD_TO_AGREGATE", fallback=None)
        config_params["send_data_function"] = config.get("DEFAULT", "SEND_DATA_FUNCTION", fallback='default')

    except KeyError as e:
        raise KeyError("Key was not found. Error: {} .Aborting packet-distributor".format(e))
    except ValueError as e:
        raise ValueError("Key could not be parsed. Error: {}. Aborting packet-distributor".format(e))

    return config_params


def main():
    config_params = initialize_config()
    logging_level = config_params["logging_level"] 
    input_queue_name = config_params["input_queue_name"]
    output_queue_name = config_params["output_queue_name"]
    query = config_params["query"] 
    primary_key = config_params["primary_key"]
    agg = config_params["agg"]
    field_to_agregate = config_params["field_to_agregate"]
    send_data_function = config_params["send_data_function"]

    initialize_log(logging_level)

    # Log config parameters at the beginning of the program to verify the configuration
    # of the component
    logging.debug(f"action: config | result: success | logging_level: {logging_level}")

    try:
        groupby = Groupby(input_queue_name, output_queue_name, query, primary_key, agg, field_to_agregate, send_data_function)
        groupby.run()
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
