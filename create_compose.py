import argparse
import yaml
import json

ID_IDENTIFICATOR = "NODE_ID_HERE"
BASE_FOLDER = "compose_creater/"
BASE_NODES = ["accepter", "station_parser", "status_controller", "groupby_query_1", "groupby_query_2", "groupby_query_3"]
OTHER_NODES_IDEFNTIFICATOR = "NODES_HERE"
OTHER_MONITORS_IDEFNTIFICATOR = "MONITORS_HERE"



def set_up_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-ft_1',  '--filter_trips_1', type=int, help='defines number of trips filters for query1', default=1)
    parser.add_argument('-ft_2', '--filter_trips_2', type=int, help='defines number of trips filters for query2', default=1)
    parser.add_argument('-ft_3', '--filter_trips_3', type=int, help='defines number of trips filters for query3', default=1)

    parser.add_argument('-fw_1', '--filter_weather_1', type=int, help='defines number of weather filters for query1', default=1)

    parser.add_argument('-fs_2', '--filter_station_2', type=int, help='defines number of station filters for query2', default=1)
    parser.add_argument('-fs_3', '--filter_station_3', type=int, help='defines number of station filters for query3', default=1)

    parser.add_argument('-j_1', '--joiner_1', type=int, help='defines number of joiners for query1', default=1)
    parser.add_argument('-j_2', '--joiner_2', type=int, help='defines number of joiners for query2', default=1)
    parser.add_argument('-j_3', '--joiner_3', type=int, help='defines number of joiners for query3', default=1)

    parser.add_argument('-dm', '--date_modifier', type=int, help='defines number of date modificator nodes for query1', default=1)
    parser.add_argument('-dc', '--dist_calculator', type=int, help='defines number of distance calculator nodes for query3', default=1)

    parser.add_argument('-tp', '--trip_parser', type=int, help='defines number of trip parser nodes', default=1)
    parser.add_argument('-wp', '--weather_parser', type=int, help='defines number of weather parser nodes', default=1)
    parser.add_argument('-sp', '--station_parser', type=int, help='defines number of station parser nodes', default=1)

    parser.add_argument('-mon',  '--monitors', type=int, help='defines number of monitors', default=3)


    args = parser.parse_args()
    return args


def copy_module(docker_file, node_file, node_id):
    docker_f = open(docker_file, "a", encoding="utf-8")
    node_f = open(node_file, "r", encoding="utf-8")

    for line in node_f:
        if line.find(ID_IDENTIFICATOR) >= 0:
            line = line.replace(ID_IDENTIFICATOR, str(node_id))
        docker_f.write(line)

    docker_f.write("\n\n")

    docker_f.close()
    node_f.close()

def add_monitors(docker_file, monitor_base, monitor_id, monitors_amount, nodes_to_check):
    monitors = []
    for i in range(monitors_amount):
        other_id = i+1
        if other_id != monitor_id:
            monitors.append(other_id)

    docker_f = open(docker_file, "a", encoding="utf-8")
    node_f = open(monitor_base, "r", encoding="utf-8")

    for line in node_f:
        if line.find(ID_IDENTIFICATOR) >= 0:
            line = line.replace(ID_IDENTIFICATOR, str(monitor_id))
        if line.find(OTHER_NODES_IDEFNTIFICATOR) >= 0:
            line = line.replace(OTHER_NODES_IDEFNTIFICATOR, str(nodes_to_check))
        if line.find(OTHER_MONITORS_IDEFNTIFICATOR) >= 0:
            line = line.replace(OTHER_MONITORS_IDEFNTIFICATOR, str(monitors))
        docker_f.write(line)

    docker_f.write("\n\n")

    docker_f.close()
    node_f.close()


def create_nodes_list(args):
    nodes = BASE_NODES.copy()
    for i in range(args.trip_parser):
        nodes.append(f"trip_parser_{i+1}")
    for i in range(args.station_parser):
        nodes.append(f"station_parser_{i+1}")
    for i in range(args.weather_parser):
        nodes.append(f"weather_parser_{i+1}")

    for i in range(args.filter_weather_1):
        nodes.append(f"prectot_filter_{i+1}")
    for i in range(args.date_modifier):
        nodes.append(f"date_modifier_{i+1}")
    for i in range(args.filter_trips_1):
        nodes.append(f"filter_trips_query1_{i+1}")
    for i in range(args.joiner_1):
        nodes.append(f"joiner_query_1_{i+1}")

    for i in range(args.filter_trips_2):
        nodes.append(f"filter_trips_year_{i+1}")
    for i in range(args.filter_station_2):
        nodes.append(f"filter_stations_query2_{i+1}")
    for i in range(args.joiner_2):
        nodes.append(f"joiner_query_2_{i+1}")

    for i in range(args.filter_trips_3):
        nodes.append(f"filter_trips_query3_{i+1}")
    for i in range(args.filter_station_3):
        nodes.append(f"filter_stations_query3_{i+1}")
    for i in range(args.joiner_3):
        nodes.append(f"joiner_query_3_{i+1}")
    for i in range(args.dist_calculator):
        nodes.append(f"distance_calculator_{i+1}")

    return nodes

def create_compose(args):
    file_name = "docker-compose-dev2.yaml"
    file = open(file_name, "w", encoding="utf-8")
    file.close()

    copy_module(file_name, BASE_FOLDER+"base.txt", 0)
    nodes = create_nodes_list(args)

    for i in range(args.monitors):
        add_monitors(file_name, BASE_FOLDER+"monitor.txt", i+1, args.monitors, nodes)

    for i in range(args.trip_parser):
        copy_module(file_name, BASE_FOLDER+"trip_parser.txt", i+1)
    for i in range(args.station_parser):
        copy_module(file_name, BASE_FOLDER+"station_parser.txt", i+1)
    for i in range(args.weather_parser):
        copy_module(file_name, BASE_FOLDER+"weather_parser.txt", i+1)

    for i in range(args.filter_weather_1):
        copy_module(file_name, BASE_FOLDER+"prectot_filter.txt", i+1)
    for i in range(args.date_modifier):
        copy_module(file_name, BASE_FOLDER+"date_modifier.txt", i+1)
    for i in range(args.filter_trips_1):
        copy_module(file_name, BASE_FOLDER+"filter_trips_query1.txt", i+1)
    for i in range(args.joiner_1):
        copy_module(file_name, BASE_FOLDER+"joiner_query_1.txt", i+1)

    for i in range(args.filter_trips_2):
        copy_module(file_name, BASE_FOLDER+"filter_trips_year.txt", i+1)
    for i in range(args.filter_station_2):
        copy_module(file_name, BASE_FOLDER+"filter_stations_query2.txt", i+1)
    for i in range(args.joiner_2):
        copy_module(file_name, BASE_FOLDER+"joiner_query_2.txt", i+1)

    for i in range(args.filter_trips_3):
        copy_module(file_name, BASE_FOLDER+"filter_trips_query3.txt", i+1)
    for i in range(args.filter_station_3):
        copy_module(file_name, BASE_FOLDER+"filter_stations_query3.txt", i+1)
    for i in range(args.joiner_3):
        copy_module(file_name, BASE_FOLDER+"joiner_query_3.txt", i+1)
    for i in range(args.dist_calculator):
        copy_module(file_name, BASE_FOLDER+"distance_calculator.txt", i+1)


def create_exchanges_file(args):
    with open("./eof_manager/exchanges.json", "r") as exchanges:
        data = json.load(exchanges)

        data["weathers"]["writing"] = args.weather_parser
        data["weathers"]["queues_binded"]["prectot_filter"]["listening"] = args.filter_weather_1

        data["trips"]["writing"] = args.trip_parser
        data["trips"]["queues_binded"]["filter_trips_query1"]["listening"] = args.filter_trips_1
        data["trips"]["queues_binded"]["filter_trips_year"]["listening"] = args.filter_trips_2
        data["trips"]["queues_binded"]["filter_trips_query3"]["listening"] = args.filter_trips_3

        data["stations"]["writing"] = args.station_parser
        data["stations"]["queues_binded"]["filter_stations_query2"]["listening"] = args.filter_station_2
        data["stations"]["queues_binded"]["filter_stations_query3"]["listening"] = args.filter_station_3

        data["joiner_query_1"]["writing"] = args.date_modifier
        data["joiner_query_2"]["writing"] = args.filter_station_2
        data["joiner_query_3"]["writing"] = args.filter_station_3

        exchanges.close()
        with open("./eof_manager/exchanges.json", "w") as outfile:
            outfile.write(json.dumps(data, indent=4))


def create_queues_file(args):
    with open("./eof_manager/queues.json", "r") as queues:
        data = json.load(queues)

        data["date_modifier"]["writing"] = args.filter_weather_1
        data["date_modifier"]["listening"] = args.date_modifier

        data["joiner_1"]["writing"] = args.filter_trips_1
        data["joiner_1"]["listening"] = args.joiner_1

        data["groupby_query_1"]["writing"] = args.joiner_1
        data["groupby_query_1"]["listening"] = 1

        data["joiner_2"]["writing"] = args.filter_trips_2
        data["joiner_2"]["listening"] = args.joiner_2

        data["groupby_query_2"]["writing"] = args.joiner_2
        data["groupby_query_2"]["listening"] = 1

        data["joiner_3"]["writing"] = args.filter_trips_3
        data["joiner_3"]["listening"] = args.joiner_3

        data["distance_calculator"]["writing"] = args.joiner_3
        data["distance_calculator"]["listening"] = args.dist_calculator

        data["groupby_query_3"]["writing"] = args.dist_calculator
        data["groupby_query_3"]["listening"] = 1

        data["trip"]["writing"] = 1
        data["trip"]["listening"] = args.trip_parser

        data["weather"]["writing"] = 1
        data["weather"]["listening"] = args.weather_parser

        data["station"]["writing"] = 1
        data["station"]["listening"] = args.station_parser

        queues.close()
        with open("./eof_manager/queues.json", "w") as outfile:
            outfile.write(json.dumps(data, indent=4))


def create_eof_config(args):
    create_exchanges_file(args)
    create_queues_file(args)


if __name__ == '__main__':
    try:
        args = set_up_parser()
        create_compose(args)
        create_eof_config(args)
    except (Exception) as e:
        print("Error occurred: {}".format(e))