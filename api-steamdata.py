import requests
import json
import pickle


key = 'E7A8E033472E33429602FDC1FEAC4C71'

# steamId = 76561198083486927
# steamId = 76561198100198908
# steam_id = 76561198003962089

# response = requests.get(f'https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={key}&format=json&steamid={steamId}&include_played_free_games=true')

# response = requests.get(f'http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key={key}&steamid={steamId}&relationship=friend')

# friendJson = response.json()

# print(friendJson['friendslist'])


def collectUserData(count):
    ''' Used for collecting and seeding user data from Steam. Uses friendsToGather for storing future friends to grab'''

    seed_steamId = 76561198100198908
    
    #To be reassigned later
    user_data = None
    que = None

    #Fetch pickled que, or create one if it doesn't exist 
    try:
        que = pickle.load(open('pickled_que.pql', 'rb'))
        # print('made it to the try except for opening/creating pickle')
    except (OSError, IOError):
        pickle.dump([seed_steamId], open('pickled_que.pql', 'wb'))
        que = [seed_steamId]
        # print('created pickle')


    #Open the userData_raw json file, which contains all of the current user data
    user_data = open_json('userData_Raw.json')

    #While the iteratations are below the count arg, fetch the user's steam data, update the JSON, and adjust the que accordingly to ensure that nothing is lost if error

    iterations = 0
    key = 'E7A8E033472E33429602FDC1FEAC4C71'

    no_games_reachable = 0

    while (iterations <= count and len(que) > 0):
        iterations += 1
        print('iterations', iterations)
        #items in pickled list are stored as steam Ids
        steamId = que.pop(0)
        print('current steam user', steamId)


        friends_list = grab_user_friends(steamId, key)

        if friends_list == {}:
            pass
        elif friends_list == None:
            continue
        else:
            que = que + [friend['steamid'] for friend in friends_list if (friend['steamid'] not in que and friend['steamid'] not in user_data.keys())]
            #Re-pickle que and overwrite
            pickle.dump(que, open('pickled_que.pql', 'wb'))

        #Create entry for user in the json 
        user_data[steamId] = []

        #Make an API request to grab all the current user's steam info 
        games_list = grab_user_games(steamId, key)

        if games_list == {}:
            no_games_reachable += 1
            continue

        for game in games_list: 
            # print('about to print game')
            # print(game)
            if game['playtime_forever'] == 0:
                # print('continued')
                continue
            
            #Add the relevant information to the user data  object
            
            #Put game time as a value to the game id 
            game_dict = {game['appid']: game['playtime_forever']}

            #Add the dictionary to the user_data dictionary with the user steam id as the key
            user_data[steamId].append(game_dict)            
            # print('added game')
        

        #Update the json file to reflect the current state of user_data
        with open('userData_Raw.json', 'w') as user_data_json:
            json.dump(user_data, user_data_json)
            # print('updated json')

    print(f'Out of {count} searched, {no_games_reachable} failed to get games. {no_games_reachable / count}% success')


                            




               


def open_json(jsonFileString):
    with open(jsonFileString) as user_data_json:
        data = json.load(user_data_json)
        # print('opened json')
        return data


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



        

collectUserData(10)