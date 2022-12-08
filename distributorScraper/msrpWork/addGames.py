#!/usr/bin/env python3

import sys
sys.path.append('..')
import json
import sqlFunctions

def epic():
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()
    cursor.execute("select game_id from MSRP m, GAMES g where g.id = m.game_id and source='Epic Games';")
    results = cursor.fetchall()
    enteredIds = [result[0] for result in results]

    with open("/var/www/html/cse30246/databased/distributorScraper/msrpWork/EpicGamesAdd.json", 'r') as file:
        data = json.load(file)
        data = data["found"]["new"]
        for game in data:
            sqlFunctions.MySQL_insert_into_MSRP(data[game]["gameid"], data[game]["storeLink"], data[game]["initialPrice"], "Epic Games", 1, connection)

def gog():
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()
    cursor.execute("select game_id from MSRP m, GAMES g where g.id = m.game_id and source='GOG';")
    results = cursor.fetchall()
    enteredIds = [result[0] for result in results]

    with open("/var/www/html/cse30246/databased/distributorScraper/msrpWork/GOGGamesAdd.json", 'r') as file:
        data = json.load(file)
        data = data["found"]["new"]
        for game in data:
            if data[game]["gameid"] not in enteredIds:
                sqlFunctions.MySQL_insert_into_MSRP(data[game]["gameid"], data[game]["storeLink"], data[game]["initialPrice"], "GOG", 1, connection)

def steam():
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()
    cursor.execute("select game_id from MSRP m, GAMES g where g.id = m.game_id and source='Steam';")
    results = cursor.fetchall()
    enteredIds = [result[0] for result in results]

    with open("/var/www/html/cse30246/databased/distributorScraper/msrpWork/SteamGamesAddFixed.json", 'r') as file:
        data = json.load(file)
        for game in data:
            if data[game]["gameid"] not in enteredIds and data[game]["storeLink"] != "NA" and data[game]["initialPrice"] != "NA":
                #print(game, data[game]["storeLink"], data[game]["initialPrice"])
                sqlFunctions.MySQL_insert_into_MSRP(data[game]["gameid"], data[game]["storeLink"], data[game]["initialPrice"], "Steam", 1, connection)

def main():
    steam()

if __name__ == "__main__":
    main()