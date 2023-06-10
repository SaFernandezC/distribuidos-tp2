import ujson as json

def parse_weathers(item, city):
    item = item.split(',')
    return {"city": city, "date": item[0], "prectot": float(item[1])}

def parse_trips(item, city):
    item = item.split(',')
    return {
        "city": city,
        "start_date": item[0].split(' ')[0], # Viene con tiempo, no lo quiero
        "start_station_code": item[1],
        "end_date": item[2].split(' ')[0], # Viene con tiempo, no lo quiero
        "end_station_code": item[3],
        "duration_sec": float(item[4]) if float(item[4]) >= 0 else 0,
        "yearid": item[-1]
    }
def parse_stations(item, city):
    item = item.split(',')
    return {
        "city": city,
        "code": item[0],
        "name": item[1],
        "latitude": float(item[2]) if item[2] != '' else 0,
        "longitude": float(item[3]) if item[3] != '' else 0,
        "yearid": item[-1],
    }


def def_function(type):
    if type == "weathers":
        return parse_weathers
    elif type == "trips":
        return parse_trips
    else: # Stations
        return parse_stations

def send(queue, batch, client_id):
    city = batch["city"]
    data = batch["data"]
    parser = def_function(batch["type"])

    parsed = []
    for item in data:
        parsed.append(parser(item, city))

    batch = json.dumps({"client_id":client_id, "data":parsed})
    queue.send(batch)
