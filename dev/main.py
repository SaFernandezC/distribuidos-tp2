import time
import ujson as json
import random
import subprocess

def main():
    """
        Replico el distance calculator
    """
    containers = ['monitor_2', 'monitor_3', 'eof_manager_1', 'status_controller_1', 'groupby_query_1_1', 'groupby_query_2_1', 'groupby_query_3_1', 'trip_parser_1', 'trip_parser_2', 'station_parser_1', 'station_parser_2', 'weather_parser_1', 'weather_parser_2', 'prectot_filter_1', 'prectot_filter_2', 'date_modifier_1', 'date_modifier_2', 'filter_trips_query1_1', 'filter_trips_query1_2', 'joiner_query_1_1', 'joiner_query_1_2', 'filter_trips_year_1', 'filter_trips_year_2', 'filter_stations_query2_1', 'filter_stations_query2_2', 'joiner_query_2_1', 'joiner_query_2_2', 'filter_trips_query3_1', 'filter_trips_query3_2', 'filter_stations_query3_1', 'filter_stations_query3_2', 'joiner_query_3_1', 'joiner_query_3_2', 'distance_calculator_1', 'distance_calculator_2']

    # client = docker.from_env()

    while True:
        amount = random.randint(1, 3)
        for _i in range(amount):
            to_stop = random.randint(0, len(containers)-1)
            print(f"Stoppeo {containers[to_stop]}")
            name = containers[to_stop]
            subprocess.run(['docker', 'stop', name], check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        time.sleep(10)

if __name__ == "__main__":
    main()
