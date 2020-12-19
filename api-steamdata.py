import requests
import json
import pickle
import os
from dotenv import load_dotenv
import psycopg2


def collectUserData(count):
    ''' Used for collecting and seeding user data from Steam.'''

    seed_steamId = os.getenv('SEED_STEAM_ID')
    key = os.getenv('STEAM_KEY')
    
    #To be reassigned later
    user_memo = None
    que = None
    game_memo = None

    #Fetch pickled que, or create one if it doesn't exist 
    try:
        que = pickle.load(open('pickled_que.pql', 'rb'))
        # print('made it to the try except for opening/creating pickle')
    except (OSError, IOError):
        pickle.dump([seed_steamId], open('pickled_que.pql', 'wb'))
        que = [seed_steamId]
        # print('created pickle')


    #Grab the users and games stored in the database to ensure that there are no duplicate entries
    user_memo = grab_current_users_DB()
    game_memo = grab_current_games_DB()

    #Converted to sets for performance increase
    user_memo = set(user_memo)
    game_memo = set(game_memo)
    # print(game_memo)

    #While the iteratations are below the count arg, fetch the user's steam data, update the JSON, and adjust the que accordingly to ensure that nothing is lost if error
    iterations = 0
    no_games_reachable = 0


    while (iterations <= count and len(que) > 0):
        print('iterations', iterations)
        iterations += 1
        #items in pickled list are stored as steam Ids
        steamId = que.pop(0)
        print('current steam user', steamId)

        #Re-pickle que and overwrite
        pickle.dump(que, open('pickled_que.pql', 'wb'))

        #If the user doesn't exist already, add them to the database and memo
        if steamId not in user_memo:
            insert_user_data_DB(steamId)
            user_memo.add(steamId)
        else:
            #Otherwise, continue because this person has been explored already
            continue

        friends_list = grab_user_friends(steamId, key)

        #Some people don't have friends. In which case pass and add games
        if friends_list == {}:
            pass
        elif friends_list == None:
            #Will come back none if profile is inaccessible 
            no_games_reachable += 1
            continue
        else:
            #If user has friends, add ones not already explored in que
            que = que + [friend['steamid'] for friend in friends_list if (friend['steamid'] not in que and friend['steamid'] not in user_memo)]
            #Re-pickle que and overwrite
            pickle.dump(que, open('pickled_que.pql', 'wb'))


        #Make an API request to grab all the current user's steam info 
        games_list = grab_user_games(steamId, key)
        # print(games_list)
        # print(games_list)
        if games_list == {}:
            #Person has no games or is otherwise unreachable
            no_games_reachable += 1
            continue

        for game in games_list: 
            # print(game)

            #If the player hasn't played it, don't bother
            if game['playtime_forever'] == 0:
                continue

            #See if the game is currently in the library, add it if not
            if str(game['appid']) not in game_memo:
                insert_game_data_DB(game['appid'])
                game_memo.add(game['appid'])

            #Add the game information to the database
            insert_game_user_data_DB(steamId, game['appid'], game['playtime_forever'])



    print(f'Out of {count} searched, {no_games_reachable} failed to get games. {(count-no_games_reachable) / count * 100}% success')


                            



def grab_user_games(steamId, key):
    try:
        response = requests.get(f'https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={key}&format=json&steamid={steamId}&include_played_free_games=true')
        # print('made request')
    except Exception as e:
        print('Games request failed', e)

    if response.status_code == 200:
        response_json = response.json()
        # print('request came back okay')

        if response_json['response'] == {}:
            return response_json['response']

        # print(response_json)
        #grab list of games from json object
        games_list = response_json['response']['games']
        # print(games_list)
        return games_list
    else:
        raise Exception('Games request was not a 200', response.status_code)


def grab_user_friends(steamId, key):

    response = None

    try:
        #Fetch and add friends
        response = requests.get(f'http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key={key}&steamid={steamId}&relationship=friend')
        # print('made friend request')
    except Exception as e:
        print('There was an error in grabbing the users friends', e)
        raise Exception('Error on friends request')

    if response.status_code == 200:
        response_json = response.json()

        if response_json == {}:
            # print('friends came back empty, ')
            return response_json
            

        #Grab list/array of friends from object
        friends_list = response_json['friendslist']['friends']

        #Add to end of que all unique friends
        return friends_list
    else:
        #If error on call, return none and the main function will continue the loop
        return None


def insert_user_data_DB(user_steam_id):

    try:

        DB_NAME = os.getenv('DB_STEAMDATA')
        DB_USER = os.getenv('DB_USERNAME')
        DB_PASSWORD = os.getenv('DB_PASSWORD')

        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)

        cur = conn.cursor()

        cur.execute(
            '''
            INSERT INTO users (user_steam_id)
            VALUES (%s)
            ''', [user_steam_id]
        )

        conn.commit()
        cur.close()
        conn.close()

    except Exception as e:
        raise e


def insert_game_data_DB(game_steam_id):

    try:

        DB_NAME = os.getenv('DB_STEAMDATA')
        DB_USER = os.getenv('DB_USERNAME')
        DB_PASSWORD = os.getenv('DB_PASSWORD')

        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)

        cur = conn.cursor()

        cur.execute(
            '''
            INSERT INTO games (game_steam_id)
            VALUES (%s)
            ''', [game_steam_id]
        )

        conn.commit()
        cur.close()
        conn.close()

    except:
        return


def insert_game_user_data_DB(user_steam_id, game_steam_id, playtime):
    try:
        DB_NAME = os.getenv('DB_STEAMDATA')
        DB_USER = os.getenv('DB_USERNAME')
        DB_PASSWORD = os.getenv('DB_PASSWORD')

        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)

        cur = conn.cursor()

        cur.execute(
            '''
            INSERT INTO user_games_data (user_id, game_id, playtime)
            VALUES (%s, %s, %s)
            ''', [user_steam_id, game_steam_id, playtime]
            )

        conn.commit()
        cur.close()
        conn.close()
        

    except Exception as e:
        raise e

    #INSERT INTO users (user_steam_id)
    #Insert into games (game_steam_id)
    #INSERT INTO user_games_data (user_id, game_id, playtime)


def grab_current_users_DB():

    try:

        DB_NAME = os.getenv('DB_STEAMDATA')
        DB_USER = os.getenv('DB_USERNAME')
        DB_PASSWORD = os.getenv('DB_PASSWORD')

        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)

        cur = conn.cursor()

        cur.execute(
            '''
            SELECT * FROM users
            '''
        )

        users_table = cur.fetchall()

        result = []
        for user in users_table:
            result.append(user[1])

        conn.commit()
        cur.close()
        conn.close()

        return result

    except Exception as e:
        raise e


def grab_current_games_DB():

    try:

        DB_NAME = os.getenv('DB_STEAMDATA')
        DB_USER = os.getenv('DB_USERNAME')
        DB_PASSWORD = os.getenv('DB_PASSWORD')

        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD)

        cur = conn.cursor()

        cur.execute(
            '''
            SELECT * FROM games
            '''
        )

        games_table = cur.fetchall()

        result = []
        for user in games_table:
            result.append(user[1])

        conn.commit()
        cur.close()
        conn.close()

        return result

    except Exception as e:
        raise e


    


collectUserData(10000)