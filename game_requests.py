#!/usr/bin/env python3
import requests
import pprint
from dotenv import load_dotenv
import os

def make_request(api_url, body, ID, token):
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

def main():
    load_dotenv()
    ID = os.getenv("id_twitch")
    secret = os.getenv("secret_twitch")
    token = get_oauth(ID, secret)

    cont = True
    offset = 0
    while cont:
        response = make_request("https://api.igdb.com/v4/games", f"fields name; where id > 0; limit 500; offset {offset};", ID, token).text
        if response == "[]":
            cont = False
        offset += 500
        pprint.pprint(response)

if __name__ == "__main__":
    main()
