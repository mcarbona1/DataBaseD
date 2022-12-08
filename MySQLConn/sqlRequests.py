#!/usr/bin/env python3
import os
import getpass
import mysql.connector

def MySQL_connect(hostname, db, usernameInput=None, passwordInput=None):
    if usernameInput is None:
        usernameInput = input('Enter username: ')
    if passwordInput is None:
        passwordInput = getpass.getpass('Enter password: ')
    connection = mysql.connector.connect(user=usernameInput, password=passwordInput, host=hostname, database=db)
    return connection

def MySQL_query(conn, db_names: list, fields: list, filter_list: list = None, **kwargs):
    consQuery = f"SELECT {', '.join(fields)} FROM {', '.join(db_names)}"
    if filter_list is not None:
        consQuery += f" WHERE {' and '.join(filter_list)}"
    consQuery += ";"

    cursor = conn.cursor()
    cursor.execute(consQuery)
    results = cursor.fetchall()
    cursor.close()

    return results
