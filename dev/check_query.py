CORRECT_QUERY_1 = {"2011-03-05": {'duration_sec': 1667.362707}, "2011-03-09": {'duration_sec': 830.043362}, "2011-04-15": {'duration_sec': 1281.006812}, "2011-08-26": {'duration_sec': 1059.071630}, "2011-09-04": {'duration_sec': 2159.195062}, "2011-09-06": {'duration_sec': 755.645161}, "2011-09-07": {'duration_sec': 706.048371}, "2011-12-06": {'duration_sec': 685.944986}, "2012-02-28": {'duration_sec': 705.341121}, "2012-04-21": {'duration_sec': 1673.907268}, "2012-09-17": {'duration_sec': 723.628415}, "2012-10-28": {'duration_sec': 926.158915}, "2012-12-25": {'duration_sec': 1463.256098}, "2014-06-23": {'duration_sec': 840.952233}, "2014-08-12": {'duration_sec': 789.154234}}

CORRECT_QUERY_2 = [["Bathurst St / Queens Quay W", {"2017": 5512, "2016": 634}], ["Bridgeman Ave / Bathurst St", {"2017": 854, "2016": 390}], ["Fort York Blvd / Garrison Rd", {"2017": 3657, "2016": 1700}], ["King St W / Fraser Ave", {"2017": 929, "2016": 427}], ["King St W / Joe Shuster Way", {"2017": 2414, "2016": 759}], ["Liberty St / Fraser Ave Green P", {"2017": 2054, "2016": 1005}], ["Nelson St / Duncan St", {"2017": 8830, "2016": 1329}], ["Ontario Place Blvd / Remembrance Dr", {"2017": 7245, "2016": 2767}], ["Ossington Ave / College St W", {"2017": 776, "2016": 347}], ["Queen St E / Sackville St", {"2017": 1617, "2016": 747}], ["Queen St W / Gladstone Ave", {"2017": 3703, "2016": 1678}], ["Queens Quay / Yonge St", {"2017": 6760, "2016": 1410}], ["Strachan Ave / Princes' Blvd", {"2017": 3255, "2016": 1601}], ["Wellington St W / Portland St", {"2017": 8786, "2016": 3548}], ["Wellington St W / Stafford St", {"2017": 1927, "2016": 748}]]

CORRECT_QUERY_3 = [["Jacques-Le Ber / de la Pointe Nord", 6.003307], ["Parc Plage", 6.582435], ["de Montmorency / Richardson", 6.435541]]

# [["Jacques-Le Ber / de la Pointe Nord", 6.003307], ["Parc Plage", 6.582435], ["de Montmorency / Richardson", 6.435541]]
# [["Bathurst St / Queens Quay W", {"2017": 5512, "2016": 634}], ["Bridgeman Ave / Bathurst St", {"2017": 854, "2016": 390}], ["Fort York Blvd / Garrison Rd", {"2017": 3657, "2016": 1700}], ["King St W / Fraser Ave", {"2017": 929, "2016": 427}], ["King St W / Joe Shuster Way", {"2017": 2414, "2016": 759}], ["Liberty St / Fraser Ave Green P", {"2017": 2054, "2016": 1005}], ["Nelson St / Duncan St", {"2017": 8830, "2016": 1329}], ["Ontario Place Blvd / Remembrance Dr", {"2017": 7245, "2016": 2767}], ["Ossington Ave / College St W", {"2017": 776, "2016": 347}], ["Queen St E / Sackville St", {"2017": 1617, "2016": 747}], ["Queen St W / Gladstone Ave", {"2017": 3703, "2016": 1678}], ["Queens Quay / Yonge St", {"2017": 6760, "2016": 1410}], ["Strachan Ave / Princes' Blvd", {"2017": 3255, "2016": 1601}], ["Wellington St W / Portland St", {"2017": 8786, "2016": 3548}], ["Wellington St W / Stafford St", {"2017": 1927, "2016": 748}]]

def check_query_1(query_received):
    if len(query_received) != len(CORRECT_QUERY_1):
        return False
    
    for key, value in CORRECT_QUERY_1.items():
        received = query_received.get(key)
        try:
            if int(value["duration_sec"]) != int(received["duration_sec"]):
                return False
        except:
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
                if int(value[1]) != int(expected[1]):
                    return False
                found = True
                break
        if not found:
            return False
    
    return True

def check_queries(query1, query2, query3):
    if not check_query_1(query1):
        print(f"ERROR IN {query1}")
    else:
        print("QUERY 1 OK")

    if not check_query_2(query2):
        print(f"ERROR IN {query2}")
    else:
        print("QUERY 2 OK")
    
    if not check_query_3(query3):
        print(f"ERROR IN {query3}")
    else:
        print("QUERY 3 OK")


def main():
    query1 = {'2014-06-23': {'duration_sec': 840.9522332506203, 'count': 19344, 'sum': 16267380.0}, '2014-08-12': {'duration_sec': 789.1542340281749, 'count': 19237, 'sum': 15180960.0}, '2011-03-05': {'duration_sec': 1667.36270691334, 'count': 2054, 'sum': 3424763.0}, '2011-04-15': {'duration_sec': 1281.0068115471943, 'count': 3083, 'sum': 3949344.0}, '2011-09-04': {'duration_sec': 2159.1950622321974, 'count': 4901, 'sum': 10582215.0}, '2011-09-06': {'duration_sec': 755.6451612903226, 'count': 2666, 'sum': 2014550.0}, '2011-03-09': {'duration_sec': 830.0433618843683, 'count': 1868, 'sum': 1550521.0}, '2011-12-06': {'duration_sec': 685.944986344128, 'count': 2563, 'sum': 1758077.0}, '2011-08-26': {'duration_sec': 1059.071630128066, 'count': 4607, 'sum': 4879143.0}, '2011-09-07': {'duration_sec': 706.0483706720978, 'count': 1964, 'sum': 1386679.0}, '2012-02-28': {'duration_sec': 705.3411214953271, 'count': 428, 'sum': 301886.0}, '2012-04-21': {'duration_sec': 1673.907268170426, 'count': 399, 'sum': 667889.0}, '2012-09-17': {'duration_sec': 723.6284153005464, 'count': 549, 'sum': 397272.0}, '2012-10-28': {'duration_sec': 926.1589147286821, 'count': 258, 'sum': 238949.0}, '2012-12-25': {'duration_sec': 1463.2560975609756, 'count': 82, 'sum': 119987.0}}
    query2 = [['Nelson St / Duncan St', {'2016': 1329, '2017': 8830}], ['Queen St E / Sackville St', {'2016': 747, '2017': 1617}], ['Queen St W / Gladstone Ave', {'2016': 1678, '2017': 3703}], ['Bathurst St / Queens Quay W', {'2016': 634, '2017': 5512}], ['Queens Quay / Yonge St', {'2016': 1410, '2017': 6760}], ['Wellington St W / Portland St', {'2016': 3548, '2017': 8786}], ['Ontario Place Blvd / Remembrance Dr', {'2016': 2767, '2017': 7245}], ['Liberty St / Fraser Ave Green P', {'2016': 1005, '2017': 2054}], ['Wellington St W / Stafford St', {'2016': 748, '2017': 1927}], ['Fort York Blvd / Garrison Rd', {'2016': 1700, '2017': 3657}], ["Strachan Ave / Princes' Blvd", {'2016': 1601, '2017': 3255}], ['King St W / Fraser Ave', {'2016': 427, '2017': 929}], ['King St W / Joe Shuster Way', {'2016': 759, '2017': 2414}], ['Bridgeman Ave / Bathurst St', {'2016': 390, '2017': 854}], ['Ossington Ave / College St W', {'2016': 347, '2017': 776}]]
    query3 = [['Parc Plage', 6.5824350514101235], ['de Montmorency / Richardson', 6.435541312932454], ['Jacques-Le Ber / de la Pointe Nord', 6.00330747952395]]
    check_queries(query1, query2, query3)


if __name__ == "__main__":
    main()
