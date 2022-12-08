#!/usr/bin/env python3

import sys
import json
import requests
from datetime import datetime
import sqlFunctions

# get game price by id: https://api.gog.com/products/{id}/prices?countryCode=US
# set currency to USD: https://embed.gog.com/user/changeCurrency/USD
# get user info: https://embed.gog.com/userData.json
# get all games: https://api.gog.com//v2//games?locale=en-US&page=1&limit=200
  # must iterate through all pages

def load_GOG_games(games, msrpCheck = False, dailyPriceCheck = False, debug = False):
    if dailyPriceCheck or msrpCheck: # create connection if inserting data into database
        date = datetime.now()
        connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
        # for first MSRP insert
        cursor = connection.cursor()
        cursor.execute("select game_id from MSRP where source='GOG';")
        seenGames = {i[0] for i in cursor.fetchall()}
        
    
    result = requests.get("https://api.gog.com//v2//games?locale=en-US&page=1&limit=200").json() # first page of GOG web api
    currPage = result["page"]
    pages = result["pages"]

    while currPage <= pages:
        if debug: print("current page:", currPage)
        results = result["_embedded"]["items"]

        for game in results:
            if msrpCheck:
                GOG_MSRP_entry(game, games, seenGames, connection, debug)
            if dailyPriceCheck:
                GOG_Price_entry(game, games, date, connection, debug)

        if currPage < pages: # go to next page if more available
            result = requests.get(result["_links"]["next"]["href"]).json()
            currPage = result["page"]
        else: break

def GOG_Price_entry(game, games, date, connection, debug=False):
    storeLink = game["_links"]["store"]["href"]
    if storeLink in games:
        entry = game["_embedded"]["product"]

        if entry["isAvailableForSale"]:
            pricePage = requests.get(entry["_links"]["prices"]["href"].replace("{country}", "US")).json()
            initialPrice = int(pricePage["_embedded"]["prices"][0]["basePrice"].split()[0]) / 100
            finalPrice = int(pricePage["_embedded"]["prices"][0]["finalPrice"].split()[0]) / 100

            # insert into MSRP table
            sqlFunctions.MySQL_insert_into_PRICES(games[storeLink]["msrp_id"], date, finalPrice, connection)

            if debug: print(f"inserting price entry for MSRP {games[storeLink]['msrp_id']}: price is now ${finalPrice}")
        else:
            if debug: print(f"game at {storeLink} (title={entry['title']}) no longer in store") # entry on GOG but not for sale

def GOG_MSRP_entry(game, games, seenGames, connection, debug=False):
    storeLink = game["_links"]["store"]["href"]
    entry = game["_embedded"]["product"]
    title = entry["title"].lower().replace('\u2122', '').replace('\u00ae', '')
    title2 = entry["title"].lower().replace('\u2122', '').replace('\u00ae', '').replace(' - ', ': ')

    if (title in games or title2 in games) and games[title]["game_id"] not in seenGames:
        if entry["isAvailableForSale"]:
            pricePage = requests.get(entry["_links"]["prices"]["href"].replace("{country}", "US")).json()
            initialPrice = int(pricePage["_embedded"]["prices"][0]["basePrice"].split()[0]) / 100
            finalPrice = int(pricePage["_embedded"]["prices"][0]["finalPrice"].split()[0]) / 100
            
            # insert into MSRP table
            sqlFunctions.MySQL_insert_into_MSRP(games[title]["game_id"], storeLink, initialPrice, "GOG", 1, connection)

            if debug: print(f"{title}: initially ${initialPrice}, now ${finalPrice} at {storeLink}")
        else:
            if debug: print(title, "no longer in store") # entry on GOG but not for sale

def GOG_test():
    # example GOG price finder
    print("Enter game titles seperated by '/'")
    for line in sys.stdin:
        testGames = {}
        for item in line.rstrip().split('/'):
            testGames[item] = {"game_id": 0, "msrp_id": 0, "url": ""} # imitate games being passed in dictionary {game: game_id}
        load_GOG_games(testGames, debug = True)

def GOG_MSRPs():
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()
    cursor.execute("select id, name from GAMES;")
    results = cursor.fetchall()

    # deal with single quotes and make lower case
    games = {result[1].replace("\\'", "'")[1:-1].lower().replace('\u2122', '').replace('\u00ae', ''):{"game_id": result[0]} for result in results}
    
    load_GOG_games(games, msrpCheck = True, debug = True)

def GOG_Prices():
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()
    cursor.execute("select MSRP_ID, URL from GAMES, MSRP where id=game_id and source='GOG';")
    results = cursor.fetchall()

    # dictionary formatted {url : msrp_id}
    games = {result[1]:{"msrp_id": result[0]} for result in results}
    
    load_GOG_games(games, dailyPriceCheck = True, debug = True)

def main():
    # example GOG price finder
    # GOG_test()
    
    # fill MSRP table
    # GOG_MSRPs()

    # fill PRICES table
    GOG_Prices()

if __name__ == '__main__':
    main()