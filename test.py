import requests

url = "https://api.brawlstars.top/api/player/JJJJ"
response = requests.get(url)
print(response.text)