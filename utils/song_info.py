from requests import get, exceptions
from youtube_dl import YoutubeDL

YDL_OPTIONS = {"format": "bestaudio", "noplaylist": True}


def search_yt(item, multiple: bool = False):
    with YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            get(item)

        except exceptions.RequestException:
            if multiple:
                return ydl.extract_info(f"ytsearch5:{item}", download=False)['entries']

            else:
                info = ydl.extract_info(f"ytsearch:{item}", download=False)['entries'][0]

        else:
            info = ydl.extract_info(item, download=False)

    return {'source': info['formats'][0]['url'], 'title': info['title'], 'thumbnail': info['thumbnail'],
            'duration': info['duration']}
