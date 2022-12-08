#!/usr/bin/env python3

import sys
sys.path.append('..')
import json
import time
import requests
import sqlFunctions
from collections import OrderedDict
from tqdm import tqdm

def get_store_games():
    library = {}
    response = requests.get('https://api.steampowered.com/ISteamApps/GetAppList/v0002/?key=F34EBAC622036D4C658B6E4BC5D04B49&format=json')

    for app in response.json()["applist"]["apps"]:
        if app["name"].strip():
            library[app["name"]] = {"appid": app["appid"]}
    
    return library

def get_databased_games():
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()
    cursor.execute("select id, name from GAMES;")
    return cursor.fetchall()

def get_entered_gameids():
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()
    cursor.execute("select game_id from MSRP m, GAMES g where g.id = m.game_id and source='Steam';")
    results = cursor.fetchall()
    return [result[0] for result in results]

def refine():
    with open("SteamGamesAdd.json", "r") as file:
        games = json.load(file)
        games["invalid"] = {}

        newGames = games["found"]["new"]
        for game in tqdm(newGames, total = len(newGames)):
            id = games["found"]["new"][game]["steam id"]

            try:
                result = requests.get(f"https://store.steampowered.com/api/appdetails?appids={id}&key=F34EBAC622036D4C658B6E4BC5D04B49&format=json").json()[str(id)]
            except:
                print(f"waiting 5 mins")
                with open("SteamGamesAddFixed.json", "w") as outfile:
                    outfile.write(json.dumps(newGames, indent=4))
                time.sleep(300)
                result = requests.get(f"https://store.steampowered.com/api/appdetails?appids={id}&key=F34EBAC622036D4C658B6E4BC5D04B49&format=json").json()[str(id)]

            if result["success"]:
                data = result["data"]

                if not data["is_free"] and "price_overview" not in data: # entry on Steam by not for sale
                    games["invalid"][id] = game
                    continue

                initialPrice = 0 if data["is_free"] else data["price_overview"]["initial"] / 100
                storeLink = "https://store.steampowered.com/app/" + str(id)
                newGames[game]["initialPrice"] = initialPrice
                newGames[game]["storeLink"] = storeLink
            else:
                games["invalid"][id] = game

def main():
    steamLibrary = get_store_games()
    databasedLibrary = get_databased_games()
    databasedLibrary = {result[1].lower().replace("\\'", "'").replace('\u2122', '').replace('\u00ae', '').replace("'", "").replace("\u2019", "").replace('\u2013', '-').replace(' - ', ' ').replace(': ', ' ').replace('.', '').replace('!', '').strip(): {"game_id": result[0]} for result in databasedLibrary}
    enteredGameids = get_entered_gameids()

    oldMatchedCount = 0
    oldMatchedGames = {}
    newMatchedCount = 0
    newMatchedGames = {}
    unmatchedCount = 0
    unmatchedGames = {}

    invalidSteamGames = {}

    for game in tqdm(steamLibrary, total = len(steamLibrary)):
        titles = []
        titles.append(game.lower().replace('\u2122', '').replace('\u00ae', '').replace("'", "").replace("\u2019", "").replace('\u2013', '-').replace(' - ', ' ').replace(': ', ' ').replace('.', '').replace('!', '').strip())

        if titles[0].endswith('demo') or "soundtrack" in titles[0]: # don't get demos or soundtracks
            continue

        matchedTitle = ""
        for title in titles:
            if title in databasedLibrary: 
                matchedTitle = title
                break
        if matchedTitle:
            if databasedLibrary[matchedTitle]["game_id"] in enteredGameids:
                    oldMatchedGames[matchedTitle] = {"storeLink" : "NA", "initialPrice": "NA", "gameid": databasedLibrary[matchedTitle]["game_id"]}
                    oldMatchedCount += 1
            else:
                newMatchedGames[matchedTitle] = {"storeLink" : "NA", "initialPrice": "NA", "gameid": databasedLibrary[matchedTitle]["game_id"], "steam id": steamLibrary[game]["appid"]}
                newMatchedCount += 1
            databasedLibrary.pop(matchedTitle)
        else: 
            unmatchedGames[game] = {"storeLink" : "NA", "initialPrice": "NA", "steam id": steamLibrary[game]["appid"]}
            unmatchedCount += 1
                
    with open("SteamMatchedGames.json", "w") as outfile:
        outfile.write(json.dumps({"found": {"old": OrderedDict(sorted(oldMatchedGames.items())), "new": OrderedDict(sorted(newMatchedGames.items()))},
                                  "not found": OrderedDict(sorted(unmatchedGames.items())),
                                  "IGDB games not found": OrderedDict(sorted(databasedLibrary.items())),
                                  "counts": {"new games": newMatchedCount, "old games": oldMatchedCount, "games not found": unmatchedCount, "IGDB games not found": len(databasedLibrary)}}, indent=4))

    print(oldMatchedCount+newMatchedCount, "games found", f"({newMatchedCount} new, {oldMatchedCount} old)")
    print(unmatchedCount, "games not found")

if __name__ == "__main__":
    refine()