import datetime as dt
import logging
from urllib.parse import urlparse

import googleapiclient.discovery
import youtube_dl
from requests import post, exceptions
from youtube_dl import YoutubeDL

from main import bot

YDL_OPTIONS = {"format": "bestaudio", "noplaylist": True, "quiet": True}
LOGGER = logging.getLogger("YouTube search")


def search_yt(item):
	LOGGER.info(f"YoutubeDL search: {item}")
	with YoutubeDL(YDL_OPTIONS) as ydl:
		try:
			result = urlparse(item)
			if all([result.scheme, result.netloc]):
				LOGGER.info(f"YoutubeDL by link")
				info = ydl.extract_info(item, download=False)

			else:
				LOGGER.info(f"YoutubeDL by search")
				info = ydl.extract_info(f"ytsearch:{item}", download=False)['entries'][0]

		except youtube_dl.utils.DownloadError:
			LOGGER.error(f"YoutubeDL error")
			return False
	LOGGER.info(f"YoutubeDL result: {info['title']}")
	return {'source': info['formats'][0]['url'], 'title': info['title'], 'thumbnail': info['thumbnail'], 'duration': dt.timedelta(milliseconds=int(info['duration'])).seconds}


def search_api(querry: str):
	api_service_name = "youtube"
	api_version = "v3"

	developer_key = bot.secrets["youtube"]["api_key"]

	youtube = googleapiclient.discovery.build(
		api_service_name, api_version, developerKey=developer_key)

	request = youtube.search().list(
		part="snippet",
		q=querry
	)
	response = request.execute()

	# generate a list of video ids from response['items']
	# results = [item["id"]["videoId"] for item in response["items"]]
	result = response["items"][0]["id"]["videoId"]

	return result


magic_url = "https://www.youtube.com/youtubei/v1/player"
embed_key = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"


def get_info(video_id: str):
	headers = {
		'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
					  'Chrome/88.0.4324.96 Safari/537.36',
		'content-type': 'application/json',
		'referer': 'https://www.youtube.com/embed/' + video_id
	}

	payload_data = {
		"videoId": video_id,
		"context": {
			"client": {
				"visitorData": "CgtRQ1VwRWtZTm9YayiG3OCABg%3D%3D",
				"clientName": "WEB_EMBEDDED_PLAYER",
				"clientVersion": "20210126",
			},
		},
		"cpn": "79JIqSkI_5iSwavl"
	}

	try:
		res = post(magic_url, headers=headers, params={"key": embed_key}, json=payload_data)
		json_data = res.json()
		if res.status_code != 200:
			LOGGER.error(f"YouTube API error: {res.status_code}")
			return False
	except exceptions.RequestException:
		LOGGER.error(f"YouTube API error, trying with YoutubeDL")
		return search_yt("https://youtu.be/watch?v=" + video_id)

	try:
		audio_only = [stream for stream in json_data['streamingData']['adaptiveFormats'] if
					  'opus' in stream['mimeType'] and 'AUDIO_QUALITY_MEDIUM' == stream['audioQuality']]
		ret = {'source': audio_only[0]['url'], 'title': json_data['videoDetails']['title'],
			   'thumbnail': json_data['videoDetails']['thumbnail']['thumbnails'][-1]['url'],
			   'duration': dt.timedelta(milliseconds=int(audio_only[0]['approxDurationMs'])).seconds}
		return ret
	except KeyError:
		LOGGER.error(f"{json_data['videoDetails']['title']} is MDR locked")
		return search_yt("https://youtu.be/watch?v=" + video_id)


def fast_link(item):
	result = urlparse(item)
	if all([result.scheme, result.netloc]):
		LOGGER.info(f"YouTube link detected")
		return get_info(item.split("v=")[-1])
	else:
		LOGGER.info(f"YouTube search detected")
		music_id = search_api(item)
		return get_info(music_id)
