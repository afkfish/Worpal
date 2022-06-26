from youtube_dl import YoutubeDL

YDL_OPTIONS = {"format": "bestaudio", "noplaylist": True}


def search_yt(item):
    with YoutubeDL(YDL_OPTIONS) as ydl:
        try:
            if item.startswith("https://www.youtube.com/watch?v="):
                info = ydl.extract_info(item, download=False)
            else:
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
        except ValueError:
            return False

    return {'source': info['formats'][0]['url'], 'title': info['title'], 'thumbnail': info['thumbnail'],
            'duration': info['duration'], 'id': info['id']}