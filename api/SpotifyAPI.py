import base64
import os

import requests

from structures.playable import Playable, Playlist, Track


class SpotifyApi:
    _url = 'https://accounts.spotify.com/api/token'
    _api_url = 'https://api.spotify.com/v1/'
    _client_id = os.getenv("SPOTIFY_ID")
    _client_secret = os.getenv("SPOTIFY_SECRET")
    _message = base64.b64encode(f"{_client_id}:{_client_secret}".encode())
    _headers = {'Authorization': f"Basic {_message.decode()}"}
    _data = {'grant_type': "client_credentials"}

    def resolve(self, playable: Track | Playlist) -> Track | Playlist:
        token = requests.post(self._url, headers=self._headers, data=self._data).json()['access_token']
        headers = {"Authorization": "Bearer " + token}

        try:
            if isinstance(playable, Track):
                res = requests.get(url=f"{self._api_url}tracks/{playable.id}", headers=headers)
                playable.artists = [artist['name'] for artist in res.json()['album']['artists']]
                playable.query = res.json()['name'] + " - " + ", ".join(playable.artists)

            elif isinstance(playable, Playlist):
                res = requests.get(url=f"{self._api_url}playlists/{playable.id}", headers=headers).json()
                playable.title = res['name']
                playable.image = res['images'][0]['url']
                playable.owner = res['owner']['display_name']
                playable.tracks = [Track(Playable(user=playable.user, spotify=True)).query_(query=track['track']['name'] + " - " + ", ".join([artist['name'] for artist in track['track']['artists']])) for track in res['tracks']['items']][:10]
        except AttributeError:
            playable.valid = False

        return playable
