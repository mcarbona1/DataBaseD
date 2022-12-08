#!/usr/bin/env python3

import sys
sys.path.append('..')
import json
import requests
import sqlFunctions
from collections import OrderedDict
from tqdm import tqdm

def get_store_games():
    library = []
    result = requests.get("https://api.gog.com//v2//games?locale=en-US&page=1&limit=200").json() # first page of GOG web api
    currPage = result["page"]
    pages = result["pages"]

    while currPage <= pages:
        print(currPage)
        results = result["_embedded"]["items"]

        for game in results:
            library.append(game)

        if currPage < pages: # go to next page if more available
            result = requests.get(result["_links"]["next"]["href"]).json()
            currPage = result["page"]
        else: break
    
    return library

def get_databased_games():
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()
    cursor.execute("select id, name from GAMES;")
    return cursor.fetchall()

def get_entered_gameids():
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()
    cursor.execute("select game_id from MSRP m, GAMES g where g.id = m.game_id and source='GOG';")
    results = cursor.fetchall()
    return [result[0] for result in results]

def main():
    gogLibrary = get_store_games()
    databasedLibrary = get_databased_games()
    databasedLibrary = {result[1].replace("\\'", "'")[1:-1].lower().replace('\u2122', '').replace('\u00ae', '').replace("'s", "s").replace("\u2019s", "s").replace(' - ', ' ').replace(': ', ' ').replace(' \u2013 ', ' ').replace('!', '').strip():{"game_id": result[0]} for result in databasedLibrary}
    enteredGameids = get_entered_gameids()

    oldMatchedCount = 0
    oldMatchedGames = {}
    newMatchedCount = 0
    newMatchedGames = {}
    unmatchedCount = 0
    unmatchedGames = {}

    for game in tqdm(gogLibrary, total = len(gogLibrary)):
        storeLink = game["_links"]["store"]["href"]
        entry = game["_embedded"]["product"]
        titles = []
        titles.append(entry["title"].lower().replace('\u2122', '').replace('\u00ae', '').replace("'", "").replace("\u2019", "").replace(' \u2013 ', ' ').replace(' - ', ' ').replace(': ', ' ').strip())
        titles.append(titles[0].replace('1', 'i').replace('2', 'ii').replace('3', 'iii').replace('4', 'iv').replace('5', 'v').replace('6', 'vi').replace('7', 'vii').replace('8', 'viii').replace('9', 'ix').replace('10', 'x').replace('11', 'xi').replace('12', 'xii').replace('13', 'xiii').replace('14', 'xiv').replace('15', 'xv'))
        titles.append(titles[0].replace(' standard edition', '').replace('!', '').replace('the ', ''))

        if titles[0].endswith('demo') or "soundtrack" in titles[0]: # don't get demos or soundtracks
            continue

        if entry["isAvailableForSale"]:
            matchedTitle = ""
            for title in titles:
                if title in databasedLibrary: 
                    matchedTitle = title
                    break
            pricePage = requests.get(entry["_links"]["prices"]["href"].replace("{country}", "US")).json()
            initialPrice = int(pricePage["_embedded"]["prices"][0]["basePrice"].split()[0]) / 100
            
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
                
    with open("GOGMatchedGames.json", "w") as outfile:
        outfile.write(json.dumps({"found": {"old": OrderedDict(sorted(oldMatchedGames.items())), "new": OrderedDict(sorted(newMatchedGames.items()))},
                                  "not found": OrderedDict(sorted(unmatchedGames.items())), 
                                  "counts": {"new games": newMatchedCount, "old games": oldMatchedCount, "games not found": unmatchedCount}}, indent=4))

    print(oldMatchedCount+newMatchedCount, "games found", f"({newMatchedCount} new, {oldMatchedCount} old)")
    print(unmatchedCount, "games not found")

if __name__ == "__main__":
    main()