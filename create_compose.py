import argparse
import yaml
import json

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


    args = parser.parse_args()
    return args


def create_compose(args):

    env_vars = ["TRIP_PARSERS=", "WEATHER_PARSERS=", "STATION_PARSERS="]

    with open("docker-compose-dev.yaml", 'r') as file:
        data = yaml.safe_load(file)

        data["services"]["trip_parser"]["deploy"]["replicas"] = args.trip_parser
        data["services"]["station_parser"]["deploy"]["replicas"] = args.station_parser
        data["services"]["weather_parser"]["deploy"]["replicas"] = args.weather_parser

        data["services"]["prectot_filter"]["deploy"]["replicas"] = args.filter_weather_1
        data["services"]["date_modifier"]["deploy"]["replicas"] = args.date_modifier
        data["services"]["filter_trips_query1"]["deploy"]["replicas"] = args.filter_trips_1
        data["services"]["joiner_query_1"]["deploy"]["replicas"] = args.joiner_1

        data["services"]["filter_trips_year"]["deploy"]["replicas"] = args.filter_trips_2
        data["services"]["filter_stations_query2"]["deploy"]["replicas"] = args.filter_station_2
        data["services"]["joiner_query_2"]["deploy"]["replicas"] = args.joiner_2

        data["services"]["filter_trips_query3"]["deploy"]["replicas"] = args.filter_trips_3
        data["services"]["filter_stations_query3"]["deploy"]["replicas"] = args.filter_station_3
        data["services"]["joiner_query_3"]["deploy"]["replicas"] = args.joiner_3
        data["services"]["distance_calculator"]["deploy"]["replicas"] = args.dist_calculator

        file.close()
        with open('docker-compose-dev.yaml', 'w') as outfile:
            yaml.dump(data, outfile, default_flow_style=False)

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