import base64
import os

import requests

from structures.playable import Playable, Playlist, Track


class SpotifyApi:
    _url = 'https://accounts.spotify.com/api/token'
    _api_url = 'https://api.spotify.com/v1/'
    _data = {}
    _client_id = os.getenv("SPOTIFY_ID")
    _client_secret = os.getenv("SPOTIFY_SECRET")
    _message = base64.b64encode(f"{_client_id}:{_client_secret}".encode())
    _headers = {'Authorization': f"Basic {_message.decode()}"}
    _data['grant_type'] = "client_credentials"

    def resolve(self, playable: Track | Playlist) -> Track | Playlist:
        r = requests.post(self._url, headers=self._headers, data=self._data)
        token = r.json()['access_token']

        headers = {
            "Authorization": "Bearer " + token
        }

        if type(playable) is Track:
            track_id = playable.id
            track_url = f"{self._api_url}tracks/{track_id}"

            res = requests.get(url=track_url, headers=headers)
            playable.artists = [artist['name'] for artist in res.json()['album']['artists']]
            playable.query = res.json()['name'] + " - " + ", ".join(playable.artists)

        elif type(playable) is Playlist:
            playlist_url = f"{self._api_url}playlists/{playable.id}"

            res = requests.get(url=playlist_url, headers=headers).json()
            playable.title = res['name']
            playable.image = res['images'][0]['url']

            playable.owner = res['owner']['display_name']
            playable.tracks = [Track(Playable(user=playable.user, spotify=True)).query_(query=track['track']['name'] + " - " + ", ".join([artist['name'] for artist in track['track']['artists']])) for track in res['tracks']['items']][:10]

        return playable

    # def get_by_name(self, q, type_, limit):
    #     r = requests.post(self.url, headers=self.headers, data=self.data)
    #     token = r.json()['access_token']
    #
    #     link = {
    #         "q": q,
    #         "type": type_,
    #         "limit": limit
    #     }
    #     headers = {
    #         "Authorization": "Bearer " + token
    #     }
    #
    #     res = requests.get(url="https://api.spotify.com/v1/search?" + urlencode(link), headers=headers)
    #     return res.json()
