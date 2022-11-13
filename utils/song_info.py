import youtube_dl.utils
from requests import get, post, exceptions
from youtube_dl import YoutubeDL

YDL_OPTIONS = {"format": "bestaudio", "noplaylist": True, "quiet": True}


def search_yt(item, multiple: bool = False):
	print('Downloading: ' + item)
	with YoutubeDL(YDL_OPTIONS) as ydl:
		try:
			try:
				get(item)

			except exceptions.RequestException or exceptions.MissingSchema:
				if multiple:
					return ydl.extract_info(f"ytsearch5:{item}", download=False)['entries']

				else:
					info = ydl.extract_info(f"ytsearch:{item}", download=False)['entries'][0]

			else:
				info = ydl.extract_info(item, download=False)

		except youtube_dl.utils.DownloadError:
			return False
	return {'source': info['formats'][0]['url'], 'title': info['title'], 'thumbnail': info['thumbnail'],
			'duration': info['duration']}


magic_url = "https://www.youtube.com/youtubei/v1/player"
key = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"


def fast_link(url):
	video_id = url.split("v=")[1]
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
		res = post(url, headers=headers, params={"key": key}, json=payload_data)
		json_data = res.json()
		if res.status_code != 200:
			return False
	except exceptions.RequestException:
		print("Error in video info")
		return False

	audio_only = [stream for stream in json_data['streamingData']['adaptiveFormats'] if
				  'opus' in stream['mimeType'] and 'AUDIO_QUALITY_MEDIUM' == stream['audioQuality']]

	try:
		ret = {'source': audio_only[0]['url'], 'title': json_data['videoDetails']['title'],
			   'thumbnail': json_data['videoDetails']['thumbnail']['thumbnails'][-1]['url'],
			   'duration': audio_only[0]['approxDurationMs']}
		return ret
	except KeyError:
		return False
