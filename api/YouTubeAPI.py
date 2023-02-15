import datetime as dt
import logging
import os
import re
from urllib.parse import urlparse

import googleapiclient.discovery
import youtube_dl
from requests import post, exceptions
from youtube_dl import YoutubeDL

from structures.track import Track

YDL_OPTIONS = {"format": "bestaudio/best", "noplaylist": True, "quiet": True}
logger = logging.getLogger("YouTubeAPI")


def youtubedl_search(track: Track) -> Track:
    logger.info("YoutubeDL search: %s", track.query)
    with YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            result = urlparse(track.query)
            if all([result.scheme, result.netloc]):
                logger.info("YoutubeDL by link")
                info = ydl.extract_info(track.query, download=False)

            else:
                logger.info("YoutubeDL by search")
                info = ydl.extract_info(f"ytsearch:{track.query}", download=False)['entries'][0]

        except youtube_dl.utils.DownloadError:
            logger.error(f"YoutubeDL error")
            return track
    logger.info("YoutubeDL result: %s", info['title'])
    track.title = info['title']
    track.source = info['formats'][0]['url']
    track.thumbnail = info['thumbnail']
    track.duration = info['duration']
    return track


def youtube_search(track: Track) -> Track:
    api_service_name = "youtube"
    api_version = "v3"

    developer_key = os.getenv("YOUTUBE_API_KEY")

    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=developer_key)

    request = youtube.search().list(
        part="snippet",
        q=track.query
    )
    response = request.execute()

    # generate a list of video ids from response['items']
    # results = [item["id"]["videoId"] for item in response["items"]]
    track.id = response["items"][0]["id"]["videoId"]

    return track


magic_url = "https://www.youtube.com/youtubei/v1/player"
embed_key = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"


def youtube_api_search(track: Track) -> Track:
    if track.id is not None:
        video_id = track.id
    elif "youtu.be" in track.query:
        video_id = re.search(r"youtu.be/(.+?)", track.query).group(1)
    elif "watch?v=" in track.query:
        video_id = re.search(r"watch\?v=(.+?)", track.query).group(1)
    else:
        return track

    if "&" in video_id:
        video_id = video_id.split("&")[0]

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/88.0.4324.96 Safari/537.36',
        'content-type': 'application/json',
        'referer': f'https://www.youtube.com/embed/{video_id}'
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
            logger.error(f"YouTube API error: {res.status_code}")
            return track
    except exceptions.RequestException:
        logger.error(f"YouTube API error, trying with YoutubeDL")
        return youtubedl_search(track)

    try:
        audio_only = [stream for stream in json_data['streamingData']['adaptiveFormats'] if
                      'opus' in stream['mimeType'] and 'AUDIO_QUALITY_MEDIUM' == stream['audioQuality']]
        track.title = json_data['videoDetails']['title']
        track.source = audio_only[0]['url']
        track.thumbnail = json_data['videoDetails']['thumbnail']['thumbnails'][-1]['url']
        logger.info("Duration: " + audio_only[0]['approxDurationMs'])
        track.duration = dt.timedelta(milliseconds=int(audio_only[0]['approxDurationMs'])).seconds
        return track
    except KeyError:
        logger.error(f"Error in getting {video_id}")
        return youtubedl_search(track)


def get_link(track: Track) -> Track:
    result = urlparse(track.query)
    if all([result.scheme, result.netloc]):
        logger.info("YouTube link detected")
        return youtube_api_search(track)
    else:
        logger.info("YouTube search detected")
        music_id = youtube_search(track)
        return youtube_api_search(music_id)
