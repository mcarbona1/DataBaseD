#!/usr/bin/env python3
import os
import getpass
import mysql.connector

#def MySQL_connect(hostname, db, usernameInput=None, passwordInput=None):
#    if usernameInput is None:
#        usernameInput = input('Enter username: ')
#    if passwordInput is None:
#        passwordInput = getpass.getpass('Enter password: ')
#    connection = mysql.connector.connect(user=usernameInput, password=passwordInput, host=hostname, database=db)
#    return connection


#import MySQLdb

def Insert_Genre(entry_id, game_id, genre):

    # Open Connection
    conn = mysql.connector.connect(
            user='rwachte2', password='pwpwpwpw', host='localhost', database='rwachte2')

    # create cursor object
    cursor = conn.cursor()

    insert_stmt = ("INSERT INTO GENRE"
            "(entry_id, game_id, genre) "
            "VALUES (%s, %s, %s)")

    data = (entry_id, game_id, genre)

    #format values?
    #insert_values = f"({})".format(','.join(['"{}"'.format(item) for item in values]))
    #print(insert_values)
    

    try:
        #Execute SQL Command
        cursor.execute(insert_stmt, data)

        #Commit your changes in the database
        conn.commit()

    except:

        #Rolling back in case of error
        conn.rollback()

    conn.close()


