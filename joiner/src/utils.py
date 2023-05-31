def default(key, item, side_table):
    values = []
    for _i in key:
        values.append(item[_i])

    if tuple(values) in side_table:
        return True, {**item,**side_table[tuple(values)]}

    return False, {}

def join_func_query3(key, item, side_table):

    if (item["start_station_code"],item["yearid"]) in side_table and (item["end_station_code"],item["yearid"]) in side_table:
        start_station = side_table[(item["start_station_code"],item["yearid"])]
        end_station = side_table[(item["end_station_code"],item["yearid"])]
    
        res = {"end_name": end_station["name"], "start_latitude": start_station["latitude"],
                "start_longitude": start_station["longitude"], "end_latitude": end_station["latitude"],
                "end_longitude": end_station["longitude"]}

        return True, res
    return False, {}