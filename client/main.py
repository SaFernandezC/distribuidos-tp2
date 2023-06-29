from configparser import ConfigParser
from common.client import Client
import logging
import os
import time

WEATHERS = {
    "montreal": "./data/montreal/weather.csv",
    "toronto": "./data/toronto/weather.csv",
    "washington": "./data/washington/weather.csv"
}

STATIONS = {
    "montreal": "./data/montreal/stations.csv",
    "toronto": "./data/toronto/stations.csv",
    "washington": "./data/washington/stations.csv"
}


TRIPS = {
    "montreal": "./data/montreal_old/trips.csv",
    "toronto": "./data/toronto_old/trips.csv",
    "washington": "./data/washington_old/trips.csv"
}

def initialize_config():
    config = ConfigParser(os.environ)
    config.read("config.ini")

    config_params = {}
    try:
        config_params["server_ip"] = os.getenv('SERVER_IP', config["DEFAULT"]["SERVER_IP"])
        config_params["server_port"] = int(os.getenv('SERVER_PORT', config["DEFAULT"]["SERVER_PORT"]))
        config_params["logging_level"] = os.getenv('LOGGING_LEVEL', config["DEFAULT"]["LOGGING_LEVEL"])
        config_params["lines_per_batch"] = int(os.getenv('LINES_PER_BATCH', config["DEFAULT"]["LINES_PER_BATCH"]))
        config_params["id"] = int(os.getenv('ID', config["DEFAULT"]["ID"]))
        config_params["cities"] = os.getenv('CITIES', config["DEFAULT"]["CITIES"])

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

def send_data(client, cities):
    weathers = {}
    stations = {}
    trips = {}
    for city in cities:
        weathers.update({city: WEATHERS[city]})    
        stations.update({city: STATIONS[city]})
        trips.update({city: TRIPS[city]})
    
    client.send_weathers(weathers)
    client.send_stations(stations)
    client.send_trips(trips)

def ask_for_data(client):
    ready = False
    while not ready:
        ready, data = client.ask_results()
        logging.info("Waiting for data")
        time.sleep(10)
    
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
    id = config_params["id"]
    cities = eval(config_params["cities"])

    initialize_log(logging_level)

    # Log config parameters at the beginning of the program to verify the configuration
    # of the component
    logging.info(f"action: config | result: success | server_ip: {server_ip} | "
                  f"server_port: {server_port} | logging_level: {logging_level}")

    # Initialize server and start server loop

    print(f"Inicio Nuevo Cliente! [{id}]")
    while True:
        try:
            # time.sleep(id)
            client = Client(server_ip, server_port, lines_per_batch)
            send_data(client, cities)
            ask_for_data(client)
            client.send_finish()
            break
        except Exception as e:
            logging.error("Error: {} - Intento reconexion".format(e))
            break
            time.sleep(5)
    client.stop()

if __name__ == "__main__":
    main()