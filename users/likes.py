import sys
from datetime import date
from datetime import timedelta
from collections import defaultdict
sys.path.append('..')
from distributorScraper import sqlFunctions

# to be called by front end
def like_game(username: str, gameid: int):
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()
    cursor.execute(f"select * from LIKES where username = '{username}' and game_id = {gameid};")
    if cursor.fetchall():
        cursor.execute(f"update LIKES set weight = 1 where username = '{username}' and game_id = {gameid};")
    else:
        cursor.execute(f"insert into LIKES (username, game_id, weight) values ('{username}', {gameid}, 1);")
    connection.commit()
    cursor.close()
    connection.close()

def dislike_game(username: str, gameid: int):
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()
    cursor.execute(f"select * from LIKES where username = '{username}' and game_id = {gameid};")
    if cursor.fetchall():
        cursor.execute(f"update LIKES set weight = -1 where username = '{username}' and game_id = {gameid};")
    else:
        cursor.execute(f"insert into LIKES (username, game_id, weight) values ('{username}', {gameid}, -1);")
    connection.commit()
    cursor.close()
    connection.close()

def neutral_game(username: str, gameid: int):
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()
    cursor.execute(f"update LIKES set weight = 0 where username = '{username}' and game_id = {gameid};")
    connection.commit()
    cursor.close()
    connection.close()

# to be called by front end (to determine if game will have add/remove from wishlist button)
def get_user_liked(username: str):
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()

    cursor.execute(f"select game_id from LIKES where username = '{username}' and weight = 1")
    results = [item[0] for item in cursor.fetchall()]
    cursor.close()
    connection.close()
    return results

def get_user_disliked(username: str):
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()

    cursor.execute(f"select game_id from LIKES where username = '{username}' and weight = -1")
    results = [item[0] for item in cursor.fetchall()]
    cursor.close()
    connection.close()
    return results

def main():
    print("***Likes Demo***")
    like_game("mcarbona", 119133)
    like_game("mcarbona", 11133)

if __name__ == "__main__":
    main()