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
    except (OSError, IOError):
        pickle.dump([seed_steamId], open('pickled_que.pql', 'wb'))
        que = [seed_steamId]


    #Open the userData_raw json file, which contains all of the current user data
    with open('userData_Raw.json') as user_data_json:
        user_data = json.load(user_data_json)

    #While the iteratations are below the count arg, fetch the user's steam data, update the JSON, and adjust the que accordingly to ensure that nothing is lost if error

    iterations = 0
    key = 'E7A8E033472E33429602FDC1FEAC4C71'

    while (iterations <= count):
        iterations += 1
        #items in pickled list are stored as steam Ids
        steamId = que.pop(0)

        try:
            #Fetch and add friends
            response = requests.get(f'http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key={key}&steamid={steamId}&relationship=friend')
            if response.status_code == 200:
                response_json = response.json()

                if response_json == {}:
                    pickle.dump(que, open('pickled_que.pql', 'wb'))
                    continue

                #Grab list/array of friends from object
                friends_list = response_json['friendslist']['friends']

                #Add to end of que all unique friends
                que = que + [friend.steamdid for friend in friends_list if (friend.steamid not in que or friend.steamid not in user_data.keys())]

                #Re-pickle que and overwrite
                pickle.dump(que, open('pickled_que.pql', 'wb'))


                #Make an API request to grab all the current user's steam info 
                try:
                    response = requests.get(f'https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={key}&format=json&steamid={steamId}&include_played_free_games=true')

                    if requests.status_code == 200:
                        response_json = response.json()

                        #grab list of games from json object
                        games_list = response_json['response']['games']

                        for game in games_list: 

                            if game['playtime_forever'] == 0:
                                continue
                            
                            #Add the relevant information to the user data  object
                            user_data[steamId][game['appid']] = game['playtime_forever']

                            with open('userData_Raw.json', 'w') as user_data_json:
                                json.dump(user_data, user_data_json)


                            




                except:
                    pass


        except:
            pass






# collectUserData(10)