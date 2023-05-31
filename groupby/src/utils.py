def default(group_table):
    return group_table

def find_dup_trips_year(group_table):
    filtered = []
    for estacion, valores in group_table.items():
        if '2017' not in valores: continue
        if '2016' not in valores: continue
        
        if valores['2017'] > valores['2016'] * 2:
            filtered.append((estacion, valores))
        
    return filtered

def find_stations_query_3(group_table):
    filtered = []
    for estacion, valores in group_table.items():
        if valores["distance"] >= 6:
            filtered.append((estacion, valores["distance"]))

    return filtered