#!/usr/bin/env python3
from flask import Flask, render_template, request, redirect, session
from flask_session import Session
import datetime
import os
import sys
import uuid
directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(directory)
import users.user as user
import users.likes as likes
import users.wishlist as wishlist
import game_requests as gr
import plotting.pricePlot as pp
from typing import List
import MySQLConn.genreData as recommendation

port = 5006
conn = gr.get_dbConn()
game_list = gr.get_list(conn)
conn.close()
recommendation.get_data()

sps = dict()

def clean_game_list(game_list: List[int], conn):
    clean_games = []
    for game_id in game_list:
        game = gr.get_game(conn, game_id)
        if game['artwork'] == None:
            game['artwork_url'] = "https://images.igdb.com/igdb/image/upload/t_cover_big/nocover.png"
        else:
            game['artwork_url'] = game['artwork'][0].strip("'")
        game['name'] = game.get('name').strip("'")
        clean_games.append(game)
    return clean_games

def create_app():
    app = Flask(__name__)
    app.config["SESSION_PERMANENT"] = False 
    app.config["SESSION_TYPE"] = "filesystem"
    app.config['SESSION_FILE_DIR'] = './.roost_session/'
    Session(app)

    @app.route("/")
    def home():
        return redirect("/index")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        params = dict()
        params['user'] = session.get('username')
        if session.get("username") is not None:
            return redirect("/")
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")
            if not user.login(username, password):
                params["failed"] = True
                return render_template("login.html", **params)
            session["username"] = username
            session["likes"] = likes.get_user_liked(username)
            session["dislikes"] = likes.get_user_disliked(username)
            session["wishlist"] = wishlist.get_user_wishlist(username) 
            session["recommendations"] = recommendation.user_recs(username, "./static/indices.csv")
            return redirect("/user_home")
        params["username"] = session.get("username")
        return render_template("login.html", **params)

    @app.route("/user_home", methods=["GET", "POST"])
    def user_home():
        params = dict()
        params['user'] = session.get('username')
        if session.get("username") is None:
            return redirect("/login")
        conn = gr.get_dbConn()
        if request.method == "POST":
            form = request.form
            if form.get("command") == "like":
                likes.like_game(session.get("username"), form.get("id"))
                username = session.get("username")
                session["likes"] = likes.get_user_liked(username)
                session["dislikes"] = likes.get_user_disliked(username)
                session["wishlist"] = wishlist.get_user_wishlist(username) 
                session["recommendations"] = recommendation.user_recs(username, "./static/indices.csv")
            elif form.get("command") == "dislike":
                likes.dislike_game(session.get("username"), form.get("id"))
                username = session.get("username")
                session["likes"] = likes.get_user_liked(username)
                session["dislikes"] = likes.get_user_disliked(username)
                session["wishlist"] = wishlist.get_user_wishlist(username) 
                session["recommendations"] = recommendation.user_recs(username, "./static/indices.csv")
            elif form.get("command") == "neutral":
                likes.neutral_game(session.get("username"), form.get("id"))
                username = session.get("username")
                session["likes"] = likes.get_user_liked(username)
                session["dislikes"] = likes.get_user_disliked(username)
                session["wishlist"] = wishlist.get_user_wishlist(username) 
                session["recommendations"] = recommendation.user_recs(username, "./static/indices.csv")
            elif form.get("command") == "removeWishlist":
                wishlist.remove_from_wishlist(session.get("username"), form.get("id"))
                username = session.get("username")
                session["likes"] = likes.get_user_liked(username)
                session["dislikes"] = likes.get_user_disliked(username)
                session["wishlist"] = wishlist.get_user_wishlist(username) 
                session["recommendations"] = recommendation.user_recs(username, "./static/indices.csv")


        params['base_url'] = f'http://db8.cse.nd.edu:{port}'

        params["username"] = session.get("username")
        for item in ["likes", "dislikes", "recommendations", "wishlist"]:
            params[item] = (item, clean_game_list(session.get(item, []), conn))

        if len(params["likes"][1]) < 5:
            params["recommendations"] = ("recommendations", [])

        conn.close()
        return render_template("user_home.html", **params)



    @app.route("/signup", methods=["GET", "POST"])
    def signup():
        params = dict()
        params['user'] = session.get('username')
        if session.get("username"):
            redirect("/")
        if request.method == "POST":
            email = request.form.get("email")
            username = request.form.get("username")
            password = request.form.get("password")
            passwordVerify = request.form.get("passwordVerify")
            if not password == passwordVerify:
                params["failed"] = True
                params["failure_reason"] = "Passwords did not match!"
                return render_template("signup.html", **params)
            try:
                user.signup(username, email, password)
                session.clear()
                return redirect("/login")
            except ValueError as e:
                params["failed"] = True
                params["failure_reason"] = e
                return render_template("signup.html", **params)

        params["username"] = session.get("username")
        return render_template("signup.html", **params)

    @app.route("/logout")
    def logout():
        session.clear()
        return redirect("/")

    @app.route("/index", methods=["GET", "POST"])
    def index():
        # Home page with recs if logged in or sales if not
        params = dict()
        vals = dict()
        params['user'] = session.get('username')
        params["query"] = False
        params['base_url'] = f'http://db8.cse.nd.edu:{port}'
        conn = gr.get_dbConn()
        sales_result = gr.get_NEW_SALES(conn)
        sales_games = []
        for sale_id, game_id in sales_result:
            game = gr.get_game(conn, game_id)
            sales_games.append(game)
            if game['artwork'] == None:
                game['artwork_url'] = "https://images.igdb.com/igdb/image/upload/t_cover_big/nocover.png"
            else:
                game['artwork_url'] = game['artwork'][0].strip("'")
            game['name'] = game.get('name').strip("'")
        params['sales_games'] = sales_games
        conn.close()
        return render_template("index.html", **params)
   
    @app.route("/search", methods=["GET", "POST"])
    def search():
        # Original Search page
        params = dict()
        vals = dict()
        params['user'] = session.get('username')
        params["query"] = False
        conn = gr.get_dbConn()
        if request.method == "POST" and request.form.get("gameQuery"):
            query = request.form.get("gameQuery")
            result = gr.fuzzy_search(query, game_list)
            #result = set(result)
            params["result"] = result
            params["query"] = True
            params['base_url'] = f'http://db8.cse.nd.edu:{port}'
            games = []
            for game_name, game_id in result:
                game = gr.get_game(conn, game_id)
                games.append(game)
                if game['artwork'] == None:
                    game['artwork_url'] = "https://images.igdb.com/igdb/image/upload/t_cover_big/nocover.png"
                else:
                    game['artwork_url'] = game['artwork'][0].strip("'")
                game['name'] = game.get('name').strip("'")
            params['games'] = games
        conn.close()
        return render_template("search.html", **params)

    @app.route("/game/<game_id>", methods=["GET", "POST"])
    def show_game(game_id):
        conn = gr.get_dbConn()
        game = gr.get_game(conn, game_id)
        msrp_info = gr.get_MSRP(conn, game_id)
        price_list = list(map(lambda x: {x[-2]: gr.get_prices(conn, x[0])}, msrp_info))
        prices = {} 
        for source in price_list:
            for key, value in source.items():
                prices[key] = value
        params = dict()
        if request.method == "POST":
            form = request.form
            if not session.get("username"):
                return redirect("/login")

            if form.get("command") == "like":
                likes.like_game(session.get("username"), form.get("id"))
                username = session.get("username")
                session["likes"] = likes.get_user_liked(username)
                session["dislikes"] = likes.get_user_disliked(username)
                session["wishlist"] = wishlist.get_user_wishlist(username) 
                session["recommendations"] = recommendation.user_recs(username, "./static/indices.csv")
            elif form.get("command") == "dislike":
                likes.dislike_game(session.get("username"), form.get("id"))
                username = session.get("username")
                session["likes"] = likes.get_user_liked(username)
                session["dislikes"] = likes.get_user_disliked(username)
                session["wishlist"] = wishlist.get_user_wishlist(username) 
                session["recommendations"] = recommendation.user_recs(username, "./static/indices.csv")
            elif form.get("command") == "neutral":
                likes.neutral_game(session.get("username"), form.get("id"))
                username = session.get("username")
                session["likes"] = likes.get_user_liked(username)
                session["dislikes"] = likes.get_user_disliked(username)
                session["wishlist"] = wishlist.get_user_wishlist(username) 
                session["recommendations"] = recommendation.user_recs(username, "./static/indices.csv")
            elif form.get("command") == "addWishlist":
                wishlist.add_to_wishlist(session.get("username"), form.get("id"))
                username = session.get("username")
                session["likes"] = likes.get_user_liked(username)
                session["dislikes"] = likes.get_user_disliked(username)
                session["wishlist"] = wishlist.get_user_wishlist(username) 
                session["recommendations"] = recommendation.user_recs(username, "./static/indices.csv")
            elif form.get("command") == "removeWishlist":
                wishlist.remove_from_wishlist(session.get("username"), form.get("id"))
                username = session.get("username")
                session["likes"] = likes.get_user_liked(username)
                session["dislikes"] = likes.get_user_disliked(username)
                session["wishlist"] = wishlist.get_user_wishlist(username) 
                session["recommendations"] = recommendation.user_recs(username, "./static/indices.csv")


        params['user'] = session.get('username')
        if game['artwork'] == None:
            game['artwork_url'] = "https://images.igdb.com/igdb/image/upload/t_cover_big/nocover.png"
        else:
            game['artwork_url'] = game['artwork'][0].strip("'")
        game['name'] = game.get('name').strip("'").replace("\\'", "'")
        relGames = []
        for relGame in game.get("related", []):
            relGames.append((relGame[0].strip("'"), relGame[1]))
        game['related'] = relGames
        params['gameName'] = game.get("name")
        params['id'] = game.get("igdb_id")
        params['source'] = list(map(lambda x: x[-2], msrp_info))
        params['fields'] = game.keys() #keys of first dictionary or something like that
        params['vals'] = game
        params['vals']['related'] = [(game[0].replace("\\'", "'"), game[1]) for game in params['vals']['related']]
        params['developers'] = [company[0] for company in game['companies'] if company[1]]
        params['publishers'] = [company[0] for company in game['companies'] if company[2]]
        params['prices'] = prices
        params['msrp'] = list(map(lambda x: (x[-2], x[-3]), msrp_info))
        params['source_link'] = list(map(lambda x: (x[-2], x[-4]), msrp_info))
        params['base_url'] = f'http://db8.cse.nd.edu:{port}'
        params['graph'] = pp.get_price_history(game_id)
        if session.get("username"):
            params['liked'] = game.get("igdb_id") in session["likes"]
            params['disliked'] = game.get("igdb_id") in session["dislikes"]
            params['wishlist'] = game.get("igdb_id") in session["wishlist"]
        conn.close()
        return render_template("game_new.html", **params)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run("db8.cse.nd.edu", port)
