#!/usr/bin/env python3

import mysql.connector
import sklearn
from sklearn.model_selection import train_test_split 
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neighbors import NearestNeighbors
import numpy as np
import pandas as pd
import time
import random

class HashTable:

	# Create empty bucket list of given size
	def __init__(self, size):
		self.size = size
		self.hash_table = self.create_buckets()

	def create_buckets(self):
		return [[] for _ in range(self.size)]

	# Insert values into hash map
	def set_val(self, key, val):
		
		# Get the index from the key
		# using hash function
		hashed_key = hash(key) % self.size
		
		# Get the bucket corresponding to index
		bucket = self.hash_table[hashed_key]

		found_key = False
		for index, record in enumerate(bucket):
			record_key, record_val = record
			
			# check if the bucket has same key as
			# the key to be inserted
			if record_key == key:
				found_key = True
				break

		# If the bucket has same key as the key to be inserted,
		# Update the key value
		# Otherwise append the new key-value pair to the bucket
		if found_key:
			bucket[index] = (key, val)
		else:
			bucket.append((key, val))

	# Return searched value with specific key
	def get_val(self, key):
		
		# Get the index from the key using
		# hash function
		hashed_key = hash(key) % self.size
		
		# Get the bucket corresponding to index
		bucket = self.hash_table[hashed_key]

		found_key = False
		for index, record in enumerate(bucket):
			record_key, record_val = record
			
			# check if the bucket has same key as
			# the key being searched
			if record_key == key:
				found_key = True
				break

		# If the bucket has same key as the key being searched,
		# Return the value found
		# Otherwise indicate there was no record found
		if found_key:
			return record_val
		else:
			return "No record found"

	# Remove a value with specific key
	def delete_val(self, key):
		
		# Get the index from the key using
		# hash function
		hashed_key = hash(key) % self.size
		
		# Get the bucket corresponding to index
		bucket = self.hash_table[hashed_key]

		found_key = False
		for index, record in enumerate(bucket):
			record_key, record_val = record
			
			# check if the bucket has same key as
			# the key to be deleted
			if record_key == key:
				found_key = True
				break
		if found_key:
			bucket.pop(index)
		return

	# To print the items of hash map
	def __str__(self):
		return "".join(str(item) for item in self.hash_table)

# making GLOBAL HashTable of row number and game_id
hashmap = HashTable(38000)
reverse_hashmap = HashTable(225000)


def get_data():
    #establishing the connection
    conn = mysql.connector.connect(user='rwachte2', password='pwpwpwpw', host='localhost', database='rwachte2')

    #Creating a cursor object using the cursor() method
    cursor = conn.cursor()

    # Preparing SQL query to INSERT a record into the database.
    sql = """SELECT GENRE.game_id, GENRE.genre FROM GENRE INNER JOIN MSRP ON GENRE.game_id=MSRP.game_id"""

    #try:
       # Executing the SQL command
    cursor.execute(sql)

       # Commit your changes in the database
       #conn.commit()

    #except:
       # Rolling back in case of error
    #   conn.rollback()


    data = []

    #copy data from cursor
    for entry in cursor:
        data.append(entry)

    # close cursor
    cursor.close()

    #close connection
    conn.close()

    # creates dictionary of genres with counts of each in table
    genres_total = {}
    genres = []
    count = 0
    for genre in data:
        count += 1
        genres_total[genre[1]] = genres_total.get(genre[1], 0) + 1
        if genre[1] not in genres:
            genres.append(genre[1])
    
    ##print(genres)
    genre_index = dict(enumerate(genres))
    genre_dict = {value:key for key, value in genre_index.items()}
    #print(genre_index)

    genre_count = 0
    for genre in genres:
        genre_count += 1
    count = 37950 #TODO: fix hard coding
    #print("Number of genres is: ", genre_count)
    games = {}
    #genre_data = [[0]*(genre_count+1)]*count
    genre_data = [[0 for i in range((genre_count + 1))] for j in range(count)]


    # creates dictionary of games with each genre tag in a list
    # places game_id in each row of genre_data array
    i = 0
    for entry in data:
        if entry[0] not in games:
            #print(entry[0])
            genre_data[i][0] = entry[0]
            i+=1
            games[entry[0]] = []
        games[entry[0]].append(entry[1])

    #print(genre_data)
    # create array of games with ID and boolean value for their respective genre tag
    i = 0
    for row in genre_data:
        game_id = row[0]
        game_genres = games[game_id]
        #print(game_genres)
        for genre in game_genres:
            #print(game_id, genre)
            index = genre_dict[genre] + 1
            #print(index)
            try: genre_data[i][int(index)] = 1
            except: break
        i += 1
        #print(game_genres)

    df = pd.DataFrame(genre_data, columns=['Game ID', 'Shooter', 'Simulator', 'Adventure', 'Role-Playing (RPG)', 'Strategy', 'Turn-Based Strategy (TBS)', 'Tactical', 'Real-Time Strategy (RTS)', 'Fighting','Racing','Hack and Slash',  'Point and Click', 'Puzzle','Platform', 'Indie','MOBA','Music', 'Arcade', 'Sport', 'Pinball',   'Card & Board Game', 'Visual Novel', 'Quiz/Trivia'])
    corr = df.corr()
    #print(corr)

    #print(df)
    X = df.to_numpy()

    global hashmap
    global reverse_hashmap

    # making HashTable of row number and game_id
    #hashmap = HashTable(38000)
    #reverse_hashmap = HashTable(38000)

    row_num = 0
    for row in X:
        game_id = row[0]
        hashmap.set_val(int(row_num), int(game_id))
        reverse_hashmap.set_val(int(game_id), int(row_num))
        row_num += 1


    X = np.delete(X,0,1)

    #print(X)
    return(X, hashmap, reverse_hashmap)

def knn(X, hashmap):

    nbrs = NearestNeighbors(n_neighbors=5, algorithm='auto').fit(X)
    distances, indices = nbrs.kneighbors(X)

    #print(indices)

    row_iter = 0
    for row in indices:
        col_iter = 0
        for col in row:
            #print(indices[row_iter][col_iter])
            indices[row_iter][col_iter] = hashmap.get_val(int(indices[row_iter][col_iter]))
            col_iter += 1
        row_iter += 1
    #print(indices)


    #format printing of recommendations

    raw_recommends = \
            sorted(
                list(
                    zip(
                        indices.squeeze().tolist(),
                        distances.squeeze().tolist()
                    )
                ),
                key=lambda x: x[1]
            )[:0:-1]


    #for i, (idx, dist) in enumerate(raw_recommends):
                #print('{0}: {1}, with distance '
                      #'of {2}'.format(i+1, idx, dist))

    np.savetxt('../gameApp/static/indices.csv', indices, fmt='%d', delimiter=',')

    return indices

def user_recs(user, indices='indices.csv'):

    index = open(indices)
    indices_arr = np.loadtxt(index, delimiter=",", dtype = int, encoding="utf-8-sig")

    
    #print(indices)

    #establishing the connection
    conn = mysql.connector.connect(user='rwachte2', password='pwpwpwpw', host='localhost', database='rwachte2')

    #Creating a cursor object using the cursor() method
    cursor = conn.cursor()

    # Preparing SQL query to INSERT a record into the database.
    sql = """SELECT username, game_id, weight FROM LIKES where weight='-1' OR weight='1'"""

    cursor.execute(sql)

    data = []

    for entry in cursor:
        #print(entry)
        data.append(entry)


    likes = []
    dislikes = []
    
    # sort likes and dislikes
    for entry in data:
        if entry[0] == user:
            if entry[2] == 1:
                likes.append(entry[1])
            elif entry[2] == -1:
                dislikes.append(entry[1])


    #print("likes:")
    #print(likes)
    #print("dislikes:")
    #print(dislikes)

    recs = []

    #get neighbors for likes
    for like in likes:
        row_num = reverse_hashmap.get_val(int(like))
        for index in indices_arr[row_num]:
            if index != like:
                recs.append(index)

    #get neighbors for dislikes and remove them
    for dislike in dislikes:
        row_num = reverse_hashmap.get_val(int(dislike))
        for index in indices_arr[int(row_num)]:
            if index in recs:
                recs.remove(index)
    
    #print("recommendations:")
    random.shuffle(recs)
    #print(recs)

    cursor.close()
    conn.close()

    return recs


