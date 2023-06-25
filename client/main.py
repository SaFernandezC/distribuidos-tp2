from configparser import ConfigParser
from common.client import Client
import logging
import os
import time

def initialize_config():
    config = ConfigParser(os.environ)
    config.read("config.ini")

    config_params = {}
    try:
        config_params["server_ip"] = os.getenv('SERVER_IP', config["DEFAULT"]["SERVER_IP"])
        config_params["server_port"] = int(os.getenv('SERVER_PORT', config["DEFAULT"]["SERVER_PORT"]))
        config_params["logging_level"] = os.getenv('LOGGING_LEVEL', config["DEFAULT"]["LOGGING_LEVEL"])
        config_params["lines_per_batch"] = int(os.getenv('LINES_PER_BATCH', config["DEFAULT"]["LINES_PER_BATCH"]))

    except KeyError as e:
        raise KeyError("Key was not found. Error: {} .Aborting server".format(e))
    except ValueError as e:
        raise ValueError("Key could not be parsed. Error: {}. Aborting server".format(e))

    return config_params

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

def send_data(client):
    weathers = {
        "montreal": "./data/montreal/weather.csv",
        "toronto": "./data/toronto/weather.csv",
        "washington": "./data/washington/weather.csv"
    }

    client.send_weathers(weathers)

    stations = {
        "montreal": "./data/montreal/stations.csv",
        "toronto": "./data/toronto/stations.csv",
        "washington": "./data/washington/stations.csv"
    }
    client.send_stations(stations)
    
    trips = {
        "montreal": "./data/montreal/reduced_trips_montreal.csv",
        "toronto": "./data/toronto/reduced_trips_toronto.csv",
        "washington": "./data/washington/reduced_trips_washington.csv"
    }
    client.send_trips(trips)
            


def ask_for_data(client):
    ready = False
    while not ready:
        ready, data = client.ask_results()
        logging.info("Waiting for data")
        time.sleep(5)
    
    if data is not None:
        logging.info("Data ready")
        print("Query1: ", data["query1"])
        print("*------------------*")
        print("Query2: ", data["query2"])
        print("*------------------*")
        print("Query3: ", data["query3"])

def main():
    config_params = initialize_config()
    logging_level = config_params["logging_level"]
    server_port = config_params["server_port"]
    server_ip = config_params["server_ip"]
    lines_per_batch = config_params["lines_per_batch"]

    initialize_log(logging_level)

    # Log config parameters at the beginning of the program to verify the configuration
    # of the component
    logging.info(f"action: config | result: success | server_ip: {server_ip} | "
                  f"server_port: {server_port} | logging_level: {logging_level}")

    # Initialize server and start server loop
    while True:
        try:
            logging.info("Connecting to server")
            client = Client(server_ip, server_port, lines_per_batch)
            client.send_status()
            send_data(client)
            ask_for_data(client)
            client.send_finish()
            break
        except Exception as e:
            logging.error("Error: {}".format(e))
            time.sleep(5)


if __name__ == "__main__":
    main()