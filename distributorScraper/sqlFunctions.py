#!/usr/bin/env python3

import sys
import getpass
from datetime import datetime
import mysql.connector
import json

def MySQL_connect(hostname, db, usernameInput=None, passwordInput=None):
    if usernameInput is None:
        usernameInput = input('Enter username: ')
    if passwordInput is None:
        passwordInput = getpass.getpass('Enter password: ')
    connection = mysql.connector.connect(user=usernameInput, password=passwordInput, host=hostname, database=db)
    return connection

def MySQL_insert_into_PRICES(MSRP_id: int, date: datetime, current_price: float, connection):
    cursor = connection.cursor()

    insert_stmt = f"INSERT INTO PRICES (MSRP_ID, date, curr_price) VALUES ({MSRP_id}, '{date}', {current_price})"

    try:
        cursor.execute(insert_stmt) # Execute SQL Command
        connection.commit() # Commit your changes in the database
    except:
        connection.rollback() # Rolling back in case of error
    
def MySQL_insert_into_MSRP(game_id: int, url: str, base_price: float, source: str, available: int, connection):
    cursor = connection.cursor()
    insert_stmt = f"INSERT INTO MSRP (game_id, URL, base_price, source, available) VALUES ({game_id}, '{url}', {base_price}, '{source}', {available})"

    try:
        cursor.execute(insert_stmt) # Execute SQL Command
        connection.commit() # Commit your changes in the database
    except:
        connection.rollback() # Rolling back in case of error

def main():
    connection = MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()
    cursor.execute("select id, name from GAMES")
    results = cursor.fetchall()
    games = {result[1].replace("\\'", "'")[1:-1]:{"game_id": result[0], "msrp_id": 0} for result in results} # deal with single quotes
    #MySQL_insert_into_MSRP(19924, "http://poggers.com", 69.99, "EPIC", 1, connection)
    #MySQL_insert_into_PRICES(1, datetime.now(), 42.99, None)
    with open("queryTest.json", "w") as outfile:
        outfile.write(json.dumps(games, indent=4))
if __name__ == "__main__":
    main()