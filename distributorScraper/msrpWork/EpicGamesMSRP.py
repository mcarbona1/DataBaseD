#!/usr/bin/env python3

import sys
sys.path.append('..')
import json
from epicstore_api import EpicGamesStoreAPI
from datetime import datetime
import sqlFunctions
from collections import OrderedDict

def get_store_games():
    api = EpicGamesStoreAPI()
    date = datetime.now()
    dateRange = date.strftime('[1958-10-16T14:02:36.304Z,%Y-%m-%dT14:02:36.304Z]')
    start = 0
    library = []

    while True:
        games = api.fetch_store_games(
            product_type='games/edition/base|bundles/games|editors',
            count=1000,
            sort_by='releaseDate',
            sort_dir='DESC',
            release_date=dateRange,
            with_price=True,
            start=start
        )

        results = games["data"]["Catalog"]["searchStore"]

        library = library + results["elements"]
        if ((start + 1000) > results["paging"]["total"]): break
        start += 1000

    return library

def get_databased_games():
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()
    cursor.execute("select id, name from GAMES;")
    return cursor.fetchall()

def get_entered_gameids():
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()
    cursor.execute("select game_id from MSRP m, GAMES g where g.id = m.game_id and source='Epic Games';")
    results = cursor.fetchall()
    return [result[0] for result in results]

# 1258 games match when not filtering invalid slugs
def main():
    epicLibrary = get_store_games() # get all games from Epic Store API
    databasedLibrary = get_databased_games()
    databasedLibrary = {result[1].replace("\\'", "'")[1:-1].lower().replace('\u2122', '').replace('\u00ae', '').replace("'s", "s").replace("\u2019s", "s").replace(' - ', ' ').replace(': ', ' ').replace(' \u2013 ', ' ').replace('!', '').strip():{"game_id": result[0]} for result in databasedLibrary}
    enteredGameids = get_entered_gameids()
    with open("databasedGames.json", "w") as outfile:
        outfile.write(json.dumps(OrderedDict(sorted(databasedLibrary.items())), indent=4))

    oldMatchedCount = 0
    oldMatchedGames = {}
    newMatchedCount = 0
    newMatchedGames = {}
    unmatchedCount = 0
    unmatchedGames = {}
    for game in epicLibrary:
        productSlug = game["productSlug"].strip() if isinstance(game["productSlug"], str) else None
        titles = []
        titles.append(game["title"].lower().replace('\u2122', '').replace('\u00ae', '').replace("'s", "s").replace("\u2019s", "s").replace(' - ', ' ').replace(': ', ' ').replace(' \u2013 ', ' ').strip())
        titles.append(titles[0].replace(' standard edition', '').replace('!', ''))

        if productSlug:
            if productSlug.endswith("/home"): # strip '/home' from end of valid productSlugs (end of links)
                productSlug = productSlug.replace("/home", "")

            storeLink = "https://store.epicgames.com/en-US/p/" + productSlug
            initialPrice = game["price"]["totalPrice"]["originalPrice"] / 100

            matchedTitle = ""
            for title in titles:
                if title in databasedLibrary: 
                    matchedTitle = title
                    break

            if matchedTitle:
                if databasedLibrary[matchedTitle]["game_id"] in enteredGameids:
                    oldMatchedGames[matchedTitle] = {"storeLink" : storeLink, "initialPrice": initialPrice, "gameid": databasedLibrary[matchedTitle]["game_id"]}
                    oldMatchedCount += 1
                else:
                    newMatchedGames[matchedTitle] = {"storeLink" : storeLink, "initialPrice": initialPrice, "gameid": databasedLibrary[matchedTitle]["game_id"]}
                    newMatchedCount += 1
            else: 
                unmatchedGames[title] = {"storeLink" : storeLink, "initialPrice": initialPrice}
                unmatchedCount += 1

    with open("EpicGamesMatchedGames.json", "w") as outfile:
        outfile.write(json.dumps({"found": {"old": OrderedDict(sorted(oldMatchedGames.items())), "new": OrderedDict(sorted(newMatchedGames.items()))},
                                  "not found": OrderedDict(sorted(unmatchedGames.items()))}, indent=4))
    
    print(oldMatchedCount+newMatchedCount, "games found", f"({newMatchedCount} new, {oldMatchedCount} old)")
    print(unmatchedCount, "games not found")

if __name__ == "__main__":
    main()