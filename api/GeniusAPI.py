import logging
import os
from urllib.parse import urlencode

import requests
from bs4 import BeautifulSoup

token = os.getenv("GENIUS_TOKEN")
headers = {
	"Authorization": f"Bearer {token}"
}
LOGGER = logging.getLogger("Genius lyrics")


def search_song(query):
	attr = {
		"q": query
	}
	url = "https://api.genius.com/search?" + urlencode(attr)

	res = requests.get(url=url, headers=headers).json()
	try:
		data = {
			"title": res["response"]["hits"][0]["result"]["title"],
			"url": res["response"]["hits"][0]["result"]["url"]
		}
	except IndexError or KeyError:
		LOGGER.error("Couldn't find the song.")
		return

	return data


def get_lyrics(data):
	url = data["url"]
	final = ""

	soup = BeautifulSoup(requests.get(url).content, 'lxml')

	for line in soup.find_all('div', {'data-lyrics-container': 'true'}):
		t = line.get_text(strip=True, separator='\n')
		if t:
			final += t

	return final
