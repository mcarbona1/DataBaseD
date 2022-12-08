import sys
from datetime import date
from datetime import timedelta
from collections import defaultdict
sys.path.append('..')
from distributorScraper import sqlFunctions
from email.message import EmailMessage
import ssl
import smtplib

# to be called by front end
def add_to_wishlist(username: str, gameid: int):
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()
    cursor.execute(f"select * from WISHLIST where username = '{username}' and game_id = {gameid};")
    if cursor.fetchall():
        cursor.execute(f"update WISHLIST set on_wishlist = 1 where username = '{username}' and game_id = {gameid};")
    else:
        cursor.execute(f"insert into WISHLIST (username, game_id, on_wishlist) values ('{username}', {gameid}, 1);")
    connection.commit()
    cursor.close()
    connection.close()

# to be called by front end
def remove_from_wishlist(username: str, gameid: int):
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()
    cursor.execute(f"update WISHLIST set on_wishlist = 0 where username = '{username}' and game_id = {gameid};")
    connection.commit()
    cursor.close()
    connection.close()

# to be called by front end (to determine if game will have add/remove from wishlist button)
def get_user_wishlist(username: str):
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()

    cursor.execute(f"select game_id from WISHLIST where username = '{username}' and on_wishlist = 1")
    results = [item[0] for item in cursor.fetchall()]
    cursor.close()
    connection.close()
    return results

def check_wishlists():
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()
    images = {}
    today = date.today()
    yesterday = today - timedelta(days = 1)
    
    # get each user's wishlist
    cursor.execute(f"select username, game_id from WISHLIST where on_wishlist = 1")
    wishlists = defaultdict(list)
    for user, gameid in cursor.fetchall():
        wishlists[user].append(gameid)

    # get new game sales (today's price is lower than yesterday's price)
    cursor.execute(f"select game_id, MSRP.msrp_id, name, source, base_price, todays_price, yesterdays_price, URL from GAMES, MSRP, (select todays_price, yesterdays_price, a.msrp_id from ((select curr_price as todays_price, msrp_id from PRICES where date = '{today}') as a inner join  (select curr_price as yesterdays_price, msrp_id from PRICES where date = '{yesterday}') as b on b.msrp_id = a.msrp_id and a.todays_price < b.yesterdays_price)) price where price.msrp_id = MSRP.msrp_id and GAMES.id = MSRP.game_id order by source, name;")
    deals = defaultdict(list)
    for deal in cursor.fetchall(): # filter data s.t. each game key corresponds to a list of its new sales
        deals[deal[0]].append({"msrp_id": deal[1], "name": deal[2], "source": deal[3], "base_price": deal[4], "todays_price": deal[5], "yesterdays_price": deal[6], "url": deal[7]})

    for user in wishlists:
        message = ""
        for game in wishlists[user]:
            if game in deals:
                if game not in images: 
                    cursor.execute(f"select url from COVERS where game_id = {game}")
                    imgs = [img[0] for img in cursor.fetchall()]
                    images[game] = imgs[0] if imgs else "Image unavailable"
                    
                message = message + deals[game][0]["name"] + f"({images[game]}):\n" + "\n".join(f"{deal['source']}: {deal['todays_price']} ({int(100*(1 - deal['todays_price']/deal['base_price']))}% off from {deal['base_price']}), {deal['url']}" for deal in deals[game])
                if game != wishlists[user][-1]: message = message + '\n' 
        if message: print(f"Hello {user}\nThe following games on your wishlist are on sale:\n{message}")

    cursor.close()
    connection.close()

def main():
    print("***Wishlist Demo***")
    choice = input("'add to wishlist', 'remove from wishlist', 'get user wishlist', or 'check sales': ")

    if choice == 'add to wishlist':
        username = input("username: ")
        gameid = input("IGDB game id: ")
        add_to_wishlist(username, gameid)
    elif choice == 'remove from wishlist':
        username = input("username: ")
        gameid = input("IGDB game id: ")
        remove_from_wishlist(username, gameid)
    elif choice == 'get user wishlist':
        username = input("username: ")
        print(get_user_wishlist(username))
    elif choice == 'check sales':
        check_wishlists()

if __name__ == "__main__":
    main()