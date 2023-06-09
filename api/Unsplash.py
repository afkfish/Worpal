import os

import requests

auth_header = {
    'Authorization': f'Client-ID {os.getenv("UNSPLASH_TOKEN")}'
}


def search(query: str) -> [str]:
    query = query.replace(" ", "+")
    url = f"https://api.unsplash.com/search/photos?query={query}"
    response = requests.get(url, headers=auth_header).json()
    try:
        filtered = [x['urls']['full'] for x in response['results']]
        return filtered[:10]
    except KeyError | IndexError:
        return ["https://unsplash.com/"]
