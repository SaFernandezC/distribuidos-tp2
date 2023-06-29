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
        if len(value) != len(received):
            return False
        try:
            if int(value["duration_sec"]) != int(received["duration_sec"]):
                return False
        except:
            return False
        # if value["count"] != received["count"]:
        #     return False
        # if value["sum"] != received["sum"]:
        #     return False
    
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
    query1 = {}
    query2 = {}
    query3 = {}
    check_queries(query1, query2, query3)


if __name__ == "__main__":
    main()
