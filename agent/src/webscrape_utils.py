import requests 
from bs4 import BeautifulSoups

r = requests.get('https://api.github.com/events')
print(r.text)
