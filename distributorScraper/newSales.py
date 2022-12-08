#!/usr/bin/env python3

import sys
from datetime import date
from datetime import timedelta
import sqlFunctions

# get 100 random game ids for new sales, updating NEW_SALES table with results
def main():
    connection = sqlFunctions.MySQL_connect("localhost", "rwachte2", "rwachte2", "pwpwpwpw")
    cursor = connection.cursor()
    today = date.today()
    dateCutoff = today - timedelta(days = 14) # check games that 
    query = f"""select game_id from (select MSRP_ID, max(curr_price) as base_price from PRICES where date > '{dateCutoff}' group by msrp_id) a 
            inner join PRICES p on a.MSRP_ID = p.MSRP_ID 
            inner join MSRP m on a.MSRP_ID = m.MSRP_ID 
            inner join GAMES g on m.game_id = g.id where age_rating is not NULL and age_rating != 'AO' and a.base_price > p.curr_price and p.date = '{today}' order by rand() limit 100;"""

    '''select game_id from (select MSRP_ID, max(curr_price) as base_price from PRICES where date > '2022-11-16' group by msrp_id) a 
            inner join PRICES p on a.MSRP_ID = p.MSRP_ID 
            inner join MSRP m on a.MSRP_ID = m.MSRP_ID 
            inner join GAMES g on m.game_id = g.id where age_rating is not NULL and age_rating != 'AO' and a.base_price > p.curr_price and p.date = '2022-12-02' order by rand() limit 100;'''

    cursor.execute(query)

    saleGames = [item[0] for item in cursor.fetchall()]
    for sale_id, game_id in enumerate(saleGames, start=1):
        cursor.execute(f"UPDATE NEW_SALES set game_id = {game_id} where sale_id = {sale_id}") # Execute SQL Command
        connection.commit() # Commit your changes in the database

    cursor.close()
    connection.close()

if __name__ == "__main__":
    main()