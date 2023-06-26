from configparser import ConfigParser
from common.client import Client
import json
import logging
import os
import time
import random

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

CORRECT_QUERY_1 = {'2014-06-23': {'duration_sec': 390.0, 'count': 2, 'sum': 780.0}, '2014-08-12': {'duration_sec': 2400.0, 'count': 1, 'sum': 2400.0}, '2015-08-10': {'duration_sec': 3030.0, 'count': 2, 'sum': 6060.0}, '2016-08-15': {'duration_sec': 900.0, 'count': 2, 'sum': 1800.0}, '2016-10-20': {'duration_sec': 1200.0, 'count': 1, 'sum': 1200.0}, '2017-04-30': {'duration_sec': 180.0, 'count': 1, 'sum': 180.0}, '2018-07-24': {'duration_sec': 1420.0, 'count': 3, 'sum': 4260.0}, '2019-10-16': {'duration_sec': 505.0, 'count': 2, 'sum': 1010.0}, '2019-10-30': {'duration_sec': 631.6666666666666, 'count': 3, 'sum': 1895.0}, '2019-09-30': {'duration_sec': 1478.5, 'count': 2, 'sum': 2957.0}, '2011-09-04': {'duration_sec': 1489.0, 'count': 1, 'sum': 1489.0}, '2011-04-15': {'duration_sec': 1210.0, 'count': 1, 'sum': 1210.0}, '2012-10-28': {'duration_sec': 864.0, 'count': 2, 'sum': 1728.0}, '2012-04-21': {'duration_sec': 683.0, 'count': 1, 'sum': 683.0}, '2013-10-10': {'duration_sec': 571.0, 'count': 1, 'sum': 571.0}, '2013-12-28': {'duration_sec': 3688.0, 'count': 1, 'sum': 3688.0}, '2013-07-10': {'duration_sec': 757.0, 'count': 1, 'sum': 757.0}, '2013-06-09': {'duration_sec': 320.0, 'count': 1, 'sum': 320.0}, '2014-04-14': {'duration_sec': 623.0, 'count': 1, 'sum': 623.0}, '2014-04-29': {'duration_sec': 451.0, 'count': 1, 'sum': 451.0}, '2014-11-25': {'duration_sec': 2033.0, 'count': 4, 'sum': 8132.0}, '2014-05-15': {'duration_sec': 615.5, 'count': 2, 'sum': 1231.0}, '2015-06-26': {'duration_sec': 729.5, 'count': 2, 'sum': 1459.0}, '2016-09-27': {'duration_sec': 863.0, 'count': 2, 'sum': 1726.0}, '2017-10-28': {'duration_sec': 874.6666666666666, 'count': 3, 'sum': 2624.0}, '2017-05-04': {'duration_sec': 766.0, 'count': 2, 'sum': 1532.0}, '2017-07-27': {'duration_sec': 251.0, 'count': 1, 'sum': 251.0}, '2018-10-10': {'duration_sec': 869.0, 'count': 4, 'sum': 3476.0}, '2018-06-02': {'duration_sec': 5118.0, 'count': 2, 'sum': 10236.0}, '2018-11-04': {'duration_sec': 3058.0, 'count': 2, 'sum': 6116.0}, '2018-07-20': {'duration_sec': 1325.0, 'count': 3, 'sum': 3975.0}, '2018-09-08': {'duration_sec': 181.0, 'count': 1, 'sum': 181.0}, '2018-12-14': {'duration_sec': 514.0, 'count': 1, 'sum': 514.0}, '2019-03-20': {'duration_sec': 555.0, 'count': 2, 'sum': 1110.0}, '2020-10-11': {'duration_sec': 224.0, 'count': 1, 'sum': 224.0}, '2020-10-28': {'duration_sec': 1724.0, 'count': 1, 'sum': 1724.0}}
CORRECT_QUERY_2 = [['Milton / du Parc', {'2016': 2, '2017': 5}], ['Métro St-Laurent (de Maisonneuve / St-Laurent)', {'2016': 1, '2017': 3}], ['Queen / Wellington', {'2016': 1, '2017': 3}], ['Métro Mont-Royal (Rivard / du Mont-Royal)', {'2016': 2, '2017': 5}], ['du Mont-Royal / Clark', {'2016': 2, '2017': 6}], ['Drolet / Beaubien', {'2016': 1, '2017': 3}], ['Bernard / Jeanne-Mance', {'2016': 1, '2017': 4}], ["Duluth / de l'Esplanade", {'2016': 1, '2017': 3}], ['Métro Charlevoix (Centre / Charlevoix)', {'2016': 1, '2017': 5}], ['de Bullion / du Mont-Royal', {'2016': 1, '2017': 3}], ['Marché Atwater', {'2016': 1, '2017': 3}], ['Marquette / Rachel', {'2016': 1, '2017': 3}], ['Notre-Dame / de la Montagne', {'2016': 1, '2017': 3}], ['University / Prince-Arthur', {'2016': 1, '2017': 4}], ['2nd & G St NE', {'2016': 1, '2017': 3}], ['14th & L St NW', {'2016': 1, '2017': 3}], ['14th & Rhode Island Ave NW', {'2016': 2, '2017': 5}], ['15th & East Capitol St NE', {'2016': 1, '2017': 4}], ['4th St & Madison Dr NW', {'2016': 2, '2017': 6}], ['New Hampshire Ave & 24th St NW', {'2016': 1, '2017': 3}], ["Independence Ave & L'Enfant Plaza SW/DOE", {'2016': 1, '2017': 4}], ['21st & I St NW', {'2016': 1, '2017': 4}], ['8th & O St NW', {'2016': 1, '2017': 4}], ['Thomas Circle', {'2016': 1, '2017': 6}], ['14th & V St NW', {'2016': 1, '2017': 3}], ['New York Ave & 15th St NW', {'2016': 1, '2017': 6}], ['1st & D St SE', {'2016': 1, '2017': 3}], ['Ohio Dr & West Basin Dr SW / MLK & FDR Memorials', {'2016': 1, '2017': 4}], ['15th & K St NW', {'2016': 1, '2017': 3}], ['4th & E St SW', {'2016': 1, '2017': 3}], ['Henry Bacon Dr & Lincoln Memorial Circle NW', {'2016': 1, '2017': 4}]]
CORRECT_QUERY_3 = [['Côte St-Antoine / Royal', 6.670738828948932], ['Cadillac / Sherbrooke', 7.107107455146269], ['François-Perrault / L.-O.-David', 6.264774436327337], ['LaSalle / Godin', 6.53756885740052], ['Valois / Ste-Catherine', 10.86260696181812], ['Marmier', 8.149483960281302], ['de la Pépinière / Pierre-de-Coubertin', 6.105784349330771], ['Drolet / Gounod', 6.119495936971842]]

def check_query_1(query_received):
    if len(query_received) != len(CORRECT_QUERY_1):
        return False
    
    for key, value in CORRECT_QUERY_1.items():
        received = query_received.get(key)
        if len(value) != len(received):
            return False
        if value["duration_sec"] != received["duration_sec"]:
            return False
        if value["count"] != received["count"]:
            return False
        if value["sum"] != received["sum"]:
            return False
    
    return True

def check_query_2(query_received):
    if len(query_received) != len(CORRECT_QUERY_2):
        return False
    
    for value in query_received:
        found = False
        for expected in CORRECT_QUERY_2:
            if value[0] == expected[0]:
                if value[1]["2016"] != expected[1]["2016"]:
                    return False
                if value[1]["2017"] != expected[1]["2017"]:
                    return False
                found = True
                break
        if not found:
            return False
    
    return True

def check_query_3(query_received):
    if len(query_received) != len(CORRECT_QUERY_3):
        return False
    
    for value in query_received:
        found = False
        for expected in CORRECT_QUERY_3:
            if value[0] == expected[0]:
                if value[1] != expected[1]:
                    return False
                found = True
                break
        if not found:
            return False
    
    return True


def check_queries(data):
    logging.info("Data ready")

    if not check_query_1(data["query1"]):
        print(data["query1"])
    else:
        print("QUERY 1 OK")

    if not check_query_2(data["query2"]):
        print(data["query2"])
    else:
        print("QUERY 2 OK")
    
    if not check_query_3(data["query3"]):
        print(data["query3"])
    else:
        print("QUERY 3 OK")


def ask_for_data(client):
    ready = False
    while not ready:
        ready, data = client.ask_results()
        logging.info("Waiting for data")
        time.sleep(2)
    
    check_queries(data)
    # logging.info("Data ready")
    # print("Query1: ", data["query1"])
    # print("*------------------*")
    # print("Query2: ", data["query2"])
    # print("*------------------*")
    # print("Query3: ", data["query3"])

def main():
    config_params = initialize_config()
    logging_level = config_params["logging_level"]
    server_port = config_params["server_port"]
    server_ip = config_params["server_ip"]
    lines_per_batch = config_params["lines_per_batch"]
    id = config_params["id"]

    initialize_log(logging_level)

    # Log config parameters at the beginning of the program to verify the configuration
    # of the component
    logging.info(f"action: config | result: success | server_ip: {server_ip} | "
                  f"server_port: {server_port} | logging_level: {logging_level}")

    # Initialize server and start server loop
    i = 0
    while True and i != 5:
        print("Inicio Nuevo Cliente!")
        while True:
            try:
                time.sleep(id)
                client = Client(server_ip, server_port, lines_per_batch)
                send_data(client)
                ask_for_data(client)
                client.send_finish()
                break
            except Exception as e:
                logging.error("Error: {}".format(e))
                time.sleep(5)
        client.stop()
        time.sleep(10)
        i += 1

if __name__ == "__main__":
    main()