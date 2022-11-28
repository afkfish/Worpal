import base64
from urllib.parse import urlencode

import requests

from main import bot


class SpotifyApi():
	url = 'https://accounts.spotify.com/api/token'
	headers = {}
	data = {}
	client_id = bot.secrets["spotify"]["client_id"]
	client_secret = bot.secrets["spotify"]["client_secret"]
	message = base64.b64encode(f"{client_id}:{client_secret}".encode())
	headers['Authorization'] = f"Basic {message.decode()}"
	data['grant_type'] = "client_credentials"

	def get_by_id(self, trackid):
		r = requests.post(self.url, headers=self.headers, data=self.data)
		token = r.json()['access_token']

		trackurl = f"https://api.spotify.com/v1/tracks/{trackid}"
		headers = {
			"Authorization": "Bearer " + token
		}

		res = requests.get(url=trackurl, headers=headers)
		return res.json()

	def get_by_name(self, q, type_, limit):
		r = requests.post(self.url, headers=self.headers, data=self.data)
		token = r.json()['access_token']

		link = {
			"q": q,
			"type": type_,
			"limit": limit
		}
		headers = {
			"Authorization": "Bearer " + token
		}

		res = requests.get(url="https://api.spotify.com/v1/search?" + urlencode(link), headers=headers)
		return res.json()

	def get_playlist(self, playlist_id):
		r = requests.post(self.url, headers=self.headers, data=self.data)
		token = r.json()['access_token']

		playlist_url = f"https://api.spotify.com/v1/playlists/{playlist_id}"
		headers = {
			"Authorization": "Bearer " + token
		}
		res = requests.get(url=playlist_url, headers=headers)
		return res.json()
