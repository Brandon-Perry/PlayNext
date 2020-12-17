import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv('DB_STEAMDATA')
DB_USER = os.getenv('DB_USERNAME')
DB_PASSWORD = os.getenv('DB_PASSWORD')

# print(DB_NAME, DB_USER, DB_PASSWORD)

#connect to database
try:
    conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)

    #Create cursor to perform operations
    cur = conn.cursor()

    #create users table
    cur.execute('CREATE TABLE users (id serial PRIMARY KEY, user_steam_id varchar UNIQUE)')

    #create games table
    cur.execute('CREATE TABLE games (id serial PRIMARY KEY, game_steam_id varchar UNIQUE)')

    #Create join table with time spent playing (minutes)
    cur.execute('CREATE TABLE user_games_data (id serial PRIMARY KEY, user_id varchar REFERENCES users (user_steam_id), game_id varchar REFERENCES games (game_steam_id), playtime int)')

    #Save and close session
    conn.commit()
    cur.close()
    conn.close()
except Exception as e:
    print(e)