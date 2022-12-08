#!/usr/bin/env python3
from time import sleep
from fuzzywuzzy import fuzz
import requests
import base64
import pprint
from dotenv import load_dotenv
import os
import MySQLConn.sqlRequests as sql
import re
import json


class game:
    def __init__(self, gameObj):
        if isinstance(gameObj, str):
            raise ValueError
        if isinstance(gameObj, dict):
            self.name = gameObj["name"]
            self.igdb_id = gameObj["id"]
            self.genres = gameObj.get('genres') # translate
            self.age_rating = gameObj.get("age_ratings")
            self.rating = gameObj.get("rating")
            self.critic_rating = gameObj.get("aggregated_rating")
            self.release_date = gameObj.get("release_dates") # translate
            self.related = gameObj.get("similar_games") # translate
            self.companies = gameObj.get("involved_companies") # translate
            self.description = gameObj.get("summary")
            if self.description is None:
                self.description = gameObj.get("storyline")
            self.artwork = gameObj.get("artworks") #translate
        if isinstance(gameObj, tuple):
            self.igdb_id = gameObj[0]
            self.name = gameObj[1]
            self.rating = gameObj[2]
            self.critic_rating = gameObj[3]
            self.release_date = gameObj[4]
            self.description = gameObj[5]
            if not self.description == "NULL":
                self.description = decode(self.description)
            self.age_rating = gameObj[7] if gameObj[7] is not None else gameObj[12][3]
            self.companies = gameObj[8]
            self.genres = gameObj[9]
            self.related = gameObj[10]
            self.artwork = gameObj[11]
            self.critic_rating_count = gameObj[12][1]
            self.rating_count = gameObj[12][2]

    def printGame(self):
        for tag in self.__dict__:
            print(f"{tag}: {getattr(self, tag)}")

    def jsonify(self):
        returnDict = self.__dict__

        return returnDict

    def translateGame(self, ID, token):
        if not self.genres is None:
            translatedGenres = []
            for genre in self.genres:
                translatedGenres.append(genre.get("name"))
            self.genres = translatedGenres

        if not self.release_date is None:
            for date in self.release_date:
                if date.get("platform") != 6:
                    continue
                month = date.get("m")
                year = date.get("y")
                day = re.search('(?<= )\d+(?=,)', date.get("human", ""))
                if day and month and year:
                    day = day.group(0)
                    self.release_date = f"{month}-{day}-{year}"
                elif month and year:
                    self.release_date = f"{month}-01-{year}"
                else:
                    continue
                break
            if isinstance(self.release_date, list):
                self.release_date = None

        if not self.companies is None:
            translatedCompanies = []
            for company in self.companies:
                companyId = company.get("company")
                response = make_request("https://api.igdb.com/v4/companies", f"fields name; where id = {companyId};", ID, token)
                if response.status_code != 200:
                    continue
                try:
                    translatedCompany = (response.json()[0].get("name"), company.get("developer"), company.get("publisher"))
                    translatedCompanies.append(translatedCompany)
                except IndexError:
                    continue
            self.companies = translatedCompanies

        if not self.artwork is None:
            art = self.artwork[0]
            self.artwork = f"https:{art.get('url')}"

        if not self.age_rating is None:
            ratings = ["EC", "E", "E10", "T", "M", "AO"]
            for rating in self.age_rating:
                if (rating.get("rating") is None) or (rating.get("category") is None) or not (rating.get("rating") >= 7 and rating.get("rating") <= 12) or not (rating.get("category") == 1):
                    continue
                rating = rating.get("rating")
                self.age_rating = ratings[rating-7]
                break
            if isinstance(self.age_rating, list):
                self.age_rating = None



    def writeGame(self, conn):
        cursor = conn.cursor()
        null = "NULL"
        gamedbsqlhead = "INSERT INTO GAMES (id, name, age_rating, rating, critic_rating, release_date, description, art) "
        try:
            valsql = gamedbsqlhead + "VALUES ("
            valsql += f"{self.igdb_id}, "
            valsql += f'QUOTE("{self.name}"), '
            if self.age_rating is None or not isinstance(self.age_rating, str):
                valsql += f"{null}, "
            else:
                valsql += f"'{self.age_rating}', "
            valsql += f"{null if self.rating is None else self.rating}, "
            valsql += f"{null if self.critic_rating is None else self.critic_rating}, "
            if self.release_date is None or isinstance(self.release_date, list):
                valsql += f"{null}, "
            else:
                valsql += f"STR_TO_DATE('{self.release_date}', '%m-%d-%Y'), "
            if self.description is None:
                valsql += f"{null}, "
            else:
                valsql += f'"{encode(self.description)}", '
            if self.artwork is None or isinstance(self.artwork, list):
                valsql += f"{null}); "
            else:
                valsql += f"QUOTE('{self.artwork}'));"
            cursor.execute(valsql)
        except Exception as e:
            print(f"Error: {e}")
            cursor.close()
            return False

        genredbsqlhead = "INSERT INTO GENRE (game_id, genre) "
        if self.genres is not None:
            for genre in self.genres:
                if genre is None:
                    pass
                try:
                    valsql = genredbsqlhead + "VALUES ("
                    valsql += f"'{self.igdb_id}', "
                    valsql += f'"{genre}");'
                    cursor.execute(valsql)
                except Exception as e:
                    print(f"Error: {e}")

        relateddbsqlhead = "INSERT INTO RELATED_GAMES (base_game_id, related_game_id) "
        if self.related is not None:
            for game in self.related:
                try:
                    game = game.get("id")
                    if game is None:
                        continue
                    valsql = relateddbsqlhead + "VALUES ("
                    valsql += f'"{self.igdb_id}", '
                    valsql += f'"{game}");'
                    cursor.execute(valsql)
                except Exception as e:
                    print(f"Error: {e}")
        companydbsqlhead = "INSERT INTO INVOLVED_COMPANY (game_id, company, developer, publisher) "
        if self.companies is not None:
            for company in self.companies:
                if company[0] is None:
                    continue
                try:
                    valsql = companydbsqlhead + "VALUES ("
                    valsql += f"'{self.igdb_id}', "
                    valsql += f'"{company[0]}", '
                    valsql += f"'{1 if company[1] else 0}', "
                    valsql += f"'{1 if company[2] else 0}');"
                    cursor.execute(valsql)
                except Exception as e:
                    print(f"Error: {e}")
        try:
            conn.commit()
        except Exception as e:
            print(f"Error: {e}")
            cursor.close()
            return False

        cursor.close()
        return True





def make_request(api_url: str, body: str, ID, token):
    response = requests.post(api_url, headers={"Client-ID": ID, "Authorization": f"Bearer {token}"}, data=body)
    return response

def get_oauth(ID, secret):
    token = os.getenv("token_twitch")
    response = make_request("https://api.igdb.com/v4/games", f"fields name; where id > 0; limit 1;", ID, token)
    if response.status_code != 200:
        response = requests.post("https://id.twitch.tv/oauth2/token", params={"client_id": ID, "client_secret": secret, "grant_type": "client_credentials"})
        token = response.json()["access_token"]
        with open(".env", "w") as fd:
            fd.write(f"id_twitch={ID}\n")
            fd.write(f"secret_twitch={secret}\n")
            fd.write(f"token_twitch={token}\n")
    return token


def _write_game_thread(ID, secret, token, response, conn):
    try:
        newGame = game(response)
    except ValueError:
        return
    if newGame is None:
        return
    newGame.translateGame(ID, token)

    if not newGame.writeGame(conn):
        with open("./error.txt", "a") as fd:
            fd.write(json.dumps(response))

def encode(text: str):
    return base64.b64encode(text.encode()).decode() if text is not None else text

def decode(cypher_text):
    return base64.b64decode(cypher_text.encode()).decode() if cypher_text is not None else cypher_text

def _write_db(ID, secret, token, conn):
    cont = True
    offset = 0
    number_req = 50

    while cont:
        sleep(1)
        response = make_request("https://api.igdb.com/v4/games", f"fields name, id, genres.name, age_ratings.*, rating, aggregated_rating, release_dates.*, similar_games.name, involved_companies.*, summary, artworks.*; where id > 0 & platforms = (6) & category != (3, 5); limit {number_req}; offset {offset}; sort id asc;", ID, token).json()
        if response == []:
            cont = False
            continue
        if isinstance(response, dict) and response.get("message"):
            print(response.get("message"))
            continue

        offset += number_req
        for item in response:
            _write_game_thread(ID, secret, token, item, conn)

    conn.close()

def get_MSRP(conn, game_id):
    result = sql.MySQL_query(conn, ["MSRP"], ["*"], [f"game_id = {game_id}"])
    if len(result) > 0:
        return result
    return None

def get_NEW_SALES(conn):
    result = sql.MySQL_query(conn, ['NEW_SALES'], ["*"])
    if len(result) > 0:
        return result
    return None

def get_game(conn, game_id):
    response =  sql.MySQL_query(conn, ["GAMES"], ["*"], [f"id = {game_id}"])
    companies = sql.MySQL_query(conn, ["INVOLVED_COMPANY"], ["company", "developer", "publisher"], [f"game_id = {game_id}"])
    genres = sql.MySQL_query(conn, ["GENRE"], ["genre"], [f"game_id = {game_id}"])
    related = [(tuple[0].replace("\\+'", "'"), tuple[1]) for tuple in sql.MySQL_query(conn, ["GAMES", "RELATED_GAMES"], ["GAMES.name", "GAMES.id"], [f"RELATED_GAMES.base_game_id = {game_id}", "RELATED_GAMES.related_game_id = GAMES.id and id in (select game_id from MSRP)"])]
    artworks = sql.MySQL_query(conn, ["COVERS"], ["COVERS.url", "COVERS.height", "COVERS.width"], [f"COVERS.game_id = {game_id}"])
    add_info = sql.MySQL_query(conn, ["ADD_INFO"], ["*"], [f"ADD_INFO.id = {game_id}"])
    if len(artworks) > 0:
        artworks = artworks[0]
    else:
        artworks = None
    for i in range(len(genres)):
        genres[i] = genres[i][0]

    if len(response) < 1:
        return None 
    response = (*response[0], companies, genres, related, artworks, add_info[0] if len(add_info) > 0 else (None, None, None, None))
    gameInfo = game(response)
    return gameInfo.jsonify()


def get_prices(conn, game_id):
    result = sql.MySQL_query(conn, ["PRICES"], ["date", "curr_price"], [f"MSRP_ID = {game_id}"])
    return result


def fuzzy_search(query: str, options: list):
    search_results = list(map(lambda x: x[1], sorted(list(set(filter(lambda g: True if g[0] >= 85 else False, map(lambda x: (fuzz.partial_ratio(x[0].lower(), query.lower()), x), options)))), key=lambda x: x[0], reverse=True)))
    """
    i = 1
    while i < len(search_results):
        if search_results[i][0] == search_results[i-1][0]:
            search_results.pop(i)
            i -= 1
        i += 1
    """
    return None if search_results is None else search_results


def get_dbConn():
    return sql.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")

def get_list(conn):
    return sql.MySQL_query(conn, ["GAMES", "MSRP"], ["GAMES.name", "GAMES.id"], ["GAMES.id = MSRP.game_id", "MSRP.available = 1"])


def _get_pics(game_list: list, conn, token, ID):
    def get_pics_helper(game: dict, conn):
        cursor = conn.cursor()
        if game.get("cover"):
            cover = game.get("cover")
            gamedbsqlhead = "INSERT INTO COVERS (game_id, url, height, width) "
            try:
                valsql = gamedbsqlhead + "VALUES ("
                game_id = game.get('id')
                valsql += f"{game_id}, "
                url = cover.get('url')
                valsql += f'QUOTE("{url}"), '
                height = cover.get('height')
                width = cover.get('width')
                valsql += f'{height}, '
                valsql += f'{width});'
                cursor.execute(valsql)
            except Exception as e:
                print(f"Error: {e}")

        if game.get("artworks"):
            artworks = game.get("artworks")
            gamedbsqlhead = "INSERT INTO ARTWORK (game_id, url, height, width) "
            for art in artworks:
                try:
                    valsql = gamedbsqlhead + "VALUES ("
                    game_id = game.get('id')
                    valsql += f"{game_id}, "
                    url = art.get('url')
                    valsql += f'QUOTE("{url}"), '
                    height = art.get('height') 
                    width = art.get('width')
                    valsql += f'{height}, '
                    valsql += f'{width});'
                    cursor.execute(valsql)
                except Exception as e:
                    print(f"Error: {e}")


        try:
            conn.commit()
        except Exception as e:
            print(f"Error: {e}")
            cursor.close()
            return False

        cursor.close()
        return True
    
    def clean_urls(game):
        if game.get("cover"):
            cover = game.get('cover')
            cover["url"] = "https:" + cover.get("url")
            cover["url"] = cover.get("url").replace("t_thumb", "t_original")
        if game.get("artworks"):
            translatedArt = []
            artworks = game.get('artworks')
            for art in artworks:
                art["url"] = "https:" + art.get("url")
                art["url"] = art.get("url").replace("t_thumb", "t_original")
                translatedArt.append(art)
        
            game["artworks"] = translatedArt
        return game
            
    index = 0
    errored = False
    cover_list = sql.MySQL_query(conn, ["COVERS"], ["COVERS.game_id"])
    cover_list = set(map(lambda x: x[0], cover_list))   
    game_list = list(filter(lambda x: x[1] not in cover_list, game_list))
    while index < len(game_list):
        if index + 50 > len(game_list):
            games = game_list[index:]
        else:
            games = game_list[index:index+50]
        request = make_request("https://api.igdb.com/v4/games", f"fields cover.*, artworks.*; where id = ({','.join(list(map(lambda x: str(x[1]), games)))}); limit 50;", ID, token)
        if request.status_code != 200:
            if errored == True:
                print(request.text)
                print(index)
                errored=False
                continue
            sleep(1)
            errored = True
            continue
        index += 50
        if errored:
            errored = False
        for game in request.json():
            game = clean_urls(game)
            get_pics_helper(game, conn)


def _get_extra_info(game_list: list, conn, ID, token):
    def translate_age_rating(game: dict):
        age_mapping = [3, 7, 12, 16, 18]
        if game.get("age_ratings"):
            for rating in game.get("age_ratings", []):
                if rating.get("category") != 2:
                    continue
                map_index = rating.get("rating", 0)-1
                if map_index > len(age_mapping) or map_index < 0:
                    continue
                rating = age_mapping[map_index]
                if rating == 3 or rating == 7:
                    game["age_rating"] = "E"
                elif rating == 12:
                    game["age_rating"] = "T"
                elif rating == 16:
                    game["age_rating"] = "M"
                elif rating == 18:
                    game["age_rating"] = "AO"
        if not isinstance(game.get('age_rating'), str):
            game['age_rating'] = None
        return game

    def add_info_helper(game, conn):
        cursor = conn.cursor()
        gamedbsqlhead = "INSERT INTO ADD_INFO (id, critic_rating_count, user_rating_count, age_rating_translated) "
        try:
            valsql = gamedbsqlhead + "VALUES ("
            game_id = game.get('id')
            valsql += f"{game_id}, "
            rating_count = game.get('rating_count', "NULL") 
            critic_count = game.get('aggregated_rating_count', "NULL")
            valsql += f'{critic_count}, '
            valsql += f'{rating_count}, '
            age_rating = game.get('age_rating')
            if age_rating is None:
                valsql += 'NULL);'
            else:
                valsql += f'"{age_rating}");'


            cursor.execute(valsql)
        except Exception as e:
            print(f"Error: {e}")
            print(valsql)

        try:
            conn.commit()
        except Exception as e:
            print(f"Error: {e}")

        cursor.close()

    
    add_info_list = sql.MySQL_query(conn, ["ADD_INFO"], ["ADD_INFO.id"])
    add_info_list = set(map(lambda x: x[0], add_info_list))   
    game_list = list(filter(lambda x: x[1] not in add_info_list, game_list))
    index = 0
    errored = False
    while index < len(game_list):
        sleep(.25)
        if index + 50 > len(game_list):
            games = game_list[index:]
        else:
            games = game_list[index:index+50]
        request = make_request("https://api.igdb.com/v4/games", f"fields rating_count, aggregated_rating_count, age_ratings.*; where id = ({','.join(list(map(lambda x: str(x[1]), games)))}); limit 50;", ID, token)
        if request.status_code != 200:
            if errored == True:
                print(request.text)
                print(index)
                errored=False
                continue
            sleep(1)
            errored = True
            continue
        index += 50
        if errored:
            errored = False
        for game in request.json():
            game = translate_age_rating(game)
            add_info_helper(game, conn)

def _get_keywords(game_list: list, conn, ID, token):
    def translate_keywords(game):
        if game.get("keywords") is None:
            game["keywords"] = None
            return game
        
        translated_keywords = []
        for keyword in game.get("keywords"):
            if keyword.get("slug") is None:
                continue
            translated_keywords.append(keyword.get("slug"))
        
        game["keywords"] = translated_keywords

        return game

    def get_keywords_helper(game, conn):
        if game.get("keywords") is None:
            return
        
        cursor = conn.cursor()
        keywords = game.get("keywords")
        gamedbsqlhead = "INSERT INTO KEYWORDS (game_id, slug) "
        for keyword in keywords:
            try:
                valsql = gamedbsqlhead + "VALUES ("
                game_id = game.get('id')
                valsql += f"{game_id}, "
                valsql += f'QUOTE("{keyword}"));'
                cursor.execute(valsql)
            except Exception as e:
                print(f"Error: {e}")
                print(f"{game.get('id')}: {keyword}")


        try:
            conn.commit()
        except Exception as e:
            print(f"Error: {e}")
            print(game.get("id"))
            cursor.close()
        cursor.close()

    keyword_list = sql.MySQL_query(conn, ["KEYWORDS"], ["KEYWORDS.game_id"])
    keyword_list = set(map(lambda x: x[0], keyword_list))   
    game_list = list(filter(lambda x: x[1] not in keyword_list, game_list))
    print(game_list)
    index = 0
    errored = False
    while index < len(game_list):
        sleep(.25)
        if index + 50 > len(game_list):
            games = game_list[index:]
        else:
            games = game_list[index:index+50]
        request = make_request("https://api.igdb.com/v4/games", f"fields keywords.*; where id = ({','.join(list(map(lambda x: str(x[1]), games)))}); limit 50;", ID, token)
        if request.status_code != 200:
            if errored == True:
                print(request.text)
                print(index)
                errored=False
                continue
            sleep(1)
            errored = True
            continue
        index += 50
        if errored:
            errored = False
        for game in request.json():
            game = translate_keywords(game)
            get_keywords_helper(game, conn)

def main():
    load_dotenv()
    ID = os.getenv("id_twitch")
    secret = os.getenv("secret_twitch")
    token = get_oauth(ID, secret)
    conn = get_dbConn()
    game_list = sql.MySQL_query(conn, ["GAMES"], ["GAMES.name", "GAMES.id"])
    print(get_prices(conn, 16287))
    #request = make_request("https://api.igdb.com/v4/games", f'fields name, keywords.*; search "Dark Souls"; limit 5;', ID, token)
    #pprint.pprint(request.json())
    #_get_keywords(game_list, conn, ID, token)
    

if __name__ == "__main__":
    main()
