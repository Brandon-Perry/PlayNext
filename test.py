import requests
import json
import pickle


key = 'E7A8E033472E33429602FDC1FEAC4C71'

steamId = 76561198100198908

response = requests.get(f'http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key={key}&steamid={steamId}&relationship=friend')


x = response.json()

print(x['friendslist']['friends'])

