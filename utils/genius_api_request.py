import json
from urllib.parse import urlencode

import requests

from main import bot


class GeniusApi:
	headers = {}
	token = bot.secrets["genius"]["access_token"]
	headers["Authorization"] = "Bearer " + token

	def get_song(self, q):
		attr = {
			"q": q
		}
		url = "https://api.genius.com/search?" + urlencode(attr)

		res = requests.get(url=url, headers=self.headers)
		try:
			data = {
				"title": res.json()["response"]["hits"][0]["result"]["title"],
				"url": res.json()["response"]["hits"][0]["result"]["url"]
			}
		except IndexError:
			raise IndexError("Couldn't find the song.")

		return data
