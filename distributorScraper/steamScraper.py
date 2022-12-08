#!/usr/bin/env python3

import sys
import json
import time
import requests
from datetime import datetime
import sqlFunctions

# get game data by id: https://store.steampowered.com/api/appdetails?appids=433340
# for games like ELDEN RING, making all games lowercase

def load_Steam_games(games, msrpCheck = False, dailyPriceCheck = False, debug = False):
    if dailyPriceCheck or msrpCheck: # create connection if inserting data into database
        connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
        # first MSRP insert
        cursor = connection.cursor()
        cursor.execute("select game_id from MSRP where source='Steam';")
        seenGames = {i[0] for i in cursor.fetchall()}
        date = datetime.now()

    # create dictionary to map game names to their ids
    response = requests.get('https://api.steampowered.com/ISteamApps/GetAppList/v0002/?key=F34EBAC622036D4C658B6E4BC5D04B49&format=json')
    ids = {}
    for app in response.json()["applist"]["apps"]:
        if app["name"].strip(): # use valid names (some test games are empty strings)
            ids[app["name"].lower().replace('\u2122', '').replace('\u00ae', '')] = app["appid"]  # convert to lowercase
            ids[app["name"].lower().replace('\u2122', '').replace('\u00ae', '').replace(' - ', ': ')] = app["appid"]
    
    # get prices and links for games in steam library
    for i, game in enumerate(games):
        if msrpCheck:
            Steam_MSRP_entry(game, games, ids, seenGames, connection, debug)
        elif dailyPriceCheck:
            Steam_Price_entry(game, games, date, connection, debug=False)

        if i % 1000 == 0 and debug: print("Progress Update: entry", i, "/", len(games))

def Steam_Price_entry(game_id, games, date, connection, debug=False):
    id = game_id

    try:
        result = requests.get(f"https://store.steampowered.com/api/appdetails?appids={id}&key=F34EBAC622036D4C658B6E4BC5D04B49&format=json").json()[str(id)]
    except:
        if debug: print("Error: request failed, pausing queries for 5 minutes")
        time.sleep(300)
        result = requests.get(f"https://store.steampowered.com/api/appdetails?appids={id}&key=F34EBAC622036D4C658B6E4BC5D04B49&format=json").json()[str(id)]

    if result["success"]:
        data = result["data"]

        if not data["is_free"] and "price_overview" not in data: # entry on Steam by not for sale
            if debug: print("game id (", game_id, ") no longer in store")
            return

        initialPrice = 0 if data["is_free"] else data["price_overview"]["initial"] / 100
        finalPrice = 0 if data["is_free"] else data["price_overview"]["final"] / 100
    
        # insert into Prices table
        sqlFunctions.MySQL_insert_into_PRICES(games[game_id]["msrp_id"], date, finalPrice, connection)

        if debug: print(f"inserting price entry for MSRP {games[game_id]['msrp_id']}: price is now ${finalPrice}")
    else: 
        if debug: print(f"request to {'https://store.steampowered.com/api/appdetails?appids={id}&key=F34EBAC622036D4C658B6E4BC5D04B49&format=json'} unsuccessful")
    

def Steam_MSRP_entry(game, games, ids, seenGames, connection, debug=False):
    if game not in ids: # game provided not on steam
        if debug: print(game, "not found")
        return
    if games[game]["game_id"] in seenGames:
        if debug: print(game, "already in database")
        return

    id = ids[game]
    if debug: print("querying store info for id: ", id)
    try:
        result = requests.get(f"https://store.steampowered.com/api/appdetails?appids={id}&key=F34EBAC622036D4C658B6E4BC5D04B49&format=json").json()[str(id)]
    except:
        if debug: print("Error: request failed, pausing queries for 5 minutes")
        time.sleep(300)
        result = requests.get(f"https://store.steampowered.com/api/appdetails?appids={id}&key=F34EBAC622036D4C658B6E4BC5D04B49&format=json").json()[str(id)]

    if result["success"]:
        data = result["data"]

        if not data["is_free"] and "price_overview" not in data: # entry on Steam by not for sale
            if debug: print(game, "no longer in store")
            return

        initialPrice = 0 if data["is_free"] else data["price_overview"]["initial"] / 100
        finalPrice = 0 if data["is_free"] else data["price_overview"]["final"] / 100
        storeLink = "https://store.steampowered.com/app/" + str(id)

        # insert into MSRP table
        sqlFunctions.MySQL_insert_into_MSRP(games[game]["game_id"], storeLink, initialPrice, "Steam", 1, connection)

        if debug: print(f"{game}: initially ${initialPrice}, now ${finalPrice} at {storeLink}")

def steam_test():
    # example steam price finder
    print("Enter game titles seperated by '/'")
    for line in sys.stdin:
        testGames = {}
        for item in line.rstrip().split('/'):
            testGames[item] = {"game_id": 0, "msrp_id": 0} # imitate games being passed in dictionary {game: game_id}
        load_Steam_games(testGames, debug = True)

def Steam_MSRPs():
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()
    cursor.execute("select id, name from GAMES;")
    results = cursor.fetchall()

    # deal with single quotes and make lower case
    games = {result[1].replace("\\'", "'")[1:-1].lower().replace('\u2122', '').replace('\u00ae', ''):{"game_id": result[0], "msrp_id": 0} for result in results}

    load_Steam_games(games, msrpCheck = True, debug = True)

def Steam_Prices():
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()
    cursor.execute("select MSRP_ID, URL from GAMES, MSRP where id=game_id and source='Steam';")
    results = cursor.fetchall()

    # dictionary formatted {game_id : msrp_id}
    games = {result[1].split('/')[-1]:{"msrp_id": result[0]} for result in results}

    load_Steam_games(games, dailyPriceCheck = True, debug = True)

def main():
    # example steam price finder
    #steam_test()

    # fill MSRP table
    # Steam_MSRPs()

    # fill Prices table
    Steam_Prices()

if __name__ == '__main__':
    main()