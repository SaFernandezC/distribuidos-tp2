from configparser import ConfigParser
from src.Filter import Filter
import logging
import os
from dotenv import load_dotenv

load_dotenv()


def initialize_config():
    config = ConfigParser(os.environ)
    # If config.ini does not exists original config object is not modified
    config.read("config.ini")

    config_params = {}
    try:
        config_params["logging_level"] = config.get("DEFAULT", "LOGGING_LEVEL", fallback=None)
        config_params["amount_filters"] = int(config.get("DEFAULT", "AMOUNT_FILTERS", fallback=0))
        config_params["select"] = config.get("DEFAULT", "SELECT", fallback=None)
        config_params["operators"] = config.get("DEFAULT", "OPERATORS", fallback=None)
        config_params["input_queue"] = config.get("DEFAULT", "INPUT_QUEUE", fallback=None)
        config_params["input_exchange"] = config.get("DEFAULT", "INPUT_EXCHANGE", fallback=None)
        config_params["input_exchange_type"] = config.get("DEFAULT", "INPUT_EXCHANGE_TYPE", fallback=None)
        config_params["output_exchange"] = config.get("DEFAULT", "OUTPUT_EXCHANGE", fallback=None)
        config_params["output_exchange_type"] = config.get("DEFAULT", "OUTPUT_EXCHANGE_TYPE", fallback=None)
        config_params["output_queue_name"] = config.get("DEFAULT", "OUTPUT_QUEUE_NAME", fallback=None)
        config_params["id"] = os.getenv('ID', None)

        raw_filters = []
        for i in range(config_params["amount_filters"]):
            raw_filters.append(config.get("DEFAULT", "FILTER_"+str(i)))
        config_params["raw_filters"] = raw_filters

    except KeyError as e:
        raise KeyError("Key was not found. Error: {} .Aborting packet-distributor".format(e))
    except ValueError as e:
        raise ValueError("Key could not be parsed. Error: {}. Aborting packet-distributor".format(e))

    return config_params


def main():
    config_params = initialize_config()
    logging_level = config_params["logging_level"] 
    amount_filters = config_params["amount_filters"]
    select = config_params["select"] 
    operators = config_params["operators"]
    input_queue = config_params["input_queue"]
    input_exchange = config_params["input_exchange"] 
    input_exchange_type = config_params["input_exchange_type"]
    output_exchange = config_params["output_exchange"]
    output_exchange_type = config_params["output_exchange_type"]
    output_queue_name = config_params["output_queue_name"]
    raw_filters = config_params["raw_filters"]
    node_id = config_params["id"]

    initialize_log(logging_level)

    # Log config parameters at the beginning of the program to verify the configuration
    # of the component
    logging.debug(f"action: config | result: success | logging_level: {logging_level}")

    # raw_filters = []
    # for i in range(CANTIDAD):
    #     raw_filters.append(os.getenv('FILTER_'+str(i)))

    try:
        filter = Filter(select, raw_filters, amount_filters, operators, input_exchange, input_exchange_type, input_queue,
                        output_exchange, output_exchange_type, output_queue_name, node_id)
        filter.run()
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
