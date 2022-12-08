#!/usr/bin/env python3

import sys
import json
import requests
from epicstore_api import EpicGamesStoreAPI
from datetime import datetime
import sqlFunctions

def get_EpicGames_games(start: int):
    api = EpicGamesStoreAPI()
    date = datetime.now()
    dateRange = date.strftime('[1958-10-16T14:02:36.304Z,%Y-%m-%dT14:02:36.304Z]')

    games = api.fetch_store_games(
        product_type='games/edition/base|bundles/games|editors',
        # Default filter in store page.
        count=1000,
        sort_by='releaseDate',
        sort_dir='DESC',
        release_date=dateRange,
        with_price=True,
        start=start
    )

    return games["data"]["Catalog"]["searchStore"]

def load_EpicGames_games(games, msrpCheck = False, dailyPriceCheck = False, debug = False):
    if dailyPriceCheck or msrpCheck: # create connection if inserting data into database
        date = datetime.now()
        connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
        # for first MSRP insert
        cursor = connection.cursor()
        cursor.execute("select game_id from MSRP where source='Epic Games';")
        seenGames = {i[0] for i in cursor.fetchall()}

    start = 0
    while True:
        if debug: print("current page:", start//1000 + 1)
        results = get_EpicGames_games(start)

        for game in results["elements"]:
            if msrpCheck:
                EpicGames_MSRP_entry(game, games, seenGames, connection, debug)
            if dailyPriceCheck:
                EpicGames_Price_entry(game, games, date, connection, debug)

        lastPage = ((start + 1000) > results["paging"]["total"])
        if lastPage: break
        start += 1000

def EpicGames_Price_entry(game, games, date, connection, debug=False):
    productSlug = game["productSlug"]
    title = game['title'].lower().replace('\u2122', '').replace('\u00ae', '')
    if not productSlug: # unable to get store link for game (productSlug = null)
        if debug: print(f"title {title} has invalid productSlug {productSlug}")
        return
    productSlug = productSlug.replace("/home", "").strip()
    storeLink = "https://store.epicgames.com/en-US/p/" + productSlug

    if productSlug in games:
        initialPrice = game["price"]["totalPrice"]["originalPrice"] / 100
        finalPrice = game["price"]["totalPrice"]["discountPrice"] / 100

        # insert into PRICES table
        sqlFunctions.MySQL_insert_into_PRICES(games[productSlug]["msrp_id"], date, finalPrice, connection)

        if debug: print(f"inserting price entry for MSRP {games[productSlug]['msrp_id']}: price is now ${finalPrice}")
    else:
        if debug: print(f"game at {storeLink} (title={title}) no longer in store") # entry on Epic Games but not for sale

def EpicGames_MSRP_entry(game, games, seenGames, connection, debug=False):
    title = game["title"].lower().replace('\u2122', '').replace('\u00ae', '')
    title2 = game["title"].lower().replace('\u2122', '').replace('\u00ae', '').replace(' - ', ': ')

    if (title in games and games[title]["game_id"] not in seenGames) or (title2 in games and games[title2]["game_id"] not in seenGames):
        productSlug = game["productSlug"].strip()
        if not productSlug: # unable to get store link for game (productSlug = null)
            if debug: print(f"title {title} has invalid productSlug {productSlug}")
            return
        if productSlug.endswith("/home"): # strip '/home' from end of valid productSlugs (end of links)
            productSlug = productSlug.replace("/home", "")

        storeLink = "https://store.epicgames.com/en-US/p/" + productSlug
        initialPrice = game["price"]["totalPrice"]["originalPrice"] / 100
        finalPrice = game["price"]["totalPrice"]["discountPrice"] / 100

        # insert into MSRP table
        sqlFunctions.MySQL_insert_into_MSRP(games[title]["game_id"], storeLink, initialPrice, "Epic Games", 1, connection)

        if debug: print(f"{title}: initially ${initialPrice}, now ${finalPrice} at {storeLink}")
    if title not in games:
        print("no", title)

def api_test():
    # test to get first page of api
    api = EpicGamesStoreAPI()
    games = api.fetch_store_games(
        product_type='games/edition/base|bundles/games|editors',
        # Default filter in store page.
        count=1000,
        sort_by='releaseDate',
        sort_dir='ASC',
        release_date=datetime.now().strftime('[1958-10-16T14:02:36.304Z,%Y-%m-%dT14:02:36.304Z]'),
        with_price=True,
        start=0
    )
    with open("EpicOutput2.json", "w") as outfile:
        outfile.write(json.dumps(games, indent=4))

def EpicGames_test():
    # example Epic Games price finder
    print("Enter game titles seperated by '/'")
    for line in sys.stdin:
        testGames = {}
        for item in line.rstrip().split('/'):
            testGames[item] = {"game_id": 0, "msrp_id": 0} # imitate games being passed in dictionary {game: game_id}
        load_EpicGames_games(testGames, debug = True)

def EpicGames_MSRPs():
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()
    cursor.execute("select id, name from GAMES;")
    results = cursor.fetchall()

    # deal with single quotes and make lower case
    games = {result[1].replace("\\'", "'")[1:-1].lower().replace('\u2122', '').replace('\u00ae', ''):{"game_id": result[0]} for result in results}
    
    load_EpicGames_games(games, msrpCheck = True, debug = True)

def EpicGames_Prices():
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()
    cursor.execute("select MSRP_ID, URL from GAMES, MSRP where id=game_id and source='Epic Games';")
    results = cursor.fetchall()

    # dictionary formatted {productSlug : msrp_id}
    games = {result[1].split('/')[-1]:{"msrp_id": result[0]} for result in results}
    
    load_EpicGames_games(games, dailyPriceCheck = True, debug = True)

def main():
    # example Epic Games price finder
    # EpicGames_test()

    # fill MSRP table
    # EpicGames_MSRPs()

    # fill PRICES table
    EpicGames_Prices()
    

if __name__ == '__main__':
    main()