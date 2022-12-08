import sys
import os
from datetime import date
from datetime import timedelta
from collections import defaultdict
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from distributorScraper import sqlFunctions
from email.message import EmailMessage
import ssl
import smtplib

LOGOS = {"Steam" : "https://cdn.freebiesupply.com/images/large/2x/steam-logo-transparent.png",
         "GOG" : "https://i.ibb.co/5Rmbhyk/GOG-logo.png",
         "Epic Games" : "https://brandslogos.com/wp-content/uploads/images/epic-games-logo-black-and-white.png",
         "Roost": "https://i.ibb.co/Pjv1k2w/Roost-Logo.png"}

def email_demo():
    email_sender = "databased69@gmail.com"
    email_password = "hfyhviogkzblavpg"
    email_receiver = "databased69@gmail.com"
    subject = "Roost Wishlist Sale Starting"
    body = f"""<!DOCTYPE html>
    <html>
      <body style="background-color:#7B2CBF; font-family:arial; margin-top:0px; margin-left:0px; margin-right:0px;">
        <div style="display: flex; flex-direction: row; background-color:#5A189A; height:6.66vw;">
          <img src="{LOGOS['Roost']}" alt="Roost" style="width:5.33vw; height:5.33vw; margin-left:10px; margin-right:10px; padding: .75vw 0;">
          <h1 style="color: #FF8500; font-size:3.33vw; margin-top: 1vw">
            Roost
          </h1>
        </div>
        <div style="margin-left:1.33vw;">
          <h2 style="color:#FF8500; font-size:2.66vw; margin-top:10px; margin-bottom:0vw;">
            Hello Caleb420
          </h2>
          <h5 style="color:white; font-size:2vw; margin-top:0px; margin-bottom:10px">
            The following games on your wishlist are on sale:
          </h5>
          <div style="background-color:#5A189A; width:20vw; margin-bottom: .5vw">
            <img src="https://images.igdb.com/igdb/image/upload/t_original/co1n24.jpg" alt="Age of Empires II" style="width:20vw;"><br>
            <h4 style="color:#FF8500; font-size:1.5vw; margin-top:0em; margin-bottom:.3em; padding-left: .2em;">
              Age of Empires II: Definitive Edition
            </h4>
            <a style="color:white; text-decoration: none;" href="https://store.steampowered.com/app/813780/Age_of_Empires_II_Definitive_Edition/">
              <div style="background-color: #240048; display: flex; flex-direction: row; margin-top: 3px; margin-bottom: 3px;">
                <div style="margin-left: 5px; margin-right: 5px; margin-top: .4vw">
                  <img src="https://cdn.freebiesupply.com/images/large/2x/steam-logo-transparent.png" alt="Steam logo" style="width:2.3vw;height:2.3vw;">
                </div>
                <div style="margin-top: .2vw;">
                  <div style="background-color: #5ca53a; font-size: 1.6vw; text-decoration: none; margin-right:5px; margin-top: .5vw; margin-bottom: .5vw;">
                    -65%
                  </div>
                </div>
                <div style="margin-top: .5vw">
                  <div style="color: #646464; font-size: 1vw;">
                    <s>$19.99</s>
                  </div>
                  <div style="color: white; font-size: 1vw; margin-top: 0vw">
                    $6.99
                  </div>
                </div>
              </div>
            </a>
          </div>
        </div>
      </body>
    </html>
    """

    em = EmailMessage()
    em["From"] = email_sender
    em["To"] = email_receiver
    em["subject"] = subject
    em.set_content(body, subtype='html')

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email_receiver, em.as_string())

def email_user(user, email, userSales):
    email_sender = "databased69@gmail.com"
    email_password = "hfyhviogkzblavpg"
    email_receiver = email
    subject = "Roost Wishlist Sale Starting"
    body = f"""<!DOCTYPE html>
    <html>
      <body style="background-color:#7B2CBF; font-family:arial; margin-top:0px; margin-left:0px; margin-right:0px;">
        <div style="display: flex; flex-direction: row; background-color:#5A189A; height:6.66vw;">
          <img src="{LOGOS['Roost']}" alt="Roost" style="width:5.33vw; height:5.33vw; margin-left:10px; margin-right:10px; padding: .75vw 0;">
          <h1 style="color: #FF8500; font-size:3.33vw; margin-top: 1vw">
            Roost
          </h1>
        </div>
        <div style="margin-left:1.33vw;">
          <h2 style="color:#FF8500; font-size:2.66vw; margin-top:10px; margin-bottom:0vw;">
            Hello {user}
          </h2>
          <h5 style="color:white; font-size:2vw; margin-top:0px; margin-bottom:10px">
            The following games on your wishlist are on sale:
          </h5>

    """
    
    for game in userSales:
        body = body + f"""
          <div style="background-color:#5A189A; width:20vw; margin-bottom: .5vw">
            <img src={userSales[game]["cover"]} alt="{userSales[game]["name"]}" style="width:20vw;"><br>
            <h4 style="color:#FF8500; font-size:1.5vw; margin-top:0em; margin-bottom:.3em; padding-left: .2em;">
                {userSales[game]["name"]}
            </h4>

        """

        for deal in userSales[game]["deals"]:
            body = body + f"""<a style="color:white; text-decoration: none;" href="{deal['link']}">
                  <div style="background-color: #240048; display: flex; flex-direction: row; margin-top: 3px; margin-bottom: 3px;">
                      <div style="margin-left: 5px; margin-right: 5px; margin-top: .4vw">
                          <img src="{LOGOS[deal['source']]}" alt="{deal['source']} logo" style="width:2.3vw;height:2.3vw;">
                      </div>
                      <div style="margin-top: .2vw;">
                        <div style="background-color: #5ca53a; font-size: 1.6vw; text-decoration: none; margin-right:5px; margin-top: .5vw; margin-bottom: .5vw;">
                            -{deal["savings"]}%
                        </div>
                      </div>
                      <div style="margin-top: .5vw">
                          <div style="color: #646464; font-size: 1vw;">
                              <s>${deal['base_price']}</s>
                          </div>
                          <div style="color: white; font-size: 1vw; margin-top: 0vw">
                              ${deal['todays_price']}
                          </div>
                      </div>
                  </div>
              </a>
              """
        
        body = body + """</div>
        """

    body = body + """</div>
  </body>
</html>"""

    em = EmailMessage()
    em["From"] = email_sender
    em["To"] = email_receiver
    em["subject"] = subject
    em.set_content(body, subtype='html')

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email_receiver, em.as_string())

def check_wishlists():
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()
    images = {}
    today = date.today()
    yesterday = today - timedelta(days = 1)
    
    # get each user's wishlist
    cursor.execute(f"select email, WISHLIST.username, game_id from WISHLIST, USERS where on_wishlist = 1 and WISHLIST.username = USERS.username;")
    wishlists = defaultdict(list)
    emails = {}
    for email, user, gameid in cursor.fetchall():
        wishlists[user].append(gameid)
        emails[user] = email

    cursor.execute(f"select game_id, MSRP.msrp_id, name, source, base_price, todays_price, yesterdays_price, URL from GAMES, MSRP, (select todays_price, yesterdays_price, a.msrp_id from ((select curr_price as todays_price, msrp_id from PRICES where date = '{today}') as a inner join  (select curr_price as yesterdays_price, msrp_id from PRICES where date = '{yesterday}') as b on b.msrp_id = a.msrp_id and a.todays_price < b.yesterdays_price)) price where price.msrp_id = MSRP.msrp_id and GAMES.id = MSRP.game_id order by source, name;")
    deals = defaultdict(list)
    for deal in cursor.fetchall(): # filter data s.t. each game key corresponds to a list of its new sales
        deals[deal[0]].append({"msrp_id": deal[1], "name": deal[2].replace("\\'", "'")[1:-1], "source": deal[3], "base_price": deal[4], "todays_price": deal[5], "yesterdays_price": deal[6], "url": deal[7]})

    for user in wishlists:
        message = ""
        userSales = {}
        for game in wishlists[user]:
            if game in deals:
                if game not in images: 
                    cursor.execute(f"select url from COVERS where game_id = {game}")
                    imgs = [img[0] for img in cursor.fetchall()]
                    images[game] = imgs[0] if imgs else "https://images.igdb.com/igdb/image/upload/t_cover_big/nocover.png"
                
                userSales[game] = {"name": deals[game][0]["name"], "cover": images[game], "deals": []}
                for deal in deals[game]:
                    userSales[game]["deals"].append({"source": deal['source'], "todays_price": deal['todays_price'], "base_price": deal['base_price'], "savings": int(100*(1 - deal['todays_price']/deal['base_price'])), "link": deal['url']})

        if userSales:
            email_user(user, emails[user], userSales)
            print(f"Emailed {user}")

    cursor.close()
    connection.close()

def main():
    check_wishlists()

if __name__ == "__main__":
    main()